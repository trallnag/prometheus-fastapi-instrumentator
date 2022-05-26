from fastapi import FastAPI
from prometheus_client import REGISTRY
from requests import Response as TestClientResponse
from starlette.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator

# ------------------------------------------------------------------------------
# Setup


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

    return app


def get_response(client: TestClient, path: str) -> TestClientResponse:
    response = client.get(path)

    print(f"\nResponse  path='{path}' status='{response.status_code}':\n")
    for line in response.content.split(b"\n"):
        print(line.decode())

    return response


# ------------------------------------------------------------------------------
# Tests


def test_expose_defaults():
    app = create_app()
    Instrumentator().instrument(app).expose(app)
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert response.status_code == 200
    assert b"http_request" in response.content


def test_expose_custom_path():
    app = create_app()
    Instrumentator().instrument(app).expose(app, endpoint="/custom_metrics")
    client = TestClient(app)

    get_response(client, "/")

    response = get_response(client, "/metrics")
    assert response.status_code == 404
    assert b"http_request" not in response.content

    response = get_response(client, "/custom_metrics")
    assert response.status_code == 200
    assert b"http_request" in response.content
