from http import HTTPStatus

from fastapi import APIRouter, FastAPI
from prometheus_client import REGISTRY, generate_latest
from starlette.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator

from helpers import utils

def _build_app_with_included_router() -> FastAPI:
    """Build a small FastAPI app that uses ``app.include_router``.

    The structure mirrors real-world usage (cf. SyncQues-Backend which
    registers ~30 routers this way) and reliably triggers the
    ``_IncludedRouter`` code path on FastAPI >= 0.116.
    """

    app = FastAPI()

    @app.get("/health")
    def read_health() -> dict:
        return {"status": "ok"}

    items_router = APIRouter()

    @items_router.get("/")
    def list_items() -> dict:
        return {"items": []}

    @items_router.get("/{item_id}")
    def read_item(item_id: int) -> dict:
        return {"item_id": item_id}

    @items_router.post("/")
    def create_item() -> dict:
        return {"created": True}

    app.include_router(items_router, prefix="/api/v1/items")

    users_router = APIRouter()

    @users_router.get("/")
    def list_users() -> dict:
        return {"users": []}

    app.include_router(users_router, prefix="/api/v1/users")

    return app


def test_included_router_does_not_crash_request():
    """Requests through an included router must not raise AttributeError."""

    utils.reset_collectors()

    app = _build_app_with_included_router()
    Instrumentator().instrument(app).expose(app)

    client = TestClient(app, raise_server_exceptions=False)

    # Direct route on the app — must succeed.
    response = client.get("/health")
    assert response.status_code == 200, response.text

    # Routes on an included router — must succeed and not return 500.
    response = client.get("/api/v1/items/")
    assert response.status_code == 200, response.text
    assert response.json() == {"items": []}

    response = client.get("/api/v1/items/42")
    assert response.status_code == 200, response.text
    assert response.json() == {"item_id": 42}

    response = client.post("/api/v1/items/", json={})
    assert response.status_code == 200, response.text

    # Second included router — confirms handling is not single-router specific.
    response = client.get("/api/v1/users/")
    assert response.status_code == 200, response.text


def test_included_router_handler_label_includes_prefix():
    """Metric label must include the ``include_router`` prefix and the
    templated leaf path, e.g. ``/api/v1/items/{item_id}``.
    """

    utils.reset_collectors()

    app = _build_app_with_included_router()
    Instrumentator().instrument(app).expose(app)

    client = TestClient(app)

    # Hit each included route so the metric is recorded.
    client.get("/api/v1/items/")
    client.get("/api/v1/items/1")
    client.get("/api/v1/users/")

    metrics_output = generate_latest(REGISTRY).decode()

    # The handler label must contain the full path including the
    # ``include_router`` prefix and the templated segment.
    assert 'handler="/api/v1/items/"' in metrics_output
    assert 'handler="/api/v1/items/{item_id}"' in metrics_output
    assert 'handler="/api/v1/users/"' in metrics_output


def test_included_router_validation_error_does_not_500():
    """Invalid request against an included router must surface the
    framework's normal 422, not the instrumentator's 500.
    """

    utils.reset_collectors()

    app = _build_app_with_included_router()
    Instrumentator().instrument(app).expose(app)

    client = TestClient(app, raise_server_exceptions=False)

    # ``item_id`` is declared ``int``; a non-numeric value must yield 422.
    response = client.get("/api/v1/items/not-an-int")
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.text


def test_included_router_not_found_does_not_500():
    """A path under an included router prefix that does not match any
    route must surface 404, not the instrumentator's 500.
    """

    utils.reset_collectors()

    app = _build_app_with_included_router()
    Instrumentator().instrument(app).expose(app)

    client = TestClient(app, raise_server_exceptions=False)

    # ``/api/v1/items/foo/extra`` does not match any registered route.
    response = client.get("/api/v1/items/foo/extra")
    assert response.status_code == HTTPStatus.NOT_FOUND, response.text
