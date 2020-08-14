import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
from starlette.responses import Response
from starlette.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator, metrics

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
    from prometheus_client import gc_collector, platform_collector, process_collector

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

    @app.post("/items")
    def create_item(item: Dict[Any, Any]):
        return None

    return app


def expose_metrics(app: FastAPI) -> None:
    if "prometheus_multiproc_dir" in os.environ:
        pmd = os.environ["prometheus_multiproc_dir"]
        print(f"Env var prometheus_multiproc_dir='{pmd}' detected.")
        if os.path.isdir(pmd):
            print(f"Env var prometheus_multiproc_dir='{pmd}' is a dir.")
            from prometheus_client import CollectorRegistry, multiprocess

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


# ------------------------------------------------------------------------------
# http_request_content_length_bytes


def test_http_request_content_length_bytes_with_handler():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(metrics.http_request_content_length_bytes()).instrument(
        app
    ).expose(app)
    client = TestClient(app)

    client.get("/", data="some data")

    response = get_response(client, "/metrics")

    assert b"http_request_content_bytes" in response.content
    assert b"http_request_content_bytes_count{" in response.content


def test_http_request_content_length_bytes_without_handler():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(
        metrics.http_request_content_length_bytes(should_drop_handler=True)
    ).instrument(app).expose(app)
    client = TestClient(app)

    client.get("/", data="some data")

    _ = get_response(client, "/metrics")

    assert (
        REGISTRY.get_sample_value(
            "http_request_content_bytes_sum", {"method": "GET", "status": "2xx"}
        )
        == 9
    )


def test_http_request_content_length_bytes_no_cl():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(metrics.http_request_content_length_bytes()).instrument(
        app
    ).expose(app)
    client = TestClient(app)

    client.get("/")

    response = get_response(client, "/metrics")

    assert b"http_request_content_bytes" in response.content
    assert b"http_request_content_bytes_count{" not in response.content


# ------------------------------------------------------------------------------
# http_response_content_length_bytes


def test_http_response_content_length_bytes_with_handler():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(metrics.http_response_content_length_bytes()).instrument(
        app
    ).expose(app)
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/")
    get_response(client, "/")

    response = get_response(client, "/metrics")

    assert b"http_response_content_bytes_count{" in response.content
    assert (
        REGISTRY.get_sample_value(
            "http_response_content_bytes_sum",
            {"handler": "/", "method": "GET", "status": "2xx"},
        )
        == 42
    )
    assert (
        REGISTRY.get_sample_value(
            "http_response_content_bytes_count",
            {"handler": "/", "method": "GET", "status": "2xx"},
        )
        == 3
    )


def test_http_response_content_length_bytes_without_handler():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(
        metrics.http_response_content_length_bytes(should_drop_handler=True)
    ).instrument(app).expose(app)
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/")
    get_response(client, "/")
    get_response(client, "/ignore")

    response = get_response(client, "/metrics")

    assert b"http_response_content_bytes_count{" in response.content
    assert (
        REGISTRY.get_sample_value(
            "http_response_content_bytes_sum", {"method": "GET", "status": "2xx"}
        )
        == 61
    )
    assert (
        REGISTRY.get_sample_value(
            "http_response_content_bytes_count", {"method": "GET", "status": "2xx"}
        )
        == 4
    )


# ------------------------------------------------------------------------------
# http_content_length_bytes


def test_http_content_length_bytes_with_handler_and_data():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(metrics.http_content_length_bytes()).instrument(app).expose(app)
    client = TestClient(app)

    client.get("/", data="some data")
    client.get("/", data="some data")
    client.get("/", data="some data")

    _ = get_response(client, "/metrics")

    assert (
        REGISTRY.get_sample_value(
            "http_content_length_bytes_sum",
            {"handler": "/", "method": "GET", "status": "2xx"},
        )
        == 69
    )


def test_http_content_length_bytes_with_handler_no_data():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(metrics.http_content_length_bytes()).instrument(app).expose(app)
    client = TestClient(app)

    client.get("/")
    client.get("/")
    client.get("/")

    _ = get_response(client, "/metrics")

    assert (
        REGISTRY.get_sample_value(
            "http_content_length_bytes_sum",
            {"handler": "/", "method": "GET", "status": "2xx"},
        )
        == 42
    )


def test_http_content_length_bytes_without_handler():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(
        metrics.http_content_length_bytes(should_drop_handler=True)
    ).instrument(app).expose(app)
    client = TestClient(app)

    client.get("/", data="some data")

    _ = get_response(client, "/metrics")

    assert (
        REGISTRY.get_sample_value(
            "http_content_length_bytes_sum", {"method": "GET", "status": "2xx"}
        )
        == 23
    )
