import re

from fastapi import APIRouter, FastAPI
from helpers import utils
from prometheus_client import CollectorRegistry, Counter, generate_latest
from starlette.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator, metrics


def test_mounted_app_with_app():
    """Tests handling of mounted app when root app is instrumented."""

    utils.reset_collectors()

    app = FastAPI()

    @app.get("/app")
    def read_main():
        return {"message": "Hello World from main app"}

    subapp = FastAPI()

    @subapp.get("/sub")
    def read_sub():
        return {"message": "Hello World from sub API"}

    app.mount("/subapi", subapp)

    metric = Counter("test", "Test.", ("modified_handler", "handler"))

    def instrumentation(info: metrics.Info) -> None:
        metric.labels(
            modified_handler=info.modified_handler, handler=str(info.request.url)
        ).inc()

    Instrumentator().add(instrumentation).instrument(app).expose(app)

    client = TestClient(app)

    assert client.get("/subapi/sub").status_code == 200

    assert client.get("/subapi").status_code == 404

    assert client.get("/app").status_code == 200

    response = client.get("/metrics").content.decode()
    print(
        "GET /metrics (filtered)\n"
        + "\n".join(re.findall(r"^.*test_total.*$", response, flags=re.MULTILINE))
    )

    want = '{handler="http://testserver/subapi/sub",modified_handler="/subapi/sub"} 1.0\n'
    assert want in response

    want = '{handler="http://testserver/subapi",modified_handler="none"} 1.0\n'
    assert want in response

    want = '{handler="http://testserver/subapi/",modified_handler="none"} 1.0\n'
    assert want in response

    want = '{handler="http://testserver/app",modified_handler="/app"} 1.0\n'
    assert want in response


def test_mounted_app_instrumented_only():
    """Tests case when mounted app is instrumented and not root app."""

    utils.reset_collectors()

    app = FastAPI()

    @app.get("/app")
    def read_main():
        return {"message": "Hello World from main app"}

    subapp = FastAPI()

    @subapp.get("/sub")
    def read_sub():
        return {"message": "Hello World from sub API"}

    app.mount("/subapi", subapp)

    metric = Counter("test", "Test.", ("modified_handler", "handler"))

    def instrumentation(info: metrics.Info) -> None:
        metric.labels(
            modified_handler=info.modified_handler, handler=str(info.request.url)
        ).inc()

    Instrumentator().add(instrumentation).instrument(subapp).expose(app)

    client = TestClient(app)

    for url in ["/subapi/sub", "/subapi", "/app"]:
        print(f"GET {url} " + client.get(url).content.decode())

    response = client.get("/metrics").content.decode()
    print(
        "GET /metrics (filtered)\n"
        + "\n".join(re.findall(r"^.*test_total.*$", response, flags=re.MULTILINE))
    )

    # Note the modified_handler. It is relative to the instrumented subapp.
    want = '{handler="http://testserver/subapi/sub",modified_handler="/sub"} 1.0\n'
    assert want in response

    want = '{handler="http://testserver/subapi/",modified_handler="none"} 1.0\n'
    assert want in response

    want = '{handler="http://testserver/subapi"'
    assert want not in response

    want = '{handler="http://testserver/app"'
    assert want not in response


def test_mounted_app_with_nested_routers():
    """Regression test for issue #389.

    Tests that routes in a mounted sub-app with nested APIRouters do not
    end up with handler="none" in the metrics. Routes should be labeled with
    their correct paths, including the mount prefix and router prefixes.

    This mirrors the scenario reported in issue #389 where a main app
    instruments itself, mounts a sub-app at /api/v1, and that sub-app
    includes APIRouters with their own prefixes.
    """

    utils.reset_collectors()

    # Make a component for a group of related endpoints
    component1 = APIRouter(prefix="", tags=["component1"])
    component2 = APIRouter(prefix="", tags=["component2"])

    @component1.get("/list")
    def c1_list():
        return [1, 2, 3]

    @component2.get("/list")
    def c2_list():
        return [4, 5, 6]

    # Combine multiple components to a standalone API
    subapp = FastAPI()
    subapp.include_router(component1, prefix="/c1")
    subapp.include_router(component2, prefix="/c2")

    # Use a dedicated registry so the default metrics of this test do not leak
    # into the shared default registry used by other tests.
    registry = CollectorRegistry(auto_describe=True)

    # Main app exposes multiple APIs and own endpoints like /health /ready, etc.
    app = FastAPI()
    Instrumentator(registry=registry).instrument(app).expose(app)
    app.mount("/api/v1", subapp)

    @app.get("/health")
    def health():
        return {"ready": True}

    client = TestClient(app)

    # Make requests to verify endpoints work
    assert client.get("/api/v1/c1/list").status_code == 200
    assert client.get("/api/v1/c1/list").json() == [1, 2, 3]

    assert client.get("/api/v1/c2/list").status_code == 200
    assert client.get("/api/v1/c2/list").json() == [4, 5, 6]

    assert client.get("/health").status_code == 200
    assert client.get("/health").json() == {"ready": True}

    # Check metrics - the important part of the regression test
    metrics_output = generate_latest(registry).decode()

    # Verify that endpoints do NOT have handler="none"
    # They should have the correct handler labels with full paths
    assert 'handler="/api/v1/c1/list"' in metrics_output
    assert 'handler="/api/v1/c2/list"' in metrics_output
    assert 'handler="/health"' in metrics_output

    # Ensure we don't have any mounted app routes with handler="none".
    lines_with_none = [
        line
        for line in metrics_output.split("\n")
        if 'handler="none"' in line and "http_request" in line
    ]
    assert len(lines_with_none) == 0, f"Found routes with handler=none: {lines_with_none}"
