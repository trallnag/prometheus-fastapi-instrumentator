from fastapi import FastAPI
from prometheus_client import CollectorRegistry, Counter
from starlette.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator, metrics


def test_multiple_apps_custom_registry():
    """
    Tests instrumentation of multiple apps in combination with  middlewares
    where each app gets it's own registry. In addition it tests that custom
    metrics are not shared between app's metrics endpoints.
    """

    app1 = FastAPI()
    app2 = FastAPI()

    @app1.get("/dummy")
    def read_dummy_app1():
        return "Hello from app1"

    @app2.get("/dummy")
    def read_dummy_app2():
        return "Hello from app2"

    registry1 = CollectorRegistry(auto_describe=True)
    registry2 = CollectorRegistry(auto_describe=True)

    Instrumentator(registry=registry1).instrument(app1).expose(app1)
    Instrumentator(registry=registry2).instrument(app2).expose(app2)

    Counter("test_app1_only", "In app1 metrics only.", registry=registry1).inc()

    # Add middleware after adding the instrumentator, this triggers another
    # app.build_middleware_stack(), which creates the middleware again, but it
    # will use the same Prometheus registry again, which could try to create the
    # same metrics again causing duplication errors.
    @app1.middleware("http")
    @app2.middleware("http")
    async def dummy_middleware(request, call_next):
        response = await call_next(request)
        return response

    client1 = TestClient(app1)
    client2 = TestClient(app2)

    client1.get("/dummy")
    client2.get("/dummy")

    metrics1 = client1.get("/metrics").content.decode()
    metrics2 = client2.get("/metrics").content.decode()

    print("app1 GET /metrics\n" + metrics1)
    print("app2 GET /metrics\n" + metrics2)

    want = 'http_requests_total{handler="/dummy",method="GET",status="2xx"} 1.0\n'
    assert want in metrics1
    assert want in metrics2

    want = "test_app1_only_total 1.0\n"
    assert want in metrics1
    assert want not in metrics2


def test_multiple_apps_expose_defaults():
    """Tests instrumentation of multiple apps in combination with middlewares."""

    app1 = FastAPI()
    app2 = FastAPI()

    @app1.get("/dummy")
    def read_dummy_app1():
        return "Hello from app1"

    @app2.get("/dummy")
    def read_dummy_app2():
        return "Hello from app2"

    Instrumentator().instrument(app1).expose(app1)
    Instrumentator().instrument(app2).expose(app2)

    # Add middleware after adding the instrumentator, this triggers another
    # app.build_middleware_stack(), which creates the middleware again, but it
    # will use the same Prometheus registry again, which could try to create the
    # same metrics again causing duplication errors.
    @app1.middleware("http")
    @app2.middleware("http")
    async def dummy_middleware(request, call_next):
        response = await call_next(request)
        return response

    client1 = TestClient(app1)
    client2 = TestClient(app2)

    client1.get("/dummy")
    client2.get("/dummy")

    metrics1 = client1.get("/metrics").content.decode()
    metrics2 = client2.get("/metrics").content.decode()

    print("app1 GET /metrics\n" + metrics1)
    print("app2 GET /metrics\n" + metrics2)

    want = 'http_requests_total{handler="/dummy",method="GET",status="2xx"} 1.0\n'
    assert want in metrics1
    assert want in metrics2


def test_multiple_apps_expose_full():
    """Tests instrumentation of multiple apps in combination with middlewares."""

    app1 = FastAPI()
    app2 = FastAPI()

    @app1.get("/dummy")
    def read_dummy_app1():
        return "Hello from app1"

    @app2.get("/dummy")
    def read_dummy_app2():
        return "Hello from app2"

    Instrumentator().add(
        metrics.request_size(),
        metrics.requests(),
        metrics.combined_size(),
        metrics.response_size(),
        metrics.latency(),
        metrics.default(),
    ).instrument(app1).expose(app1)

    Instrumentator().add(
        metrics.request_size(),
        metrics.requests(),
        metrics.combined_size(),
        metrics.response_size(),
        metrics.latency(),
        metrics.default(),
    ).instrument(app2).expose(app2)

    # Add middleware after adding the instrumentator, this triggers another
    # app.build_middleware_stack(), which creates the middleware again, but it
    # will use the same Prometheus registry again, which could try to create the
    # same metrics again causing duplication errors.
    @app1.middleware("http")
    @app2.middleware("http")
    async def dummy_middleware(request, call_next):
        response = await call_next(request)
        return response

    client1 = TestClient(app1)
    client2 = TestClient(app2)

    client1.get("/dummy")
    client2.get("/dummy")

    metrics1 = client1.get("/metrics").content.decode()
    metrics2 = client2.get("/metrics").content.decode()

    print("app1 GET /metrics\n" + metrics1)
    print("app2 GET /metrics\n" + metrics2)

    want = 'http_requests_total{handler="/dummy",method="GET",status="2xx"} 1.0\n'
    assert want in metrics1
    assert want in metrics2
