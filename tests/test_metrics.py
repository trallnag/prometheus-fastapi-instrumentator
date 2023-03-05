from typing import Any, Dict, Optional

import pytest
from fastapi import FastAPI, HTTPException
from prometheus_client import REGISTRY
from requests import Response as TestClientResponse
from starlette.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator, metrics

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

    @app.get("/runtime_error")
    def always_error():
        raise RuntimeError()

    return app


def get_response(client: TestClient, path: str) -> TestClientResponse:
    response = client.get(path)

    print(f"\nResponse  path='{path}' status='{response.status_code}':\n")
    for line in response.content.split(b"\n"):
        print(line.decode())

    return response


# ------------------------------------------------------------------------------
# Test helpers / misc


def test_is_duplicated_time_series():
    error = ValueError("xx Duplicated timeseries in CollectorRegistry: xx")
    assert metrics._is_duplicated_time_series(error)

    error = ValueError("xx Duplicated time series in CollectorRegistry: xx")
    assert metrics._is_duplicated_time_series(error)

    error = ValueError("xx xx")
    assert not metrics._is_duplicated_time_series(error)


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


def test_api_throwing_error():
    app = create_app()
    client = TestClient(app)
    with pytest.raises(RuntimeError):
        get_response(client, "/runtime_error")


# ------------------------------------------------------------------------------
# request_size


def test_request_size_all_labels():
    app = create_app()
    Instrumentator().add(metrics.request_size()).instrument(app)
    client = TestClient(app)

    client.request(method="GET", url="/", content="some data")

    assert (
        REGISTRY.get_sample_value(
            "http_request_size_bytes_sum",
            {"handler": "/", "method": "GET", "status": "2xx"},
        )
        == 9
    )


def test_request_size_no_labels():
    app = create_app()
    Instrumentator().add(
        metrics.request_size(
            should_include_handler=False,
            should_include_method=False,
            should_include_status=False,
        )
    ).instrument(app)
    client = TestClient(app)

    client.request(method="GET", url="/", content="some data")

    assert REGISTRY.get_sample_value("http_request_size_bytes_sum", {}) == 9


def test_namespace_subsystem():
    app = create_app()
    Instrumentator().add(
        metrics.request_size(
            should_include_handler=False,
            should_include_method=False,
            should_include_status=False,
            metric_namespace="namespace",
            metric_subsystem="subsystem",
        )
    ).instrument(app).expose(app)
    client = TestClient(app)

    response = get_response(client, "/metrics")

    assert b" http_request_size_bytes" not in response.content
    assert b" namespace_subsystem_http_request_size_bytes" in response.content


def test_request_size_no_cl():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(metrics.request_size()).instrument(
        app
    ).expose(app)
    client = TestClient(app)

    client.get("/")

    response = get_response(client, "/metrics")

    assert b"http_request_size_bytes" in response.content
    assert b"http_request_size_bytes_count{" in response.content


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
            "http_response_size_bytes_sum",
            {"handler": "/", "method": "GET", "status": "2xx"},
        )
        == 14
    )


def test_response_size_no_labels():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(
        metrics.response_size(
            should_include_handler=False,
            should_include_method=False,
            should_include_status=False,
        )
    ).instrument(app).expose(app)
    client = TestClient(app)

    client.get("/")

    _ = get_response(client, "/metrics")

    assert REGISTRY.get_sample_value("http_response_size_bytes_sum", {}) == 14


def test_response_size_with_runtime_error():
    app = create_app()
    Instrumentator().add(metrics.response_size()).instrument(app).expose(app)
    client = TestClient(app)

    try:
        get_response(client, "/runtime_error")
    except RuntimeError:
        pass

    response = get_response(client, "/metrics")

    assert (
        b'http_response_size_bytes_count{handler="/runtime_error",method="GET",status="5xx"} 1.0'
        in response.content
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
            "http_combined_size_bytes_sum",
            {"handler": "/", "method": "GET", "status": "2xx"},
        )
        == 14
    )


def test_combined_size_all_labels_with_data():
    app = create_app()
    Instrumentator().add(metrics.combined_size()).instrument(app).expose(app)
    client = TestClient(app)

    client.request(method="GET", url="/", content="fegfgeegeg")

    _ = get_response(client, "/metrics")

    assert (
        REGISTRY.get_sample_value(
            "http_combined_size_bytes_sum",
            {"handler": "/", "method": "GET", "status": "2xx"},
        )
        == 24
    )


def test_combined_size_no_labels():
    app = create_app()
    Instrumentator().add(
        metrics.combined_size(
            should_include_handler=False,
            should_include_method=False,
            should_include_status=False,
        )
    ).instrument(app)
    client = TestClient(app)

    client.get("/")

    assert REGISTRY.get_sample_value("http_combined_size_bytes_sum", {}) == 14


def test_combined_size_with_runtime_error():
    app = create_app()
    Instrumentator().add(metrics.combined_size()).instrument(app).expose(app)
    client = TestClient(app)

    try:
        get_response(client, "/runtime_error")
    except RuntimeError:
        pass

    response = get_response(client, "/metrics")

    assert (
        b'http_combined_size_bytes_count{handler="/runtime_error",method="GET",status="5xx"} 1.0'
        in response.content
    )


