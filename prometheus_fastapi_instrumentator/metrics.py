from typing import Callable, Tuple

from prometheus_client import Histogram, Summary
from starlette.requests import Request
from starlette.responses import Response


class Info:
    def __init__(
        self,
        request: Request,
        response: Response or None,
        method: str,
        modified_handler: str,
        modified_status: str,
        modified_duration: float,
    ):
        """
        :param request: Request object.

        :param response: Response object or `None` (just like returned by FastAPI).

        :param method: Method of the request.

        :param modified_handler: Handler representation after processing by 
            instrumentator. For example grouped to `none` if not templated.

        :param modified_status: Status code representation after processing by
            instrumentator. For example grouping into `2xx`, `3xx` and so on.

        :param modified_duration: Latency representation after processing by 
            instrumentator. For example rounding of decimals. Seconds.
        """

        self.request = request
        self.response = response
        self.method = method
        self.modified_handler = modified_handler
        self.modified_status = modified_status
        self.modified_duration = modified_duration


def _build_label_attribute_names(
    should_include_handler: bool,
    should_include_method: bool,
    should_include_status: bool,
) -> Tuple[list, list]:
    label_names = []
    info_attribute_names = []

    if should_include_handler:
        label_names.append("handler")
        info_attribute_names.append("modified_handler")

    if should_include_method:
        label_names.append("method")
        info_attribute_names.append("method")

    if should_include_status:
        label_names.append("status")
        info_attribute_names.append("modified_status")

    return label_names, info_attribute_names


def latency(
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


def request_size(
    metric_name: str = "http_request_size_bytes",
    metric_doc: str = "Content bytes of requests.",
    should_include_handler: bool = True,
    should_include_method: bool = True,
    should_include_status: bool = True,
) -> Callable[[Info], None]:
    """Record the content length of incoming requests.

    Requests / Responses with missing `Content-Length` will be skipped.
    """

    label_names, info_attribute_names = _build_label_attribute_names(
        should_include_handler, should_include_method, should_include_status
    )

    if label_names:
        METRIC = Summary(metric_name, metric_doc, labelnames=label_names)
    else:
        METRIC = Summary(metric_name, metric_doc)

    def instrumentation(info: Info) -> None:
        content_length = info.request.headers.get("Content-Length", None)
        if content_length is not None:
            if label_names:
                label_values = []
                for attribute_name in info_attribute_names:
                    label_values.append(getattr(info, attribute_name))
                METRIC.labels(*label_values).observe(int(content_length))
            else:
                METRIC.observe(int(content_length))

    return instrumentation


def response_size(
    metric_name: str = "http_response_size_bytes",
    metric_doc: str = "Content bytes of responses.",
    should_include_handler: bool = True,
    should_include_method: bool = True,
    should_include_status: bool = True,
) -> Callable[[Info], None]:
    """Record the content length of outgoing responses.

    Responses with missing `Content-Length` will be skipped.
    """

    label_names, info_attribute_names = _build_label_attribute_names(
        should_include_handler, should_include_method, should_include_status
    )

    if label_names:
        METRIC = Summary(metric_name, metric_doc, labelnames=label_names)
    else:
        METRIC = Summary(metric_name, metric_doc)

    def instrumentation(info: Info) -> None:
        content_length = info.response.headers.get("Content-Length", None)
        if content_length is not None:
            if label_names:
                label_values = []
                for attribute_name in info_attribute_names:
                    label_values.append(getattr(info, attribute_name))
                METRIC.labels(*label_values).observe(int(content_length))
            else:
                METRIC.observe(int(content_length))

    return instrumentation


def combined_size(
    metric_name: str = "http_combined_size_bytes",
    metric_doc: str = "Content bytes of requests and responses.",
    should_include_handler: bool = True,
    should_include_method: bool = True,
    should_include_status: bool = True,
) -> Callable[[Info], None]:
    """Record the combined content length of requests and responses.

    Requests / Responses with missing `Content-Length` will be skipped.
    """

    label_names, info_attribute_names = _build_label_attribute_names(
        should_include_handler, should_include_method, should_include_status
    )

    if label_names:
        METRIC = Summary(metric_name, metric_doc, labelnames=label_names)
    else:
        METRIC = Summary(metric_name, metric_doc)

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
            if label_names:
                label_values = []
                for attribute_name in info_attribute_names:
                    label_values.append(getattr(info, attribute_name))
                METRIC.labels(*label_values).observe(int(content_length))
            else:
                METRIC.observe(int(content_length))

    return instrumentation
