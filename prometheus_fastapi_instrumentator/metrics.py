from typing import Callable

from prometheus_client import Histogram, Summary
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

    :return: 
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


def http_request_content_length_bytes(
    should_drop_handler: bool = False,
) -> Callable[[Info], None]:
    """Record the content length of incoming requests.

    Requests / Responses with missing `Content-Length` will be skipped.

    :param metric_name: Name of the latency metric.
    """

    if should_drop_handler:
        METRIC = Summary(
            "http_request_content_bytes",
            "Content bytes of requests.",
            labelnames=("method", "status",),
        )
    else:
        METRIC = Summary(
            "http_request_content_bytes",
            "Content bytes of requests.",
            labelnames=("method", "handler", "status",),
        )

    def instrumentation(info: Info) -> None:
        content_length = info.request.headers.get("Content-Length", None)
        if content_length is not None:
            if should_drop_handler:
                METRIC.labels(info.request.method, info.modified_status).observe(
                    int(content_length)
                )
            else:
                METRIC.labels(
                    info.request.method, info.modified_handler, info.modified_status
                ).observe(int(content_length))

    return instrumentation


def http_response_content_length_bytes(
    should_drop_handler: bool = False,
) -> Callable[[Info], None]:
    """Record the content length of outgoing responses.

    Responses with missing `Content-Length` will be skipped.

    :param metric_name: Name of the latency metric.
    """

    if should_drop_handler:
        METRIC = Summary(
            "http_response_content_bytes",
            "Content bytes of responses.",
            labelnames=("method", "status",),
        )
    else:
        METRIC = Summary(
            "http_response_content_bytes",
            "Content bytes of responses.",
            labelnames=("method", "handler", "status",),
        )

    def instrumentation(info: Info) -> None:
        content_length = info.response.headers.get("Content-Length", None)
        if content_length is not None:
            if should_drop_handler:
                METRIC.labels(info.request.method, info.modified_status).observe(
                    int(content_length)
                )
            else:
                METRIC.labels(
                    info.request.method, info.modified_handler, info.modified_status
                ).observe(int(content_length))

    return instrumentation


def http_content_length_bytes(
    should_drop_handler: bool = False,
) -> Callable[[Info], None]:
    """Record the combined content length of requests and responses.

    Requests / Responses with missing `Content-Length` will be skipped.

    :param metric_name: Name of the latency metric.
    """

    if should_drop_handler:
        METRIC = Summary(
            "http_content_length_bytes",
            "Content bytes of requests and responses.",
            labelnames=("method", "status",),
        )
    else:
        METRIC = Summary(
            "http_content_length_bytes",
            "Content bytes of requests and responses.",
            labelnames=("method", "handler", "status",),
        )

    def instrumentation(info: Info) -> None:
        request_cl = info.request.headers.get("Content-Length", None)
        response_cl = info.response.headers.get("Content-Length", None)

        if request_cl and response_cl:
            content_length = int(request_cl) + int(response_cl)
        elif request_cl:
            content_length = int(request_cl)
        elif response_cl:
            content_length = int(response_cl)
        else:
            content_length = None

        if content_length is not None:
            if should_drop_handler:
                METRIC.labels(info.request.method, info.modified_status).observe(
                    content_length
                )
            else:
                METRIC.labels(
                    info.request.method, info.modified_handler, info.modified_status
                ).observe(content_length)

    return instrumentation
