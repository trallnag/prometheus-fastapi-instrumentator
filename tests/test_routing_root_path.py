"""Tests for route resolution and instrumentation with ASGI ``root_path``."""

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from prometheus_fastapi_instrumentator import Instrumentator, metrics
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


def test_get_route_name_omits_root_path_for_templated_route():
    """Resolved route names are templated routes, not prefixed request paths."""

    app = FastAPI(root_path="/proxy")

    @app.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        return {"item_id": item_id}

    assert (
        get_route_name(Request(_scope(app, "/items/42", root_path="/proxy")))
        == "/items/{item_id}"
    )


def test_get_route_name_omits_root_path_with_included_router():
    """Included routers keep app/router prefixes but omit ASGI ``root_path``."""

    app = FastAPI(root_path="/proxy")
    router = APIRouter(prefix="/api")

    @router.get("/users/{user_id}")
    def get_user(user_id: int) -> dict:
        return {"user_id": user_id}

    app.include_router(router)

    assert (
        get_route_name(
            Request(_scope(app, "/api/users/99", root_path="/proxy"))
        )
        == "/api/users/{user_id}"
    )


def test_instrumentation_modified_handler_omits_root_path():
    """Middleware instrumentation should expose templated handlers without root path."""

    app = FastAPI()

    @app.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        return {"item_id": item_id}

    seen_handlers = []
    seen_root_paths = []

    def instrumentation(info: metrics.Info) -> None:
        seen_handlers.append(info.modified_handler)
        seen_root_paths.append(info.request.scope.get("root_path"))

    Instrumentator().add(instrumentation).instrument(app)

    client = TestClient(app, root_path="/proxy")
    response = client.get("/items/42")

    assert response.status_code == 200
    assert seen_root_paths == ["/proxy"]
    assert seen_handlers == ["/items/{item_id}"]
