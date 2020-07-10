from typing import Optional
from fastapi import FastAPI, HTTPException
from starlette.testclient import TestClient
from starlette.responses import Response
from prometheus_client import REGISTRY
from prometheus_fastapi_exporter import PrometheusFastApiExporter

# ==============================================================================
# Setup


def create_app() -> FastAPI:
    app = FastAPI()

    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        REGISTRY.unregister(collector)

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

    return app


def get_response(client: TestClient, path: str) -> Response:
    response = client.get(path)

    print(f"\nResponse  path='{path}' status='{response.status_code}':\n")
    for line in response.content.split(b"\n"):
        print(line.decode())

    return response


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


def test_metrics_endpoint_availability():
    app = create_app()
    PrometheusFastApiExporter(app).instrument()
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert response.status_code == 200
    assert b"http_request_duration_seconds_bucket" in response.content


# ------------------------------------------------------------------------------
# Test metric name


def test_default_metric_name():
    app = create_app()
    PrometheusFastApiExporter(app).instrument()
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert b"http_request_duration_seconds" in response.content


def test_custom_metric_name():
    app = create_app()
    PrometheusFastApiExporter(app=app, metric_name="fastapi_latency").instrument()
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert b"fastapi_latency" in response.content
    assert b"http_request_duration_seconds" not in response.content


# ------------------------------------------------------------------------------
# Test grouping of status codes.


def test_grouped_status_codes():
    app = create_app()
    PrometheusFastApiExporter(app=app).instrument()
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert b'status="2xx"' in response.content
    assert b'status="200"' not in response.content


def test_ungrouped_status_codes():
    app = create_app()
    PrometheusFastApiExporter(app=app, should_group_status_codes=False).instrument()
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert b'status="2xx"' not in response.content
    assert b'status="200"' in response.content


# ------------------------------------------------------------------------------
# Test handling of templates / untemplated.


def test_ignore_untemplated():
    app = create_app()
    PrometheusFastApiExporter(app=app, should_ignore_untemplated=True).instrument()
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/items/678?q=43243")
    get_response(client, "/does_not_exist")

    response = get_response(client, "/metrics")
    assert b'handler="/does_not_exist"' not in response.content
    assert b'handler="none"' not in response.content


def test_dont_ignore_untemplated_ungrouped():
    app = create_app()
    PrometheusFastApiExporter(
        app=app, should_ignore_untemplated=False, should_group_untemplated=False,
    ).instrument()
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/items/678?q=43243")
    get_response(client, "/does_not_exist")

    response = get_response(client, "/metrics")
    assert b'handler="/does_not_exist"' in response.content
    assert b'handler="none"' not in response.content


def test_grouping_untemplated():
    app = create_app()
    PrometheusFastApiExporter(app=app).instrument()
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/items/678?q=43243")
    get_response(client, "/does_not_exist")

    response = get_response(client, "/metrics")
    assert b'handler="/does_not_exist"' not in response.content
    assert b'handler="none"' in response.content


def test_excluding_handlers():
    app = create_app()
    PrometheusFastApiExporter(app=app, excluded_handlers=["fefefwefwe"]).instrument()
    client = TestClient(app)

    get_response(client, "/")
    get_response(client, "/metrics")
    get_response(client, "/fefefwefwe")

    response = get_response(client, "/metrics")
    assert b'handler="/metrics"' in response.content
    assert b'handler="/fefefwefwe"' not in response.content
    assert b'handler="none"' not in response.content


# ------------------------------------------------------------------------------
# Test label names.


def test_default_label_names():
    app = create_app()
    PrometheusFastApiExporter(app=app).instrument()
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert b"method=" in response.content
    assert b"handler=" in response.content
    assert b"status=" in response.content


def test_custom_label_names():
    app = create_app()
    PrometheusFastApiExporter(app=app, label_names=("a", "b", "c",)).instrument()
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert b"a=" in response.content
    assert b"b=" in response.content
    assert b"c=" in response.content
    assert b"method=" not in response.content
    assert b"handler=" not in response.content
    assert b"status=" not in response.content


# ------------------------------------------------------------------------------
# Test ignore method.


def test_ignore_method():
    app = create_app()
    PrometheusFastApiExporter(app=app).instrument()
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert b'method="ignored"' in response.content
    assert b'method="GET"' not in response.content


def test_dont_ignore_method():
    app = create_app()
    PrometheusFastApiExporter(app=app, should_ignore_method=False).instrument()
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert b'method="ignored"' not in response.content
    assert b'method="GET"' in response.content


# ------------------------------------------------------------------------------
# Test None excluded handlers.


def test_excluded_handlers_none():
    app = create_app()
    exporter = PrometheusFastApiExporter(app=app, excluded_handlers=None)

    assert len(exporter.excluded_handlers) == 0
    assert isinstance(exporter.excluded_handlers, list)
    assert exporter.excluded_handlers is not None


# ------------------------------------------------------------------------------
# Test bucket without infinity.


def test_bucket_without_inf():
    app = create_app()
    PrometheusFastApiExporter(app=app, buckets=(1, 2, 3,)).instrument()
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert b"http_request_duration_seconds" in response.content


# ------------------------------------------------------------------------------
# Test with multiprocess reg.


def test_multiprocess_reg(monkeypatch, tmp_path):
    monkeypatch.setenv("prometheus_multiproc_dir", str(tmp_path))

    app = create_app()
    PrometheusFastApiExporter(app=app, buckets=(1, 2, 3,)).instrument()
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert b"http_request_duration_seconds" in response.content
    assert b"process" not in response.content
