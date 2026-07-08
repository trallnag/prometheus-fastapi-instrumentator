"""Regression tests for FastAPI `root_path` handler-label resolution.

When a FastAPI app is deployed behind a reverse proxy, the proxy typically
strips a path prefix before forwarding to the application. FastAPI exposes
this prefix via `root_path`. The ASGI server re-attaches the prefix to
`scope["path"]`, so the full URL visible to the client is correct, but
the app's routes are registered *without* the prefix.

Prior to the fix for issue #387, the route-resolution helper in
`routing.py` tried to match `scope["path"]` (which still contained the
prefix) against routes that don't carry that prefix. No route matched, the
handler fell back to `None`, and the middleware recorded the metric with
`handler="none"` instead of the templated path.
"""

from fastapi import APIRouter, FastAPI
from helpers import utils
from starlette.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator


def _reset() -> None:
    utils.reset_collectors()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _metrics(client: TestClient) -> str:
    return client.get("/metrics").content.decode()


def test_root_path_plain_route_handler_label():
    """Plain route on an app configured with `root_path` must resolve the
    templated handler label and include the prefix."""

    _reset()

    app = FastAPI(root_path="/proxy")

    @app.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        return {"item_id": item_id}

    Instrumentator().instrument(app).expose(app)
    client = TestClient(app, base_url="http://testserver/proxy")

    response = client.get("/items/42")
    assert response.status_code == 200, response.text

    payload = _metrics(client)
    assert (
        'http_requests_total{handler="/proxy/items/{item_id}",method="GET",status="2xx"} 1.0\n'
        in payload
    ), payload


def test_root_path_plain_root_route_handler_label():
    """Root path `/` on an app with `root_path` must resolve correctly."""

    _reset()

    app = FastAPI(root_path="/proxy")

    @app.get("/")
    def index() -> dict:
        return {}

    Instrumentator().instrument(app).expose(app)
    client = TestClient(app, base_url="http://testserver/proxy")

    response = client.get("/")
    assert response.status_code == 200, response.text

    payload = _metrics(client)
    assert (
        'http_requests_total{handler="/proxy/",method="GET",status="2xx"} 1.0\n'
        in payload
    ), payload


def test_root_path_include_router_handler_label():
    """A route behind a single `include_router` must emit the prefixed
    templated handler when `root_path` is set."""

    _reset()

    app = FastAPI(root_path="/proxy")
    router = APIRouter(prefix="/api")

    @router.get("/health")
    def health() -> dict:
        return {"ok": True}

    @router.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        return {"item_id": item_id}

    app.include_router(router)
    Instrumentator().instrument(app).expose(app)
    client = TestClient(app, base_url="http://testserver/proxy")

    assert client.get("/api/health").status_code == 200
    assert client.get("/api/items/7").status_code == 200

    payload = _metrics(client)
    assert (
        'http_requests_total{handler="/proxy/api/health",method="GET",status="2xx"} 1.0\n'
        in payload
    ), payload
    assert (
        'http_requests_total{handler="/proxy/api/items/{item_id}",method="GET",status="2xx"} 1.0\n'
        in payload
    ), payload


def test_root_path_nested_include_router_handler_label():
    """Nested `include_router` chains must still resolve handler labels when
    `root_path` is configured — the core regression from issue #387."""

    _reset()

    app = FastAPI(root_path="/proxy")
    api_router = APIRouter(prefix="/api")
    v1_router = APIRouter(prefix="/v1")

    @v1_router.get("/ready")
    def ready() -> dict:
        return {"ok": True}

    @v1_router.get("/users/{user_id}")
    def get_user(user_id: int) -> dict:
        return {"user_id": user_id}

    api_router.include_router(v1_router)
    app.include_router(api_router)
    Instrumentator().instrument(app).expose(app)
    client = TestClient(app, base_url="http://testserver/proxy")

    assert client.get("/api/v1/ready").status_code == 200
    assert client.get("/api/v1/users/99").status_code == 200

    payload = _metrics(client)
    assert (
        'http_requests_total{handler="/proxy/api/v1/ready",method="GET",status="2xx"} 1.0\n'
        in payload
    ), payload
    assert (
        'http_requests_total{handler="/proxy/api/v1/users/{user_id}",method="GET",status="2xx"} 1.0\n'
        in payload
    ), payload


def test_no_root_path_nested_include_router_handler_label():
    """Without `root_path` the handler label must not carry any prefix —
    guards against inadvertent changes to the baseline behaviour."""

    _reset()

    app = FastAPI()
    api_router = APIRouter(prefix="/api")
    v1_router = APIRouter(prefix="/v1")

    @v1_router.get("/ready")
    def ready() -> dict:
        return {"ok": True}

    api_router.include_router(v1_router)
    app.include_router(api_router)
    Instrumentator().instrument(app).expose(app)
    client = TestClient(app)

    assert client.get("/api/v1/ready").status_code == 200

    payload = _metrics(client)
    assert (
        'http_requests_total{handler="/api/v1/ready",method="GET",status="2xx"} 1.0\n'
        in payload
    ), payload


def test_root_path_trailing_slash_redirect_handler_label():
    """When `redirect_slashes=True` (the default) a request that would be
    redirected by adding/removing a trailing slash must still resolve with
    the prefixed templated handler."""

    _reset()

    app = FastAPI(root_path="/proxy")

    @app.get("/items/")
    def list_items() -> list:
        return []

    Instrumentator().instrument(app).expose(app)
    client = TestClient(app, base_url="http://testserver/proxy")

    response = client.get("/items", follow_redirects=True)
    assert response.status_code == 200, response.text

    payload = _metrics(client)
    assert "/proxy/items/" in payload, payload
