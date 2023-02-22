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


def test_expose_defaults_custom_registry():
    app1 = create_app()
    app2 = create_app()
    registry1 = CollectorRegistry(auto_describe=True)
    registry2 = CollectorRegistry(auto_describe=True)
    Instrumentator(registry=registry1).instrument(app1).expose(app1)
    Instrumentator(registry=registry2).instrument(app2).expose(app2)

    # Add middlewares after adding the instrumentator, this triggers another
    # app.build_middleware_stack(), which creates the middleware again, but it will use
    # the same Prometheus registry again, which could try to create the same metrics
    # again causing duplication errors
    @app1.middleware("http")
    @app2.middleware("http")
    async def no_op_middleware(request, call_next):
        response = await call_next(request)
        return response

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


def test_expose_defaults():
    app1 = create_app()
    app2 = create_app()
    Instrumentator().instrument(app1).expose(app1)
    Instrumentator().instrument(app2).expose(app2)

    # Add middlewares after adding the instrumentator, this triggers another
    # app.build_middleware_stack(), which creates the middleware again, but it will use
    # the same Prometheus registry again, which could try to create the same metrics
    # again causing duplication errors
    @app1.middleware("http")
    @app2.middleware("http")
    async def no_op_middleware(request, call_next):
        response = await call_next(request)
        return response

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
