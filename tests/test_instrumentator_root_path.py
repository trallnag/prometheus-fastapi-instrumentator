"""Tests for the instrumentator's handling of `root_path`.

Also see `test_routing_root_path.py` for tests of the routing module's handling
of `root_path`.
"""

import re

from fastapi import FastAPI
from prometheus_client import CollectorRegistry, Counter
from starlette.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator, metrics


def _build_root_path_app() -> FastAPI:
    app = FastAPI(root_path="/proxy")

    @app.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        return {"item_id": item_id}

    return app


def _build_instrumentation_metric(registry: CollectorRegistry) -> Counter:
    return Counter(
        "test",
        "Test.",
        ("modified_handler", "handler"),
        registry=registry,
    )


def _instrument_app(app: FastAPI, metric: Counter, **kwargs) -> None:
    def instrumentation(info: metrics.Info) -> None:
        metric.labels(
            modified_handler=info.modified_handler,
            handler=str(info.request.url),
        ).inc()

    Instrumentator(**kwargs).add(instrumentation).instrument(app).expose(app)


def test_instrumentator_root_path_with_exclude_by_default():
    """Tests that exported handler labels exclude `root_path` by default."""

    registry = CollectorRegistry(auto_describe=True)
    metric = _build_instrumentation_metric(registry)
    app = _build_root_path_app()
    _instrument_app(app, metric, registry=registry)

    client = TestClient(app, root_path="/proxy")

    assert client.get("/items/42").status_code == 200

    response = client.get("/metrics").content.decode()
    print(
        "GET /metrics (filtered)\n"
        + "\n".join(re.findall(r"^.*test_total.*$", response, flags=re.MULTILINE))
    )

    want = (
        '{handler="http://testserver/items/42",'
        'modified_handler="/items/{item_id}"} 1.0\n'
    )
    assert want in response


def test_instrumentator_root_path_with_include_root_path():
    """Tests that exported handler labels can include `root_path`."""

    registry = CollectorRegistry(auto_describe=True)
    metric = _build_instrumentation_metric(registry)
    app = _build_root_path_app()
    _instrument_app(app, metric, registry=registry, should_include_root_path=True)

    client = TestClient(app, root_path="/proxy")

    assert client.get("/items/42").status_code == 200

    response = client.get("/metrics").content.decode()
    print(
        "GET /metrics (filtered)\n"
        + "\n".join(re.findall(r"^.*test_total.*$", response, flags=re.MULTILINE))
    )

    want = (
        '{handler="http://testserver/items/42",'
        'modified_handler="/proxy/items/{item_id}"} 1.0\n'
    )
    assert want in response
