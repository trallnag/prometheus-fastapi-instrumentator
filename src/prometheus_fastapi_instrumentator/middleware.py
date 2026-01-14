from __future__ import annotations

import asyncio
import re
from http import HTTPStatus
from timeit import default_timer
from typing import Awaitable, Callable, Optional, Sequence, Tuple, Union

from prometheus_client import REGISTRY, CollectorRegistry, Gauge
from starlette.applications import Starlette
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Message, Receive, Scope, Send

from prometheus_fastapi_instrumentator import metrics, routing


class PrometheusInstrumentatorMiddleware:
    def __init__(
        self,
        app: Starlette,
        *,
        should_group_status_codes: bool = True,
        should_ignore_untemplated: bool = False,
        should_group_untemplated: bool = True,
        should_round_latency_decimals: bool = False,
        should_respect_env_var: bool = False,
        should_instrument_requests_inprogress: bool = False,
        should_exclude_streaming_duration: bool = False,
        excluded_handlers: Sequence[str] = (),
        body_handlers: Sequence[str] = (),
        round_latency_decimals: int = 4,
        env_var_name: str = "ENABLE_METRICS",
        inprogress_name: str = "http_requests_inprogress",
        inprogress_labels: bool = False,
        instrumentations: Sequence[Callable[[metrics.Info], None]] = (),
        async_instrumentations: Sequence[Callable[[metrics.Info], Awaitable[None]]] = (),
        metric_namespace: str = "",
        metric_subsystem: str = "",
        should_only_respect_2xx_for_highr: bool = False,
        latency_highr_buckets: Sequence[Union[float, str]] = (
            0.01,
            0.025,
            0.05,
            0.075,
            0.1,
            0.25,
            0.5,
            0.75,
            1,
            1.5,
            2,
            2.5,
            3,
            3.5,
            4,
            4.5,
            5,
            7.5,
            10,
            30,
            60,
        ),
        latency_lowr_buckets: Sequence[Union[float, str]] = (0.1, 0.5, 1),
        registry: CollectorRegistry = REGISTRY,
        custom_labels: dict = {},
    ) -> None:
        self.app = app

        self.should_group_status_codes = should_group_status_codes
        self.should_ignore_untemplated = should_ignore_untemplated
        self.should_group_untemplated = should_group_untemplated
        self.should_round_latency_decimals = should_round_latency_decimals
        self.should_respect_env_var = should_respect_env_var
        self.should_instrument_requests_inprogress = should_instrument_requests_inprogress

        self.round_latency_decimals = round_latency_decimals
        self.env_var_name = env_var_name
        self.inprogress_name = inprogress_name
        self.inprogress_labels = inprogress_labels
        self.registry = registry
        self.custom_labels = custom_labels

        self.excluded_handlers = [re.compile(path) for path in excluded_handlers]
        self.body_handlers = [re.compile(path) for path in body_handlers]

        if instrumentations:
            self.instrumentations = instrumentations
        else:
            default_instrumentation = metrics.default(
                metric_namespace=metric_namespace,
                metric_subsystem=metric_subsystem,
                should_only_respect_2xx_for_highr=should_only_respect_2xx_for_highr,
                should_exclude_streaming_duration=should_exclude_streaming_duration,
                latency_highr_buckets=latency_highr_buckets,
                latency_lowr_buckets=latency_lowr_buckets,
                registry=self.registry,
                custom_labels=custom_labels,
            )
            if default_instrumentation:
                self.instrumentations = [default_instrumentation]
            else:
                self.instrumentations = []

        self.async_instrumentations = async_instrumentations

        self.inprogress: Optional[Gauge] = None
        if self.should_instrument_requests_inprogress:
            labels = (
                (
                    "method",
                    "handler",
                )
                if self.inprogress_labels
                else ()
            )
            self.inprogress = Gauge(
                name=self.inprogress_name,
                documentation="Number of HTTP requests in progress.",
                labelnames=labels,
                multiprocess_mode="livesum",
            )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope)
        start_time = default_timer()

        handler, is_excluded = self._process_handler(request)

        if not is_excluded:
            self._inprogress_inc(request, handler)

        status_code = 500
        headers = []
        body = b""
        response_start_time = None
        response_end_time = None

        # Message body collected for handlers matching body_handlers patterns.
        should_collect_body = any(
            pattern.search(handler) for pattern in self.body_handlers
        )

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                nonlocal status_code, headers, response_start_time
                headers = message["headers"]
                status_code = message["status"]
                response_start_time = default_timer()

            elif message["type"] == "http.response.body":
                if should_collect_body and message.get("body"):
                    nonlocal body
                    body += message["body"]

                if not message.get("more_body", False):
                    nonlocal response_end_time
                    response_end_time = default_timer()

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            raise exc
        finally:
            if not is_excluded:
                await self._record_metrics(
                    request,
                    handler,
                    status_code,
                    headers,
                    body,
                    response_start_time,
                    response_end_time,
                    start_time,
                )

    def _process_handler(self, request: Request) -> Tuple[str, bool]:
        handler, is_templated = self._get_handler(request)
        is_excluded = self._is_handler_excluded(handler, is_templated)
        handler = (
            "none" if not is_templated and self.should_group_untemplated else handler
        )
        return handler, is_excluded

    def _get_inprogress(self, request: Request, handler: str) -> Gauge | None:
        if self.inprogress is None:
            return None
        if self.inprogress_labels:
            return self.inprogress.labels(request.method, handler)
        return self.inprogress

    def _inprogress_inc(self, request: Request, handler: str) -> None:
        inprogress = self._get_inprogress(request, handler)
        if inprogress is None:
            return
        inprogress.inc()

    def _inprogress_dec(self, request: Request, handler: str) -> None:
        inprogress = self._get_inprogress(request, handler)
        if inprogress is None:
            return
        inprogress.dec()

    def _calculate_durations(
        self,
        start_time: float,
        response_start_time: Optional[float],
        response_end_time: Optional[float],
    ) -> Tuple[float, float]:
        duration = max(default_timer() - start_time, 0.0)
        duration_without_streaming = 0.0

        if response_start_time:
            duration_without_streaming = max(response_start_time - start_time, 0.0)

        if response_end_time:
            duration = max(response_end_time - start_time, 0.0)

        if self.should_round_latency_decimals:
            duration = round(duration, self.round_latency_decimals)
            duration_without_streaming = round(
                duration_without_streaming, self.round_latency_decimals
            )

        return duration, duration_without_streaming

    async def _record_metrics(
        self,
        request: Request,
        handler: str,
        status_code: Union[int, HTTPStatus],
        headers: list,
        body: bytes,
        response_start_time: Optional[float],
        response_end_time: Optional[float],
        start_time: float,
    ) -> None:
        self._inprogress_dec(request, handler)

        status = (
            str(status_code.value)
            if isinstance(status_code, HTTPStatus)
            else str(status_code)
        )

        duration, duration_without_streaming = self._calculate_durations(
            start_time, response_start_time, response_end_time
        )

        if self.should_group_status_codes:
            status = status[0] + "xx"

        response = Response(
            content=body, headers=Headers(raw=headers), status_code=status_code
        )

        info = metrics.Info(
            request=request,
            response=response,
            method=request.method,
            modified_handler=handler,
            modified_status=status,
            modified_duration=duration,
            modified_duration_without_streaming=duration_without_streaming,
        )

        for instrumentation in self.instrumentations:
            instrumentation(info)

        await asyncio.gather(
            *[instrumentation(info) for instrumentation in self.async_instrumentations]
        )

    def _get_handler(self, request: Request) -> Tuple[str, bool]:
        """Extracts either template or (if no template) path.

        Args:
            request (Request): Python Requests request object.

        Returns:
            Tuple[str, bool]: Tuple with two elements. First element is either
                template or if no template the path. Second element tells you
                if the path is templated or not.
        """
        route_name = routing.get_route_name(request)
        return route_name or request.url.path, True if route_name else False

    def _is_handler_excluded(self, handler: str, is_templated: bool) -> bool:
        """Determines if the handler should be ignored.

        Args:
            handler (str): Handler that handles the request.
            is_templated (bool): Shows if the request is templated.

        Returns:
            bool: `True` if excluded, `False` if not.
        """

        if not is_templated and self.should_ignore_untemplated:
            return True

        if any(pattern.search(handler) for pattern in self.excluded_handlers):
            return True

        return False
