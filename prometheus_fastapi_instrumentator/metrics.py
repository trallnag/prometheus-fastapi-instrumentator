from typing import Callable

from prometheus_client import Histogram
from starlette.requests import Request
from starlette.responses import Response


class Info:
    def __init__(
        self,
        request: Request,
        response: Response or None,
        modified_handler: str,
        modified_status: str,
        modified_duration: float,
    ):
        """
        :param request: Request object.

        :param response: Response object or `None` (just like returned by FastAPI).

        :param modified_handler: Handler representation after processing by 
            instrumentator. For example grouped to `none` if not templated.

        :param modified_status: Status code representation after processing by
            instrumentator. For example grouping into `2xx`, `3xx` and so on.

        :param modified_duration: Latency representation after processing by 
            instrumentator. For example rounding of decimals. Seconds.
        """

        self.request = request
        self.response = response
        self.modified_handler = modified_handler
        self.modified_status = modified_status
        self.modified_duration = modified_duration


def http_request_duration_seconds(
    metric_name: str = "http_request_duration_seconds",
    buckets: tuple = Histogram.DEFAULT_BUCKETS,
    label_names: tuple = ("method", "handler", "status",),
) -> Callable[[Info], None]:
    """Default metric for the Prometheus FastAPI Instrumentator.

    :param metric_name: Name of the latency metric.

    :param buckets: Buckets for the histogram. Defaults to Prometheus default.

    :param label_names: Names of the three labels used for the metric. Does 
        not influence the label values. Defaults to ("method", "handler", "status",).
    """

    if buckets[-1] != float("inf"):
        buckets = buckets + (float("inf"),)

    METRIC = Histogram(
        name=metric_name,
        documentation="Duration of HTTP requests in seconds",
        labelnames=label_names,
        buckets=buckets,
    )

    def instrumentation(info: Info) -> None:
        METRIC.labels(
            info.request.method, info.modified_handler, info.modified_status
        ).observe(info.modified_duration)

    return instrumentation
