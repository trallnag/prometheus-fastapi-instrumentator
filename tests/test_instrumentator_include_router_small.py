from fastapi import APIRouter, FastAPI
from starlette.testclient import TestClient

from helpers import utils
from prometheus_fastapi_instrumentator import Instrumentator


def test_include_router_simple_path_is_instrumented():
    """Tests for FastAPI _IncludedRouter wrappers."""

    utils.reset_collectors()

    app = FastAPI()
    router = APIRouter(prefix="/api")

    @router.get("/health")
    def health():
        return {"ok": True}

    app.include_router(router)

    Instrumentator().instrument(app).expose(app)

    client = TestClient(app)

    response = client.get("/api/health")
    assert response.status_code == 200

    metrics_response = client.get("/metrics")
    metrics_payload = metrics_response.content.decode()

    assert (
        'http_requests_total{handler="/api/health",method="GET",status="2xx"} 1.0\n'
        in metrics_payload
    )


def test_nested_include_router_path_is_instrumented():
    """Regression test for nested include_router() registrations."""

    utils.reset_collectors()

    app = FastAPI()
    api_router = APIRouter(prefix="/api")
    v1_router = APIRouter(prefix="/v1")

    @v1_router.get("/ready")
    def ready():
        return {"ok": True}

    api_router.include_router(v1_router)
    app.include_router(api_router)

    Instrumentator().instrument(app).expose(app)

    client = TestClient(app)

    response = client.get("/api/v1/ready")
    assert response.status_code == 200

    metrics_response = client.get("/metrics")
    metrics_payload = metrics_response.content.decode()

    assert (
        'http_requests_total{handler="/api/v1/ready",method="GET",status="2xx"} 1.0\n'
        in metrics_payload
    )
