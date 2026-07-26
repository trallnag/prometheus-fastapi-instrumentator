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


def test_nested_app_subapp_only_instrumented_no_own_root_path():
    """Tests that mount prefix and root root_path are excluded when subapp is instrumented.

    The root app is configured with `root_path="/proxy"` (simulating a reverse
    proxy). The subapp has no own `root_path`. Only the subapp is instrumented
    with `should_include_root_path=True`.

    The instrumentator must NOT prepend either the root app's `/proxy` or the
    mount prefix `/api` to `modified_handler`. The handler should remain
    relative to the sub-application itself.

    Note: when root_path is set on the root FastAPI app its `__call__` injects
    it into the ASGI scope, so requests must include the proxy prefix in the
    URL for routing to work (the way a real reverse proxy would expose the app).
    """

    registry = CollectorRegistry(auto_describe=True)
    metric = _build_instrumentation_metric(registry)

    subapp = FastAPI()

    @subapp.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        return {"item_id": item_id}

    _instrument_app(subapp, metric, registry=registry, should_include_root_path=True)

    root = FastAPI(root_path="/proxy")
    root.mount("/api", subapp)

    client = TestClient(root)

    assert client.get("/proxy/api/items/7").status_code == 200

    response = client.get("/proxy/api/metrics").content.decode()
    print(
        "GET /proxy/api/metrics (filtered)\n"
        + "\n".join(re.findall(r"^.*test_total.*$", response, flags=re.MULTILINE))
    )

    # modified_handler must be relative to the subapp — neither the root app's
    # root_path (/proxy) nor the mount prefix (/api) must appear, because the
    # instrumentator only reads root_path from the instrumented subapp's own
    # app attribute, which is empty.
    want = (
        '{handler="http://testserver/proxy/api/items/7",'
        'modified_handler="/items/{item_id}"} 1.0\n'
    )
    assert want in response

    # Neither the root app's root_path nor the mount prefix must appear.
    assert 'modified_handler="/proxy/items/{item_id}"' not in response
    assert 'modified_handler="/api/items/{item_id}"' not in response
    assert 'modified_handler="/proxy/api/items/{item_id}"' not in response


def test_nested_app_subapp_only_instrumented_flag_indifferent_without_own_root_path():
    """Tests that the flag makes no difference when the subapp has no own root_path.

    The root app has `root_path="/proxy"` (reverse-proxy scenario). The subapp
    has no own `root_path`. Both `should_include_root_path=False` (default) and
    `should_include_root_path=True` must produce an identical `modified_handler`
    relative to the sub-application, because the instrumentator only reads
    `root_path` from the instrumented subapp's own app attribute (empty), not
    from the root app or the mount-injected scope value.
    """

    # --- with should_include_root_path=False (default) ---

    registry_off = CollectorRegistry(auto_describe=True)
    metric_off = Counter(
        "test_off",
        "Test.",
        ("modified_handler", "handler"),
        registry=registry_off,
    )

    subapp_off = FastAPI()

    @subapp_off.get("/items/{item_id}")
    def get_item_off(item_id: int) -> dict:
        return {"item_id": item_id}

    def instrumentation_off(info: metrics.Info) -> None:
        metric_off.labels(
            modified_handler=info.modified_handler,
            handler=str(info.request.url),
        ).inc()

    Instrumentator(registry=registry_off, should_include_root_path=False).add(
        instrumentation_off
    ).instrument(subapp_off).expose(subapp_off)

    root_off = FastAPI(root_path="/proxy")
    root_off.mount("/api", subapp_off)

    client_off = TestClient(root_off)
    assert client_off.get("/proxy/api/items/7").status_code == 200

    response_off = client_off.get("/proxy/api/metrics").content.decode()

    want = (
        '{handler="http://testserver/proxy/api/items/7",'
        'modified_handler="/items/{item_id}"} 1.0\n'
    )
    assert want in response_off

    # --- with should_include_root_path=True ---

    registry_on = CollectorRegistry(auto_describe=True)
    metric_on = Counter(
        "test_on",
        "Test.",
        ("modified_handler", "handler"),
        registry=registry_on,
    )

    subapp_on = FastAPI()

    @subapp_on.get("/items/{item_id}")
    def get_item_on(item_id: int) -> dict:
        return {"item_id": item_id}

    def instrumentation_on(info: metrics.Info) -> None:
        metric_on.labels(
            modified_handler=info.modified_handler,
            handler=str(info.request.url),
        ).inc()

    Instrumentator(registry=registry_on, should_include_root_path=True).add(
        instrumentation_on
    ).instrument(subapp_on).expose(subapp_on)

    root_on = FastAPI(root_path="/proxy")
    root_on.mount("/api", subapp_on)

    client_on = TestClient(root_on)
    assert client_on.get("/proxy/api/items/7").status_code == 200

    response_on = client_on.get("/proxy/api/metrics").content.decode()

    # When the subapp has no own root_path, enabling should_include_root_path
    # adds nothing — result must be identical to the default.
    assert want in response_on

    # Neither the root's root_path nor the mount prefix must appear in either case.
    assert 'modified_handler="/proxy/items/{item_id}"' not in response_off
    assert 'modified_handler="/proxy/items/{item_id}"' not in response_on
    assert 'modified_handler="/api/items/{item_id}"' not in response_off
    assert 'modified_handler="/api/items/{item_id}"' not in response_on
