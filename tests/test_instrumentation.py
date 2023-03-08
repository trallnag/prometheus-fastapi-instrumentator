import asyncio
import os
from http import HTTPStatus
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Info, generate_latest
from requests import Response as TestClientResponse
from starlette.responses import Response
from starlette.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator, metrics

setattr(TestClientResponse, "__test__", False)

# ------------------------------------------------------------------------------
# Setup


CUSTOM_METRICS = ["http_request_duration_seconds"]


def create_app() -> FastAPI:
    app = FastAPI()

    # Unregister all collectors.
    collectors = list(REGISTRY._collector_to_names.keys())
    print(f"before unregister collectors={collectors}")
    for collector in collectors:
        REGISTRY.unregister(collector)
    print(f"after unregister collectors={list(REGISTRY._collector_to_names.keys())}")

    # Import default collectors.
    from prometheus_client import gc_collector, platform_collector, process_collector

    # Re-register default collectors.
    process_collector.ProcessCollector()
    platform_collector.PlatformCollector()
    gc_collector.GCCollector()

    print(f"after re-register collectors={list(REGISTRY._collector_to_names.keys())}")

    @app.get("/")
    def read_root():
        return "Hello World!"

    @app.get("/sleep")
    async def sleep(seconds: float):
        await asyncio.sleep(seconds)
        return f"I have slept for {seconds}s"

    @app.get("/always_error")
    def read_always_error():
        raise HTTPException(status_code=404, detail="Not really error")

    @app.get("/always_error_httpstatus_enum")
    def read_always_error_httpstatus_enum():
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Not really an error"
        )

    @app.get("/ignore")
    def read_ignore():
        return "Should be ignored"

    @app.get("/items/{item_id}")
    def read_item(item_id: int, q: Optional[str] = None):
        return {"item_id": item_id, "q": q}

    @app.get("/just_another_endpoint")
    def read_just_another_endpoint():
        return "Green is my pepper"

    @app.post("/items")
    def create_item(item: Dict[Any, Any]):
        return None

    return app


def expose_metrics(app: FastAPI) -> None:
    if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
        pmd = os.environ["PROMETHEUS_MULTIPROC_DIR"]
        print(f"Env var PROMETHEUS_MULTIPROC_DIR='{pmd}' detected.")
        if os.path.isdir(pmd):
            print(f"Env var PROMETHEUS_MULTIPROC_DIR='{pmd}' is a dir.")
            from prometheus_client import CollectorRegistry, multiprocess

            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
        else:
            raise ValueError(f"Env var PROMETHEUS_MULTIPROC_DIR='{pmd}' not a directory.")
    else:
        registry = REGISTRY

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

    return registry


def get_response(client: TestClient, path: str) -> TestClientResponse:
    response = client.get(path)

    print(f"\nResponse  path='{path}' status='{response.status_code}':\n")
    for line in response.content.split(b"\n"):
        print(line.decode())

    return response


def assert_is_not_multiprocess(response: TestClientResponse) -> None:
    assert response.status_code == 200
    assert b"Multiprocess" not in response.content
    assert b"# HELP process_cpu_seconds_total" in response.content


def assert_request_count(
    expected: float,
    name: str = "http_request_duration_seconds_count",
    handler: str = "/",
    method: str = "GET",
    status: str = "2xx",
) -> None:
    result = REGISTRY.get_sample_value(
        name, {"handler": handler, "method": method, "status": status}
    )
    print(
        (
            f"{name} handler={handler} method={method} status={status} "
            f"result={result} expected={expected}"
        )
    )
    assert result == expected
    assert result + 1.0 != expected


# ------------------------------------------------------------------------------
# Tests


