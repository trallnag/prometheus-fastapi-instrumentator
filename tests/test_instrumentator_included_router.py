from fastapi import APIRouter, FastAPI
from helpers import utils
from prometheus_client import Counter
from starlette.routing import Mount
from starlette.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_fastapi_instrumentator.routing import _get_route_name


def _handler_metric() -> Counter:
    return Counter("test", "Test.", ("modified_handler", "handler"))


def _add_handler_instrumentation(instrumentator: Instrumentator, metric: Counter):
    def instrumentation(info: metrics.Info) -> None:
        metric.labels(
            modified_handler=info.modified_handler,
            handler=str(info.request.url),
        ).inc()

    instrumentator.add(instrumentation)


def test_included_router_resolves_prefixed_handler():
    """Routes added via ``include_router`` must not 500 and must report their
    full, prefixed path as the handler label.

    Regression test for #370. Since FastAPI 0.137 ``include_router`` stores a
    ``_IncludedRouter`` (a ``BaseRoute`` without a ``path``) in ``app.routes``,
    which made route-name resolution raise ``AttributeError`` -> HTTP 500.
    Exercising the regression requires FastAPI >= 0.137; on earlier versions
    the assertions still hold because included routes were copied with their
    full path.
    """
    utils.reset_collectors()

    app = FastAPI()

    router = APIRouter()

    @router.get("/models")
    def models():
        return {"message": "from included router"}

    app.include_router(router, prefix="/v1")

    nested_inner = APIRouter()

    @nested_inner.get("/ping")
    def ping():
        return {"message": "from nested included router"}

    nested_outer = APIRouter()
    nested_outer.include_router(nested_inner, prefix="/inner")
    app.include_router(nested_outer, prefix="/api")

    metric = _handler_metric()
    instrumentator = Instrumentator()
    _add_handler_instrumentation(instrumentator, metric)
    instrumentator.instrument(app).expose(app)

    client = TestClient(app)

    assert client.get("/v1/models").status_code == 200
    assert client.get("/api/inner/ping").status_code == 200

    response = client.get("/metrics").content.decode()

    want = '{handler="http://testserver/v1/models",modified_handler="/v1/models"} 1.0\n'
    assert want in response

    want = '{handler="http://testserver/api/inner/ping",modified_handler="/api/inner/ping"} 1.0\n'
    assert want in response


def test_included_router_without_prefix():
    """An included router without a prefix resolves to the route's own path."""
    utils.reset_collectors()

    app = FastAPI()
    router = APIRouter()

    @router.get("/widget")
    def widget():
        return {"message": "ok"}

    app.include_router(router)

    metric = _handler_metric()
    instrumentator = Instrumentator()
    _add_handler_instrumentation(instrumentator, metric)
    instrumentator.instrument(app).expose(app)

    client = TestClient(app)

    assert client.get("/widget").status_code == 200

    response = client.get("/metrics").content.decode()
    want = '{handler="http://testserver/widget",modified_handler="/widget"} 1.0\n'
    assert want in response


def test_included_router_method_mismatch_does_not_crash():
    """A 405 on an included route (path matches, method does not) must not
    crash route-name resolution.

    Regression for #370: a method mismatch yields ``Match.PARTIAL``, which used
    to hit the same missing-``path`` access on the ``_IncludedRouter`` and turn
    the 405 into a 500.
    """
    utils.reset_collectors()

    app = FastAPI()
    router = APIRouter()

    @router.get("/models")
    def models():
        return {"message": "ok"}

    app.include_router(router, prefix="/v1")

    Instrumentator().instrument(app).expose(app)

    client = TestClient(app)

    assert client.post("/v1/models").status_code == 405


def test_mount_inside_included_router():
    """A Starlette ``Mount`` nested inside an included router resolves to its
    full, prefixed path (its effective context exposes the path via
    ``starlette_route``, not ``ctx.path``)."""
    utils.reset_collectors()

    app = FastAPI()

    subapp = FastAPI()

    @subapp.get("/deep")
    def deep():
        return {"message": "ok"}

    router = APIRouter()
    router.routes.append(Mount("/mnt", app=subapp))
    app.include_router(router, prefix="/m")

    metric = _handler_metric()
    instrumentator = Instrumentator()
    _add_handler_instrumentation(instrumentator, metric)
    instrumentator.instrument(app).expose(app)

    client = TestClient(app)

    assert client.get("/m/mnt/deep").status_code == 200

    response = client.get("/metrics").content.decode()
    want = '{handler="http://testserver/m/mnt/deep",modified_handler="/m/mnt/deep"} 1.0\n'
    assert want in response


def test_websocket_under_included_router_resolves_path():
    """WebSocket routes under an included router resolve to the full prefixed
    path. Their effective context stores the path on ``starlette_route`` (its
    ``ctx.path`` is empty), so this guards that extraction path directly."""
    utils.reset_collectors()

    app = FastAPI()
    router = APIRouter()

    @router.websocket("/ws")
    async def ws(websocket):
        await websocket.accept()
        await websocket.close()

    app.include_router(router, prefix="/v1")

    scope = {"type": "websocket", "path": "/v1/ws", "headers": []}
    assert _get_route_name(scope, app.routes) == "/v1/ws"