# ------------------------------------------------------------------------------
# latency


def test_latency_all_labels():
    app = create_app()
    Instrumentator().add(metrics.latency()).instrument(app).expose(app)
    client = TestClient(app)

    client.get("/")

    _ = get_response(client, "/metrics")

    assert (
        REGISTRY.get_sample_value(
            "http_request_duration_seconds_sum",
            {"handler": "/", "method": "GET", "status": "2xx"},
        )
        > 0
    )


def test_latency_no_labels():
    app = create_app()
    Instrumentator().add(
        metrics.latency(
            should_include_handler=False,
            should_include_method=False,
            should_include_status=False,
        )
    ).instrument(app).expose(app)
    client = TestClient(app)

    client.get("/")

    _ = get_response(client, "/metrics")

    assert (
        REGISTRY.get_sample_value(
            "http_request_duration_seconds_sum",
            {},
        )
        > 0
    )


def test_latency_with_bucket_no_inf():
    app = create_app()
    Instrumentator().add(
        metrics.latency(
            should_include_handler=False,
            should_include_method=False,
            should_include_status=False,
            buckets=(1, 2, 3),
        )
    ).instrument(app).expose(app)
    client = TestClient(app)

    client.get("/")

    _ = get_response(client, "/metrics")

    assert (
        REGISTRY.get_sample_value(
            "http_request_duration_seconds_sum",
            {},
        )
        > 0
    )


# ------------------------------------------------------------------------------
# default


def test_default():
    app = create_app()
    Instrumentator().add(metrics.default()).instrument(app).expose(app)
    client = TestClient(app)

    client.request(method="GET", url="/", content="fefeef")
    client.request(method="GET", url="/")

    _ = get_response(client, "/metrics")

    assert (
        REGISTRY.get_sample_value(
            "http_requests_total",
            {"handler": "/", "method": "GET", "status": "2xx"},
        )
        > 0
    )
    assert (
        REGISTRY.get_sample_value(
            "http_request_size_bytes_sum",
            {"handler": "/"},
        )
        > 0
    )
    assert (
        REGISTRY.get_sample_value(
            "http_response_size_bytes_sum",
            {"handler": "/"},
        )
        > 0
    )
    assert (
        REGISTRY.get_sample_value(
            "http_request_duration_highr_seconds_sum",
            {},
        )
        > 0
    )
    assert (
        REGISTRY.get_sample_value(
            "http_request_duration_seconds_sum",
            {"handler": "/"},
        )
        > 0
    )


def test_default_should_only_respect_2xx_for_highr():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(
        metrics.default(should_only_respect_2xx_for_highr=True)
    ).instrument(app).expose(app)
    client = TestClient(app)

    client.request(method="GET", url="/efefewffe", content="fefeef")
    client.request(method="GET", url="/ffe04904nfiuo-ni")

    response = get_response(client, "/metrics")

    assert b"http_request_duration_highr_seconds_count 0.0" in response.content


def test_default_should_not_only_respect_2xx_for_highr():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).add(
        metrics.default(should_only_respect_2xx_for_highr=False)
    ).instrument(app).expose(app)
    client = TestClient(app)

    client.get("/efefewffe")
    client.get("/ffe04904nfiuo-ni")

    response = get_response(client, "/metrics")

    assert b"http_request_duration_highr_seconds_count 0.0" not in response.content
    assert b"http_request_duration_highr_seconds_count 2.0" in response.content


def test_default_with_runtime_error():
    app = create_app()
    Instrumentator().instrument(app).expose(app)
    client = TestClient(app)

    try:
        get_response(client, "/runtime_error")
    except RuntimeError:
        pass

    response = get_response(client, "/metrics")

    assert (
        b'http_request_size_bytes_count{handler="/runtime_error"} 1.0' in response.content
    )


# ------------------------------------------------------------------------------
# requests


def test_requests_all_labels():
    app = create_app()
    Instrumentator().add(metrics.requests()).instrument(app).expose(app)
    client = TestClient(app)

    client.get("/")

    _ = get_response(client, "/metrics")

    assert (
        REGISTRY.get_sample_value(
            "http_requests_total",
            {"handler": "/", "method": "GET", "status": "2xx"},
        )
        == 1
    )


def test_requests_no_labels():
    app = create_app()
    Instrumentator().add(
        metrics.requests(
            should_include_handler=False,
            should_include_method=False,
            should_include_status=False,
        )
    ).instrument(app).expose(app)
    client = TestClient(app)

    client.get("/")

    _ = get_response(client, "/metrics")

    assert (
        REGISTRY.get_sample_value(
            "http_requests_total",
            {},
        )
        == 2
    )


def test_request_custom_namespace():
    app = create_app()
    Instrumentator(excluded_handlers=["/metrics"]).instrument(
        app, metric_namespace="namespace", metric_subsystem="example"
    ).expose(app)
    client = TestClient(app)

    client.get("/")

    response = get_response(client, "/metrics")

    assert (
        b"namespace_example_http_request_duration_highr_seconds_bucket"
        in response.content
    )