def test_app():
    app = create_app()
    client = TestClient(app)

    response = get_response(client, "/")
    assert response.status_code == 200
    assert b"Hello World!" in response.content

    response = get_response(client, "/always_error")
    assert response.status_code == 404
    assert b"Not really error" in response.content

    response = get_response(client, "/always_error_httpstatus_enum")
    assert response.status_code == 404
    assert b"Not really an error" in response.content

    response = get_response(client, "/items/678?q=43243")
    assert response.status_code == 200
    assert b"678" in response.content

    response = get_response(client, "/items/hallo")
    assert response.status_code == 422
    assert b"value is not a valid integer" in response.content

    response = get_response(client, "/just_another_endpoint")
    assert response.status_code == 200
    assert b"Green" in response.content


def test_metrics_endpoint_availability():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(metrics.latency()).instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert_request_count(2)


# ------------------------------------------------------------------------------
# Test gzip


def test_gzip_accepted():
    app = create_app()
    Instrumentator().instrument(app).expose(app, should_gzip=True)
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/")

    response = get_response(client, "/metrics")

    assert response.headers["Content-Encoding"] == "gzip"
    assert int(response.headers["Content-Length"]) <= 2000


def test_gzip_not_accepted():
    app = create_app()
    Instrumentator().instrument(app).expose(app, should_gzip=False)
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/")

    response = get_response(client, "/metrics")

    assert response.headers.get("Content-Encoding") is None
    assert int(response.headers["Content-Length"]) >= 2000


# ------------------------------------------------------------------------------
# Test metric name


def test_default_metric_name():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(metrics.latency()).instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert_request_count(1)
    assert b"http_request_duration_seconds" in response.content


def test_default_without_add():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(metrics.latency()).instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert_request_count(1)
    assert b"http_request_duration_seconds" in response.content


def test_custom_metric_name():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(
        metrics.latency(metric_name="fastapi_latency")
    ).instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert_request_count(1, name="fastapi_latency_count")
    assert b"fastapi_latency" in response.content
    assert b"http_request_duration_seconds" not in response.content


# ------------------------------------------------------------------------------
# Test grouping of status codes.


def test_grouped_status_codes():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(metrics.latency()).instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert_request_count(1)
    assert b'status="2xx"' in response.content
    assert b'status="200"' not in response.content


def test_grouped_status_codes_with_enumeration():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(metrics.latency()).instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/always_error_httpstatus_enum")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert b'status="4xx"' in response.content
    assert b'status="H00"' not in response.content


def test_ungrouped_status_codes():
    app = create_app()
    Instrumentator(should_group_status_codes=False).add(metrics.latency()).instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert_request_count(1, status="200")
    assert b'status="2xx"' not in response.content
    assert b'status="200"' in response.content


# ------------------------------------------------------------------------------
# Test handling of templates / untemplated.


def test_ignore_untemplated():
    app = create_app()
    Instrumentator(should_ignore_untemplated=True).add(metrics.latency()).instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/items/678?q=43243")
    get_response(client, "/does_not_exist")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert_request_count(1)
    assert b'handler="/does_not_exist"' not in response.content
    assert b'handler="none"' not in response.content


def test_dont_ignore_untemplated_ungrouped():
    app = create_app()
    Instrumentator(should_ignore_untemplated=False, should_group_untemplated=False).add(
        metrics.latency()
    ).instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/")
    get_response(client, "/items/678?q=43243")
    get_response(client, "/does_not_exist")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert_request_count(2)
    assert b'handler="/does_not_exist"' in response.content
    assert b'handler="none"' not in response.content


def test_grouping_untemplated():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(metrics.latency()).instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/items/678?q=43243")
    get_response(client, "/does_not_exist")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert_request_count(1)
    assert b'handler="/does_not_exist"' not in response.content
    assert b'handler="none"' in response.content


def test_excluding_handlers():
    app = create_app()
    Instrumentator(excluded_handlers=["fefefwefwe"]).add(metrics.latency()).instrument(
        app
    )
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/metrics")
    get_response(client, "/fefefwefwe")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert_request_count(1)
    assert b'handler="/metrics"' in response.content
    assert b'handler="/fefefwefwe"' not in response.content
    assert b'handler="none"' not in response.content


