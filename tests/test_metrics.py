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


def get_response(client: TestClient, path: str) -> Response:
    response = client.get(path)

    print(f"\nResponse  path='{path}' status='{response.status_code}':\n")
    for line in response.content.split(b"\n"):
        print(line.decode())

    return response


# ==============================================================================
# Test helpers / misc


def test_existence_of_attributes():
    info = metrics.Info(
        request=None,
        response=None,
        method=None,
        modified_duration=None,
        modified_status=None,
        modified_handler=None,
    )
    assert info.request is None
    assert info.response is None
    assert info.method is None
    assert info.modified_duration is None
    assert info.modified_status is None
    assert info.modified_handler is None


def test_build_label_attribute_names_all_false():
    label_names, info_attribute_names = metrics._build_label_attribute_names(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
    )
    assert label_names == []
    assert info_attribute_names == []


def test_build_label_attribute_names_all_true():
    label_names, info_attribute_names = metrics._build_label_attribute_names(
        should_include_handler=True,
        should_include_method=True,
        should_include_status=True,
    )
    assert label_names == ["handler", "method", "status"]
    assert info_attribute_names == [
        "modified_handler",
        "method",
        "modified_status",
    ]


def test_build_label_attribute_names_mixed():
    label_names, info_attribute_names = metrics._build_label_attribute_names(
        should_include_handler=True,
        should_include_method=False,
        should_include_status=True,
    )
    assert label_names == ["handler", "status"]
    assert info_attribute_names == ["modified_handler", "modified_status"]


# ==============================================================================
# Tests for metrics / metric function builders


# ------------------------------------------------------------------------------
# request_size


def test_request_size_all_labels():
    app = create_app()
    Instrumentator().add(metrics.request_size()).instrument(app)
    client = TestClient(app)

    client.get("/", data="some data")

    assert (
        REGISTRY.get_sample_value(
            "http_request_content_bytes_sum", {"handler": "/", "method": "GET", "status": "2xx"}
        )
        == 9
    )


def test_request_size_no_labels():
    app = create_app()
    Instrumentator().add(metrics.request_size(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
    )).instrument(app)
    client = TestClient(app)

    client.get("/", data="some data")

    assert (
        REGISTRY.get_sample_value(
            "http_request_content_bytes_sum", {}
        )
        == 9
    )


def test_request_size_no_cl():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(metrics.request_size()).instrument(
        app
    ).expose(app)
    client = TestClient(app)

    client.get("/")

    response = get_response(client, "/metrics")

    assert b"http_request_content_bytes" in response.content
    assert b"http_request_content_bytes_count{" not in response.content


# ------------------------------------------------------------------------------
# response_size


def test_response_size_all_labels():
    app = create_app()
    Instrumentator().add(metrics.response_size()).instrument(app).expose(app)
    client = TestClient(app)

    client.get("/")

    _ = get_response(client, "/metrics")

    assert (
        REGISTRY.get_sample_value(
            "http_response_content_bytes_sum", {"handler": "/", "method": "GET", "status": "2xx"}
        )
        == 14
    )


def test_response_size_no_labels():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(metrics.response_size(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
    )).instrument(app).expose(app)
    client = TestClient(app)

    client.get("/")

    _ = get_response(client, "/metrics")

    assert (
        REGISTRY.get_sample_value(
            "http_response_content_bytes_sum", {}
        )
        == 14
    )


# ------------------------------------------------------------------------------
# combined_size


def test_combined_size_all_labels():
    app = create_app()
    Instrumentator().add(metrics.combined_size()).instrument(app).expose(app)
    client = TestClient(app)

    client.get("/")

    _ = get_response(client, "/metrics")

    assert (
        REGISTRY.get_sample_value(
            "http_content_bytes_sum", {"handler": "/", "method": "GET", "status": "2xx"}
        )
        == 14
    )


def test_combined_size_all_labels_with_data():
    app = create_app()
    Instrumentator().add(metrics.combined_size()).instrument(app).expose(app)
    client = TestClient(app)

    client.get("/", data="fegfgeegeg")

    _ = get_response(client, "/metrics")

    assert (
        REGISTRY.get_sample_value(
            "http_content_bytes_sum", {"handler": "/", "method": "GET", "status": "2xx"}
        )
        == 24
    )


def test_combined_size_no_labels():
    app = create_app()
    Instrumentator().add(metrics.combined_size(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
    )).instrument(app)
    client = TestClient(app)

    client.get("/")

    assert (
        REGISTRY.get_sample_value(
            "http_content_bytes_sum", {}
        )
        == 14
    )


# ------------------------------------------------------------------------------
# http_content_length_bytes


def test_http_content_length_bytes_with_handler_and_data():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(
        metrics.combined_size()
    ).instrument(app).expose(app)
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
    Instrumentator(excluded_handlers=["/metrics"]).add(
        metrics.combined_size()
    ).instrument(app).expose(app)
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
        metrics.combined_size(should_drop_handler=True)
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
