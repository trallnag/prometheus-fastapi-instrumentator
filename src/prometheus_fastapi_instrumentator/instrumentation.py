import gzip
import os
import re
from enum import Enum
from typing import Callable, List, Optional, Union

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from prometheus_fastapi_instrumentator import metrics
from prometheus_fastapi_instrumentator.middleware import (
    PrometheusInstrumentatorMiddleware,
)


class PrometheusFastApiInstrumentator:
    def __init__(
        self,
        should_group_status_codes: bool = True,
        should_ignore_untemplated: bool = False,
        should_group_untemplated: bool = True,
        should_round_latency_decimals: bool = False,
        should_respect_env_var: bool = False,
        should_instrument_requests_inprogress: bool = False,
        excluded_handlers: List[str] = None,
        round_latency_decimals: int = 4,
        env_var_name: str = "ENABLE_METRICS",
        inprogress_name: str = "http_requests_inprogress",
        inprogress_labels: bool = False,
    ):
        """Create a Prometheus FastAPI Instrumentator.

        Args:
            should_group_status_codes (bool): Should status codes be grouped into
                `2xx`, `3xx` and so on? Defaults to `True`.

            should_ignore_untemplated (bool): Should requests without a matching
                template be ignored? Defaults to `False`. This means that by
                default a request like `curl -X GET localhost:80/doesnotexist`
                will be ignored.

            should_group_untemplated (bool): Should requests without a matching
                template be grouped to handler `none`? Defaults to `True`.

            should_round_latency_decimals: Should recorded latencies be
                rounded to a certain number of decimals?

            should_respect_env_var (bool): Should the instrumentator only work - for
                example the methods `instrument()` and `expose()` - if a
                certain environment variable is set to `true`? Usecase: A base
                FastAPI app that is used by multiple distinct apps. The apps
                only have to set the variable to be instrumented. Defaults to
                `False`.

            should_instrument_requests_inprogress (bool): Enables a gauge that shows
                the inprogress requests. See also the related args starting
                with `inprogress`. Defaults to `False`.

            excluded_handlers (List[str]): List of strings that will be compiled
                to regex patterns. All matches will be skipped and not
                instrumented. Defaults to `[]`.

            round_latency_decimals (int): Number of decimals latencies should be
                rounded to. Ignored unless `should_round_latency_decimals` is
                `True`. Defaults to `4`.

            env_var_name (str): Any valid os environment variable name that will
                be checked for existence before instrumentation. Ignored unless
                `should_respect_env_var` is `True`. Defaults to `"ENABLE_METRICS"`.

            inprogress_name (str): Name of the gauge. Defaults to
                `http_requests_inprogress`. Ignored unless
                `should_instrument_requests_inprogress` is `True`.

            inprogress_labels (bool): Should labels `method` and `handler` be
                part of the inprogress label? Ignored unless
                `should_instrument_requests_inprogress` is `True`. Defaults to `False`.
        """

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

        if excluded_handlers is None:
            excluded_handlers = []

        self.excluded_handlers = [re.compile(path) for path in excluded_handlers]

        self.instrumentations: List[Callable[[metrics.Info], None]] = []

    def instrument(self, app: FastAPI):
        """Performs the instrumentation by adding middleware.

        The middleware iterates through all `instrumentations` and executes them.

        Args:
            app (FastAPI): FastAPI app instance.

        Raises:
            e: Only raised if FastAPI itself throws an exception.

        Returns:
            self: Instrumentator. Builder Pattern.
        """

        if (
            self.should_respect_env_var
            and os.environ.get(self.env_var_name, "false") != "true"
        ):
            return self

        app.add_middleware(
            PrometheusInstrumentatorMiddleware,
            should_group_status_codes=self.should_group_status_codes,
            should_ignore_untemplated=self.should_ignore_untemplated,
            should_group_untemplated=self.should_group_untemplated,
            should_round_latency_decimals=self.should_round_latency_decimals,
            should_respect_env_var=self.should_respect_env_var,
            should_instrument_requests_inprogress=self.should_instrument_requests_inprogress,
            round_latency_decimals=self.round_latency_decimals,
            env_var_name=self.env_var_name,
            inprogress_name=self.inprogress_name,
            inprogress_labels=self.inprogress_labels,
            instrumentations=self.instrumentations,
            excluded_handlers=self.excluded_handlers,
        )
        return self

    def expose(
        self,
        app: FastAPI,
        should_gzip: bool = False,
        endpoint: str = "/metrics",
        include_in_schema: bool = True,
        tags: Optional[List[Union[str, Enum]]] = None,
        **kwargs,
    ):
        """Exposes endpoint for metrics.

        Args:
            app: FastAPI app instance. Endpoint will be added to this app.

            should_gzip: Should the endpoint return compressed data? It will
                also check for `gzip` in the `Accept-Encoding` header.
                Compression consumes more CPU cycles. In most cases it's best
                to just leave this option off since network bandwith is usually
                cheaper than CPU cycles. Defaults to `False`.

            endpoint: Endpoint on which metrics should be exposed.

            include_in_schema: Should the endpoint show up in the documentation?

            tags (List[str], optional): If you manage your routes with tags.
                Defaults to None.

            kwargs: Will be passed to FastAPI route annotation.

        Raises:
            ValueError: If `prometheus_multiproc_dir` env var is found but
                doesn't point to a valid directory.

        Returns:
            self: Instrumentator. Builder Pattern.
        """

        if (
            self.should_respect_env_var
            and os.environ.get(self.env_var_name, "false") != "true"
        ):
            return self

        from prometheus_client import (
            CONTENT_TYPE_LATEST,
            REGISTRY,
            CollectorRegistry,
            generate_latest,
            multiprocess,
        )

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

        @app.get(endpoint, include_in_schema=include_in_schema, tags=tags, **kwargs)
        def metrics(request: Request):
            """Endpoint that serves Prometheus metrics."""

            if should_gzip and "gzip" in request.headers.get("Accept-Encoding", ""):
                resp = Response(content=gzip.compress(generate_latest(registry)))
                resp.headers["Content-Type"] = CONTENT_TYPE_LATEST
                resp.headers["Content-Encoding"] = "gzip"
            else:
                resp = Response(content=generate_latest(registry))
                resp.headers["Content-Type"] = CONTENT_TYPE_LATEST

            return resp

        return self

    def add(self, instrumentation_function: Callable[[metrics.Info], None]):
        """Adds function to list of instrumentations.

        Args:
            instrumentation_function (Callable[[metrics.Info], None]): Function
                that will be executed during every request handler call (if
                not excluded). See above for detailed information on the
                interface of the function.

        Returns:
            self: Instrumentator. Builder Pattern.
        """

        self.instrumentations.append(instrumentation_function)

        return self