def test_excluding_handlers_regex():
    app = create_app()
    Instrumentator(excluded_handlers=["^/$"]).add(metrics.latency()).instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/ignore")
    get_response(client, "/ignore")
    get_response(client, "/")

    response = get_response(client, "/metrics")

    assert b'handler="/"' not in response.content
    assert b'handler="none"' not in response.content
    assert b'handler="/ignore"' in response.content


def test_excluded_handlers_none():
    app = create_app()
    exporter = Instrumentator(excluded_handlers=[]).add(metrics.latency()).instrument(app)
    expose_metrics(app)

    assert len(exporter.excluded_handlers) == 0
    assert isinstance(exporter.excluded_handlers, list)
    assert exporter.excluded_handlers is not None


# ------------------------------------------------------------------------------
# Test bucket without infinity.


def test_bucket_without_inf():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(
        metrics.latency(
            buckets=(
                1,
                2,
                3,
            )
        )
    ).instrument(app).expose(app)
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert b"http_request_duration_seconds" in response.content


# ------------------------------------------------------------------------------
# Test env var option.


def test_should_respect_env_var_existence_exists():
    app = create_app()
    Instrumentator(should_respect_env_var=True, env_var_name="eoioerwjioGFIUONEIO").add(
        metrics.latency()
    ).instrument(app).expose(app)
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert response.status_code == 404


def test_should_respect_env_var_existence_not_exists():
    app = create_app()
    os.environ["eoioerwjioGFIUONEIO"] = "true"
    Instrumentator(should_respect_env_var=True, env_var_name="eoioerwjioGFIUONEIO").add(
        metrics.latency()
    ).instrument(app).expose(app)
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert response.status_code == 200


# ------------------------------------------------------------------------------
# Test decimal rounding.


def calc_entropy(decimal_str: str):
    decimals = [int(x) for x in decimal_str]
    print(decimals)
    return sum(abs(decimals[i] - decimals[i - 1]) for i in range(len(decimals)) if i != 0)


def test_entropy():
    assert calc_entropy([1, 0, 0, 4, 0]) == 9


def test_default_no_rounding():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(
        metrics.latency(
            buckets=(
                1,
                2,
                3,
            )
        )
    ).instrument(app).expose(app)
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/")
    get_response(client, "/")

    _ = get_response(client, "/metrics")

    result = REGISTRY.get_sample_value(
        "http_request_duration_seconds_sum",
        {"handler": "/", "method": "GET", "status": "2xx"},
    )

    entropy = calc_entropy(str(result).split(".")[1][4:])

    assert entropy > 15


def test_rounding():
    app = create_app()
    Instrumentator(should_round_latency_decimals=True).add(
        metrics.latency(
            buckets=(
                1,
                2,
                3,
            )
        )
    ).instrument(app).expose(app)
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/")
    get_response(client, "/")

    _ = get_response(client, "/metrics")

    result = REGISTRY.get_sample_value(
        "http_request_duration_seconds_sum",
        {"handler": "/", "method": "GET", "status": "2xx"},
    )

    entropy = calc_entropy(str(result).split(".")[1][4:])

    assert entropy < 10


def test_custom_async_instrumentation():
    app = create_app()
    client = TestClient(app)

    sync_metric = Info("sync_metric", "Documentation")
    async_metric = Info("async_metric", "Documentation")

    async def get_value():
        return "X_ASYNC_X"

    async def async_function(x):
        value = await get_value()
        async_metric.info({"type": value})

    def sync_function(_):
        sync_metric.info({"type": "X_SYNC_X"})

    instrumentator = Instrumentator()
    instrumentator.add(sync_function)
    instrumentator.add(async_function)
    instrumentator.instrument(app).expose(app)

    get_response(client, "/")
    get_response(client, "/metrics")

    result_async = REGISTRY.get_sample_value(
        "async_metric_info",
        {"type": "X_ASYNC_X"},
    )

    assert result_async > 0

    result_sync = REGISTRY.get_sample_value(
        "sync_metric_info",
        {"type": "X_SYNC_X"},
    )

    assert result_sync > 0
