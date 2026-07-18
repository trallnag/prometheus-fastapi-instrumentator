"""Tests for correct route resolution with FastAPI `root_path` focus."""

from fastapi import APIRouter, FastAPI, Request

from prometheus_fastapi_instrumentator.routing import get_route_name


def _scope(app: FastAPI, path: str, root_path: str = "") -> dict:
    return {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "root_path": root_path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "app": app,
    }


def test_routing_root_path_with_path_param():
    """Tests that path-parameter routes include the effective `root_path`."""

    app = FastAPI(root_path="/proxy")

    @app.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        return {"item_id": item_id}

    path = "/proxy/items/42"
    assert (
        get_route_name(Request(_scope(app, path, root_path="/proxy")))
        == "/proxy/items/{item_id}"
    )


def test_routing_root_path_with_slash_only():
    """Tests that the root route resolves with the effective `root_path`."""

    app = FastAPI(root_path="/proxy")

    @app.get("/")
    def index() -> dict:
        return {}

    path = "/proxy/"
    assert get_route_name(Request(_scope(app, path, root_path="/proxy"))) == "/proxy/"


def test_routing_root_path_with_include_router():
    """Tests that included-router routes resolve with the effective `root_path`."""

    app = FastAPI(root_path="/proxy")
    router = APIRouter(prefix="/api")

    @router.get("/health")
    def health() -> dict:
        return {"ok": True}

    @router.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        return {"item_id": item_id}

    app.include_router(router)

    health_path = "/proxy/api/health"
    assert (
        get_route_name(Request(_scope(app, health_path, root_path="/proxy")))
        == "/proxy/api/health"
    )

    item_path = "/proxy/api/items/7"
    assert (
        get_route_name(Request(_scope(app, item_path, root_path="/proxy")))
        == "/proxy/api/items/{item_id}"
    )


def test_routing_root_path_with_nested_include_router():
    """Tests that nested included-router routes resolve with the effective `root_path`."""

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

    ready_path = "/proxy/api/v1/ready"
    assert (
        get_route_name(Request(_scope(app, ready_path, root_path="/proxy")))
        == "/proxy/api/v1/ready"
    )

    user_path = "/proxy/api/v1/users/99"
    assert (
        get_route_name(Request(_scope(app, user_path, root_path="/proxy")))
        == "/proxy/api/v1/users/{user_id}"
    )


def test_routing_root_path_with_redirect_slash():
    """Tests that redirect-slash matching preserves the effective `root_path`."""

    app = FastAPI(root_path="/proxy")

    @app.get("/items/")
    def list_items() -> list:
        return []

    path = "/proxy/items"
    assert (
        get_route_name(Request(_scope(app, path, root_path="/proxy"))) == "/proxy/items"
    )


def test_routing_root_path_with_no_redirect_slash():
    """Tests that non-redirect-slash matching preserves the effective `root_path`."""

    app = FastAPI(root_path="/proxy", redirect_slashes=False)

    @app.get("/items/")
    def list_items() -> list:
        return []

    path = "/proxy/items/"
    assert (
        get_route_name(Request(_scope(app, path, root_path="/proxy"))) == "/proxy/items/"
    )


def test_routing_root_path_with_trailing_root_slash():
    """Tests that trailing-slash `root_path` values are normalized for path params."""

    app = FastAPI(root_path="/proxy/")

    @app.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        return {"item_id": item_id}

    path = "/proxy/items/42"
    assert (
        get_route_name(Request(_scope(app, path, root_path="/proxy")))
        == "/proxy/items/{item_id}"
    )


def test_routing_root_path_with_trailing_nested():
    """Tests that nested `include_router` route names use the normalized
    scope `root_path` when app `root_path` includes a trailing slash.
    """

    app = FastAPI(root_path="/proxy/")
    api_router = APIRouter(prefix="/api")
    v1_router = APIRouter(prefix="/v1")

    @v1_router.get("/users/{user_id}")
    def get_user(user_id: int) -> dict:
        return {"user_id": user_id}

    api_router.include_router(v1_router)
    app.include_router(api_router)

    path = "/proxy/api/v1/users/99"
    assert (
        get_route_name(Request(_scope(app, path, root_path="/proxy")))
        == "/proxy/api/v1/users/{user_id}"
    )
