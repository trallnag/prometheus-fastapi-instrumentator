from __future__ import annotations

import re
from timeit import default_timer
from typing import TYPE_CHECKING, Callable, Optional, Sequence, Tuple

from prometheus_client import Gauge
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match

from prometheus_fastapi_instrumentator import metrics

if TYPE_CHECKING:
    from asgiref.typing import ASGISendEvent


class PrometheusInstrumentatorMiddleware:
    def __init__(
        self,
        app,
        *,
        should_group_status_codes: bool = True,
        should_ignore_untemplated: bool = False,
        should_group_untemplated: bool = True,
        should_round_latency_decimals: bool = False,
        should_respect_env_var: bool = False,
        should_instrument_requests_inprogress: bool = False,
        excluded_handlers: Sequence[str] = (),
        round_latency_decimals: int = 4,
        env_var_name: str = "ENABLE_METRICS",
        inprogress_name: str = "http_requests_inprogress",
        inprogress_labels: bool = False,
        instrumentations: Sequence[Callable[[metrics.Info], None]] = (),
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

        self.excluded_handlers = [re.compile(path) for path in excluded_handlers]
        self.instrumentations = instrumentations or [metrics.default()]

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

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope)
        start_time = default_timer()

        handler, is_templated = self._get_handler(request)
        is_excluded = self._is_handler_excluded(handler, is_templated)
        handler = (
            "none" if not is_templated and self.should_group_untemplated else handler
        )
        if not is_excluded and self.inprogress:
            if self.inprogress_labels:
                inprogress = self.inprogress.labels(request.method, handler)
            else:
                inprogress = self.inprogress
            inprogress.inc()

        status_code = 500
        headers = []  # type: ignore

        async def send_wrapper(event: ASGISendEvent) -> None:
            if event["type"] == "http.response.start":
                nonlocal status_code, headers
                headers = event["headers"]  # type: ignore
                status_code = event["status"]
            await send(event)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            raise exc
        finally:
            status = str(status_code)

            if not is_excluded:
                duration = max(default_timer() - start_time, 0)

                if self.should_instrument_requests_inprogress:
                    inprogress.dec()  # type: ignore

                if self.should_round_latency_decimals:
                    duration = round(duration, self.round_latency_decimals)

                if self.should_group_status_codes:
                    status = status[0] + "xx"

                response = Response(headers=Headers(raw=headers), status_code=status_code)  # type: ignore

                info = metrics.Info(
                    request=request,
                    response=response,
                    method=request.method,
                    modified_handler=handler,
                    modified_status=status,
                    modified_duration=duration,
                )

                for instrumentation in self.instrumentations:
                    instrumentation(info)

    def _get_handler(self, request: Request) -> Tuple[str, bool]:
        """Extracts either template or (if no template) path.

        Args:
            request (Request): Python Requests request object.

        Returns:
            Tuple[str, bool]: Tuple with two elements. First element is either
                template or if no template the path. Second element tells you
                if the path is templated or not.
        """

        for route in request.app.routes:
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                return route.path, True

        return request.url.path, False

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
