from typing import Callable, Optional, Sequence, Union

from fastapi import FastAPI
from prometheus_client import REGISTRY, CollectorRegistry, Counter, Histogram, Summary

from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_fastapi_instrumentator.metrics import Info

PING_TOTAL = Counter("ping", "Number of pings calls.")


def my_metrics(
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
) -> Optional[Callable[[Info], None]]:
    def is_duplicated_time_series(error: ValueError) -> bool:
        return any(
            map(
                error.args[0].__contains__,
                [
                    "Duplicated timeseries in CollectorRegistry:",
                    "Duplicated time series in CollectorRegistry:",
                ],
            )
        )

    if latency_highr_buckets[-1] != float("inf"):
        latency_highr_buckets = [*latency_highr_buckets, float("inf")]

    if latency_lowr_buckets[-1] != float("inf"):
        latency_lowr_buckets = [*latency_lowr_buckets, float("inf")]

    # Starlette will call app.build_middleware_stack() with every new middleware
    # added, which will call all this again, which will make the registry
    # complain about duplicated metrics.
    #
    # The Python Prometheus client currently doesn't seem to have a way to
    # verify if adding a metric will cause errors or not, so the only way to
    # handle it seems to be with this try block.
    try:
        TOTAL = Counter(
            name="http_requests_total",
            documentation="Total number of requests by method, status and handler.",
            labelnames=(
                "my_method",
                "my_status",
                "my_handler",
            ),
            registry=registry,
        )

        IN_SIZE = Summary(
            name="http_request_size_bytes",
            documentation=(
                "Content length of incoming requests by handler. "
                "Only value of header is respected. Otherwise ignored. "
                "No percentile calculated. "
            ),
            labelnames=("my_handler",),
            registry=registry,
        )

        OUT_SIZE = Summary(
            name="http_response_size_bytes",
            documentation=(
                "Content length of outgoing responses by handler. "
                "Only value of header is respected. Otherwise ignored. "
                "No percentile calculated. "
            ),
            labelnames=("my_handler",),
            registry=registry,
        )

        LATENCY_HIGHR = Histogram(
            name="http_request_duration_highr_seconds",
            documentation=(
                "Latency with many buckets but no API specific labels. "
                "Made for more accurate percentile calculations. "
            ),
            buckets=latency_highr_buckets,
            registry=registry,
        )

        LATENCY_LOWR = Histogram(
            name="http_request_duration_seconds",
            documentation=(
                "Latency with only few buckets by handler. "
                "Made to be only used if aggregation by handler is important. "
            ),
            buckets=latency_lowr_buckets,
            labelnames=(
                "my_method",
                "my_handler",
            ),
            registry=registry,
        )

        def instrumentation(info: Info) -> None:
            TOTAL.labels(info.method, info.modified_status, info.modified_handler).inc()

            IN_SIZE.labels(info.modified_handler).observe(
                int(info.request.headers.get("Content-Length", 0))
            )

            if info.response and hasattr(info.response, "headers"):
                OUT_SIZE.labels(info.modified_handler).observe(
                    int(info.response.headers.get("Content-Length", 0))
                )
            else:
                OUT_SIZE.labels(info.modified_handler).observe(0)

            if info.modified_status.startswith("2"):
                LATENCY_HIGHR.observe(info.modified_duration)

            LATENCY_LOWR.labels(info.modified_handler, info.method).observe(
                info.modified_duration
            )

        return instrumentation

    except ValueError as e:
        if not is_duplicated_time_series(e):
            raise e

    return None


app = FastAPI()

Instrumentator().instrument(app).add(my_metrics()).expose(app)


@app.get("/ping")
def get_ping():
    PING_TOTAL.inc()
    return "pong"
