from typing import Optional
import os

from fastapi import FastAPI, HTTPException
from starlette.testclient import TestClient
from starlette.responses import Response
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
import pytest


# ==============================================================================
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
    from prometheus_client import platform_collector
    from prometheus_client import process_collector
    from prometheus_client import gc_collector

    # Re-register default collectors.
    process_collector.ProcessCollector()
    platform_collector.PlatformCollector()
    gc_collector.GCCollector()

    print(f"after re-register collectors={list(REGISTRY._collector_to_names.keys())}")

    @app.get("/")
    def read_root():
        return "Hello World!"

    @app.get("/always_error")
    def read_always_error():
        raise HTTPException(status_code=404, detail="Not really error")

    @app.get("/ignore")
    def read_ignore():
        return "Should be ignored"

    @app.get("/items/{item_id}")
    def read_item(item_id: int, q: Optional[str] = None):
        return {"item_id": item_id, "q": q}

    @app.get("/just_another_endpoint")
    def read_just_another_endpoint():
        return "Green is my pepper"

    return app


def expose_metrics(app: FastAPI) -> None:
    if "prometheus_multiproc_dir" in os.environ:
        pmd = os.environ["prometheus_multiproc_dir"]
        print(f"Env var prometheus_multiproc_dir='{pmd}' detected.")
        if os.path.isdir(pmd):
            print(f"Env var prometheus_multiproc_dir='{pmd}' is a dir.")
            from prometheus_client import multiprocess, CollectorRegistry

            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
        else:
            raise ValueError(f"Env var prometheus_multiproc_dir='{pmd}' not a directory.")
    else:
        registry = REGISTRY

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

    return registry


def get_response(client: TestClient, path: str) -> Response:
    response = client.get(path)

    print(f"\nResponse  path='{path}' status='{response.status_code}':\n")
    for line in response.content.split(b"\n"):
        print(line.decode())

    return response


def assert_is_not_multiprocess(response: Response) -> None:
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


# ==============================================================================
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
    Instrumentator().instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert_request_count(2)


# ------------------------------------------------------------------------------
# Test metric name


def test_default_metric_name():
    app = create_app()
    Instrumentator().instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert_request_count(1)
    assert b"http_request_duration_seconds" in response.content


def test_custom_metric_name():
    app = create_app()
    Instrumentator(metric_name="fastapi_latency").instrument(app)
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
    Instrumentator().instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert_request_count(1)
    assert b'status="2xx"' in response.content
    assert b'status="200"' not in response.content


def test_ungrouped_status_codes():
    app = create_app()
    Instrumentator(should_group_status_codes=False).instrument(app)
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
    Instrumentator(should_ignore_untemplated=True).instrument(app)
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
    Instrumentator(
        should_ignore_untemplated=False, should_group_untemplated=False
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
    Instrumentator().instrument(app)
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
    Instrumentator(excluded_handlers=["fefefwefwe"]).instrument(app)
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


# ------------------------------------------------------------------------------
# Test label names.


def test_default_label_names():
    app = create_app()
    Instrumentator().instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert_request_count(1)
    assert b"method=" in response.content
    assert b"handler=" in response.content
    assert b"status=" in response.content


def test_custom_label_names():
    app = create_app()
    Instrumentator(label_names=("a", "b", "c",)).instrument(app)
    expose_metrics(app)
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert (
        REGISTRY.get_sample_value(
            "http_request_duration_seconds_count", {"a": "GET", "b": "/", "c": "2xx"}
        )
        == 1
    )
    assert b"a=" in response.content
    assert b"b=" in response.content
    assert b"c=" in response.content
    assert b"method=" not in response.content
    assert b"handler=" not in response.content
    assert b"status=" not in response.content


# ------------------------------------------------------------------------------
# Test None excluded handlers.


def test_excluded_handlers_none():
    app = create_app()
    exporter = Instrumentator(excluded_handlers=None).instrument(app)
    expose_metrics(app)

    assert len(exporter.excluded_handlers) == 0
    assert isinstance(exporter.excluded_handlers, list)
    assert exporter.excluded_handlers is not None


# ------------------------------------------------------------------------------
# Test bucket without infinity.


def test_bucket_without_inf():
    app = create_app()
    Instrumentator(buckets=(1, 2, 3,)).instrument(app).expose(app)
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert_is_not_multiprocess(response)
    assert b"http_request_duration_seconds" in response.content


# ------------------------------------------------------------------------------
# Test decimal rounding.


def test_default_no_rounding():
    app = create_app()
    Instrumentator(buckets=(1, 2, 3,)).instrument(app).expose(app)
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/")
    get_response(client, "/")

    _ = get_response(client, "/metrics")

    result = REGISTRY.get_sample_value(
        "http_request_duration_seconds_sum",
        {"handler": "/", "method": "GET", "status": "2xx"},
    )

    assert len(str(result)) >= 10


def test_rounding():
    app = create_app()
    Instrumentator(buckets=(1, 2, 3,), should_round_latency_decimals=True).instrument(
        app
    ).expose(app)
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/")
    get_response(client, "/")

    _ = get_response(client, "/metrics")

    result = REGISTRY.get_sample_value(
        "http_request_duration_seconds_sum",
        {"handler": "/", "method": "GET", "status": "2xx"},
    )

    assert len(str(result).strip("0")) <= 8


# ------------------------------------------------------------------------------
# Test with multiprocess reg.


def is_prometheus_multiproc_set():
    if "prometheus_multiproc_dir" in os.environ:
        pmd = os.environ["prometheus_multiproc_dir"]
        if os.path.isdir(pmd):
            return True
    else:
        return False


# The environment variable MUST be set before anything regarding Prometheus is
# imported. That is why we cannot simply use `tempfile` or the fixtures
# provided by pytest. Test with:
#       mkdir -p /tmp/test_multiproc;
#       export prometheus_multiproc_dir=/tmp/test_multiproc;
#       pytest -k test_multiprocess_reg;
#       rm -rf /tmp/test_multiproc;
#       unset prometheus_multiproc_dir


@pytest.mark.skipif(
    is_prometheus_multiproc_set() is False,
    reason="Environment variable must be set before starting Python process.",
)
def test_multiprocess_reg():
    app = create_app()
    Instrumentator(buckets=(1, 2, 3,)).instrument(app).expose(app)
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert response.status_code == 200
    assert b"Multiprocess" in response.content
    assert b"# HELP process_cpu_seconds_total" not in response.content
    assert b"http_request_duration_seconds" in response.content


@pytest.mark.skipif(is_prometheus_multiproc_set() is True, reason="Will never work.")
def test_multiprocess_reg_is_not(monkeypatch, tmp_path):
    monkeypatch.setenv("prometheus_multiproc_dir", str(tmp_path))

    app = create_app()
    Instrumentator(buckets=(1, 2, 3,)).instrument(app).expose(app)

    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert response.status_code == 200
    assert b"" == response.content


@pytest.mark.skipif(
    is_prometheus_multiproc_set() is True, reason="Just test handling of env detection."
)
def test_multiprocess_env_folder(monkeypatch, tmp_path):
    monkeypatch.setenv("prometheus_multiproc_dir", "DOES/NOT/EXIST")

    app = create_app()
    with pytest.raises(Exception):
        Instrumentator(buckets=(1, 2, 3,)).instrument(app).expose(app)
