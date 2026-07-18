"""Tests for route resolution with FastAPI `root_path`."""

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


def _assert_route_names(
    app: FastAPI,
    called_path: str,
    excluded_route_name: str,
    included_route_name: str,
    root_path: str = "/proxy",
) -> None:
    request = Request(_scope(app, called_path, root_path=root_path))

    assert get_route_name(request, should_include_root_path=False) == excluded_route_name
    assert get_route_name(request, should_include_root_path=True) == included_route_name


def test_routing_root_path_with_path_param():
    """Tests that path-parameter routes resolve with and without `root_path`."""

    app = FastAPI(root_path="/proxy")

    @app.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        return {"item_id": item_id}

    _assert_route_names(
        app=app,
        called_path="/proxy/items/42",
        excluded_route_name="/items/{item_id}",
        included_route_name="/proxy/items/{item_id}",
    )


def test_routing_root_path_with_slash_only():
    """Tests that the root route resolves with and without `root_path`."""

    app = FastAPI(root_path="/proxy")

    @app.get("/")
    def index() -> dict:
        return {}

    _assert_route_names(
        app=app,
        called_path="/proxy/",
        excluded_route_name="/",
        included_route_name="/proxy/",
    )


def test_routing_root_path_with_include_router():
    """Tests that included-router routes resolve with and without `root_path`."""

    app = FastAPI(root_path="/proxy")
    router = APIRouter(prefix="/api")

    @router.get("/health")
    def health() -> dict:
        return {"ok": True}

    @router.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        return {"item_id": item_id}

    app.include_router(router)

    _assert_route_names(
        app=app,
        called_path="/proxy/api/health",
        excluded_route_name="/api/health",
        included_route_name="/proxy/api/health",
    )

    _assert_route_names(
        app=app,
        called_path="/proxy/api/items/7",
        excluded_route_name="/api/items/{item_id}",
        included_route_name="/proxy/api/items/{item_id}",
    )


def test_routing_root_path_with_nested_include_router():
    """Tests that nested included-router routes resolve with and without `root_path`."""

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

    _assert_route_names(
        app=app,
        called_path="/proxy/api/v1/ready",
        excluded_route_name="/api/v1/ready",
        included_route_name="/proxy/api/v1/ready",
    )

    _assert_route_names(
        app=app,
        called_path="/proxy/api/v1/users/99",
        excluded_route_name="/api/v1/users/{user_id}",
        included_route_name="/proxy/api/v1/users/{user_id}",
    )


def test_routing_root_path_with_redirect_slash():
    """Tests that redirect-slash matching preserves scope path across modes."""

    app = FastAPI(root_path="/proxy")

    @app.get("/items/")
    def list_items() -> list:
        return []

    _assert_route_names(
        app=app,
        called_path="/proxy/items",
        excluded_route_name="/proxy/items",
        included_route_name="/proxy/items",
    )


def test_routing_root_path_with_no_redirect_slash():
    """Tests that non-redirect-slash matching resolves with and without `root_path`."""

    app = FastAPI(root_path="/proxy", redirect_slashes=False)

    @app.get("/items/")
    def list_items() -> list:
        return []

    _assert_route_names(
        app=app,
        called_path="/proxy/items/",
        excluded_route_name="/items/",
        included_route_name="/proxy/items/",
    )


def test_routing_root_path_with_trailing_root_slash():
    """Tests that trailing-slash `root_path` values are normalized in both modes."""

    app = FastAPI(root_path="/proxy/")

    @app.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        return {"item_id": item_id}

    _assert_route_names(
        app=app,
        called_path="/proxy/items/42",
        excluded_route_name="/items/{item_id}",
        included_route_name="/proxy/items/{item_id}",
    )


def test_routing_root_path_with_trailing_nested():
    """Tests that nested `include_router` route names normalize `root_path` in both modes."""

    app = FastAPI(root_path="/proxy/")
    api_router = APIRouter(prefix="/api")
    v1_router = APIRouter(prefix="/v1")

    @v1_router.get("/users/{user_id}")
    def get_user(user_id: int) -> dict:
        return {"user_id": user_id}

    api_router.include_router(v1_router)
    app.include_router(api_router)

    _assert_route_names(
        app=app,
        called_path="/proxy/api/v1/users/99",
        excluded_route_name="/api/v1/users/{user_id}",
        included_route_name="/proxy/api/v1/users/{user_id}",
    )
