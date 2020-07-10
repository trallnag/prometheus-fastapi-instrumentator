from typing import Tuple
from timeit import default_timer
import os
import re

from prometheus_client import Histogram
from prometheus_client import CollectorRegistry, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY
from prometheus_client.multiprocess import MultiProcessCollector
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match


class PrometheusFastApiExporter:
    def __init__(
        self,
        app: FastAPI,
        metrics_endpoint: str = "/metrics",
        should_group_status_codes: bool = True,
        should_ignore_untemplated: bool = False,
        should_group_untemplated: bool = True,
        should_ignore_method: bool = True,
        excluded_handlers: list = ["/metrics"],
        buckets: tuple = Histogram.DEFAULT_BUCKETS,
        metric_name: str = "http_request_duration_seconds",
        label_names: tuple = ("method", "handler", "status",),
    ):
        """

        :param app: FastAPI app to be instrumented.

        :param metrics_endpoint: path to serve metrics at, defaults to "/metrics".

        :param should_group_status_codes: Should status codes be grouped into 
        2xx, 3xx and so on? Defaults to True.

        :param should_ignore_untemplated: Should requests without a matching 
        template be ignored? Defaults to False.

        :param should_group_untemplated: Should requests without a matching 
        template be grouped to handler None? Defaults to True.

        :param should_ignore_method: Should methods (GET, POST, etc.) be ignored? 
        If true, the label value will always be "ignored". Defaults to True.

        :param excluded_handlers: Handlers that should be ignored. List of 
        strings is turned into regex patterns. Defaults to ["/metrics"].

        :param buckets: Buckets for the histogram. Defaults to Prometheus default.

        :param metric_name: Name of the latency metric. Defaults to 
        "http_request_duration_seconds".

        :param label_names: Names of the three labels used for the metric. Does 
        not influence the label values. Defaults to ("method", "handler", "status",).
        """

        self.app = app
        self.metrics_endpoint = metrics_endpoint
        self.should_group_status_codes = should_group_status_codes
        self.should_ignore_untemplated = should_ignore_untemplated
        self.should_group_untemplated = should_group_untemplated
        self.should_ignore_method = should_ignore_method

        if excluded_handlers:
            self.excluded_handlers = [re.compile(path) for path in excluded_handlers]
        else:
            self.excluded_handlers = []

        if buckets[-1] == float("inf"):
            self.buckets = buckets
        else:
            self.buckets = buckets + float("inf")

        self.histogram = Histogram(
            name=metric_name,
            documentation="Duration of HTTP requests in seconds",
            labelnames=label_names,
            buckets=buckets,
        )

    def instrument(self) -> None:
        """Performs the instrumentation by adding middleware and endpoint."""

        self._add_metrics_endpoint()

        @self.app.middleware("http")
        async def dispatch_middleware(request: Request, call_next) -> Response:
            start_time = default_timer()

            if self.should_ignore_method:
                method = "ignored"
            else:
                method = request.method

            handler, is_templated = self._get_handler(request)

            try:
                response = None
                response = await call_next(request)
            except Exception as e:
                if response is None:
                    status = 500
                raise e from None
            else:
                status = response.status_code

            if self._is_handler_excluded(handler, is_templated):
                return response

            if is_templated is False and self.should_group_untemplated:
                handler = "none"

            duration = max(default_timer() - start_time, 0)

            self.histogram.labels(
                *self._create_label_tuple(method, handler, status)
            ).observe(duration)

            return response

    def _create_label_tuple(
        self, method: str, handler: str, code: int
    ) -> Tuple[str, str, str]:
        """Processes label values based on config.

        :param method: Method used for the request, for example `GET`.

        :param handler: Identifier for entity that handled / should handle the 
        request.

        :param code: Status code of the response. If error / exception occured 
        this should be `500`.

        :return: Processed values.
        """

        code = str(code)

        if self.should_group_status_codes:
            code = code[0] + "xx"
        return (
            method,
            handler,
            code,
        )

    def _get_handler(self, request: Request) -> Tuple[str, bool]:
        """Extracts either template or (if no template) path."""

        for route in request.app.routes:
            match, child_scope = route.matches(request.scope)
            if match == Match.FULL:
                return route.path, True

        return request.url.path, False

    def _is_handler_excluded(self, handler: str, is_templated: bool) -> bool:
        """Determines if the handler should be ignored."""

        if is_templated is False and self.should_ignore_untemplated:
            return True

        if any(pattern.search(handler) for pattern in self.excluded_handlers):
            return True

        return False

    def _add_metrics_endpoint(self) -> None:
        """Adds Prometheus metrics endpoint.

        Is done simply by adding another route, not with a distinct app that is 
        mounted to the given FastAPI app like this:

        ``` python
        prometheus_app = make_asgi_app()
        app.mount("/metrics", prometheus_app)
        ```

        It is simpler, but the disadvantage is that the `/metrics` endpoint or 
        more concrete the subapp will not be visible in the Swagger UI.
        """

        @self.app.get(self.metrics_endpoint)
        def metrics(request: Request) -> Response:
            if "prometheus_multiproc_dir" in os.environ:
                registry = CollectorRegistry()
                MultiProcessCollector(registry)
            else:
                registry = REGISTRY

            return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
