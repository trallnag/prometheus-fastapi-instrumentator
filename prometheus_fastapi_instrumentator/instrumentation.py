import os
import re
from timeit import default_timer
from typing import Tuple

from fastapi import FastAPI
from prometheus_client import Histogram
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match


class PrometheusFastApiInstrumentator:
    def __init__(
        self,
        should_group_status_codes: bool = True,
        should_ignore_untemplated: bool = False,
        should_group_untemplated: bool = True,
        should_round_latency_decimals: bool = False,
        should_respect_env_var_existence: bool = False,
        excluded_handlers: list = ["/metrics"],
        buckets: tuple = Histogram.DEFAULT_BUCKETS,
        metric_name: str = "http_request_duration_seconds",
        label_names: tuple = ("method", "handler", "status",),
        round_latency_decimals: int = 4,
        env_var_name: str = "PROMETHEUS",
    ):
        """
        :param should_group_status_codes: Should status codes be grouped into 
            `2xx`, `3xx` and so on?

        :param should_ignore_untemplated: Should requests without a matching 
            template be ignored?

        :param should_group_untemplated: Should requests without a matching 
            template be grouped to handler `none`?

        :param should_round_latency_decimals: Should recorded latencies be 
            rounded to a certain number of decimals?

        :param should_respect_env_var_existence: Should the instrumentator only 
            work - for example the methods `instrument()` and `expose()` - if 
            a certain environment variable is set? Usecase: A base FastAPI app 
            that is used by multiple distinct apps. The apps only have to set 
            the variable to be instrumented.

        :param excluded_handlers: Handlers that should be ignored. List of 
            strings is turned into regex patterns.

        :param buckets: Buckets for the histogram. Defaults to Prometheus default.

        :param metric_name: Name of the latency metric.

        :param label_names: Names of the three labels used for the metric. Does 
            not influence the label values. Defaults to ("method", "handler", 
            "status",).

        :param round_latency_decimals: Number of decimals latencies should be 
            rounded to. Ignored unless `should_round_latency_decimals` is `True`.

        :param env_var_name: Any valid os environment variable name that 
            will be checked for existence before instrumentation. Ignored 
            unless `should_respect_env_var_existence` is `True`.
        """

        self.should_group_status_codes = should_group_status_codes
        self.should_ignore_untemplated = should_ignore_untemplated
        self.should_group_untemplated = should_group_untemplated
        self.should_round_latency_decimals = should_round_latency_decimals
        self.should_respect_env_var_existence = should_respect_env_var_existence

        self.round_latency_decimals = round_latency_decimals
        self.label_names = label_names
        self.env_var_name = env_var_name

        if excluded_handlers:
            self.excluded_handlers = [re.compile(path) for path in excluded_handlers]
        else:
            self.excluded_handlers = []

        if buckets[-1] == float("inf"):
            self.buckets = buckets
        else:
            self.buckets = buckets + (float("inf"),)

        self.histogram = Histogram(
            name=metric_name,
            documentation="Duration of HTTP requests in seconds",
            labelnames=self.label_names,
            buckets=self.buckets,
        )

    def instrument(self, app: FastAPI) -> "self":
        """Performs the instrumentation by adding middleware and endpoint.
        
        :param app: FastAPI app to be instrumented.
        :param return: self.
        """

        if self.should_respect_env_var_existence and self.env_var_name not in os.environ:
            return self

        @app.middleware("http")
        async def dispatch_middleware(request: Request, call_next) -> Response:
            start_time = default_timer()

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

            if self.should_round_latency_decimals:
                duration = round(duration, self.round_latency_decimals)

            self.histogram.labels(
                *self._create_label_tuple(method, handler, status)
            ).observe(duration)

            return response

        return self

    def expose(self, app: FastAPI, endpoint: str = "/metrics") -> "self":
        """Exposes Prometheus metrics by adding endpoint to the given app.

        **Important**: There are many different ways to expose metrics. This is 
        just one of them, suited for both multiprocess and singleprocess mode. 
        Refer to the Prometheus Python client documentation for more information.

        :param app: FastAPI where the endpoint should be added to.
        :param endpoint: Route of the endpoint. Defaults to "/metrics".
        :param return: self.
        """

        if self.should_respect_env_var_existence and self.env_var_name not in os.environ:
            return self

        from prometheus_client import (CONTENT_TYPE_LATEST, REGISTRY,
                                       CollectorRegistry, generate_latest,
                                       multiprocess)

        if "prometheus_multiproc_dir" in os.environ:
            pmd = os.environ["prometheus_multiproc_dir"]
            if os.path.isdir(pmd):
                registry = CollectorRegistry()
                multiprocess.MultiProcessCollector(registry)
            else:
                raise ValueError(
                    f"Env var prometheus_multiproc_dir='{pmd}' not a directory."
                )
        else:
            registry = REGISTRY

        @app.get("/metrics")
        def metrics():
            return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

        return self

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
