from fastapi import FastAPI
from prometheus_client import CollectorRegistry
from requests import Response as TestClientResponse
from starlette.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator

# ------------------------------------------------------------------------------
# Setup


def create_app() -> FastAPI:
    app = FastAPI()

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
    app1 = create_app()
    app2 = create_app()
    registry1 = CollectorRegistry(auto_describe=True)
    registry2 = CollectorRegistry(auto_describe=True)
    Instrumentator(registry=registry1).instrument(app1).expose(app1)
    Instrumentator(registry=registry2).instrument(app2).expose(app2)
    client1 = TestClient(app1)
    client2 = TestClient(app2)

    get_response(client1, "/")
    get_response(client2, "/")

    response1 = get_response(client1, "/metrics")
    response2 = get_response(client2, "/metrics")
    assert response1.status_code == 200
    assert b"http_request" in response1.content
    assert response2.status_code == 200
    assert b"http_request" in response2.content
