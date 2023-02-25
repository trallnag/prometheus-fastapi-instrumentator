from fastapi import FastAPI
from helpers import utils
from prometheus_client import Counter
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

    for url in ["/subapi/sub", "/subapi", "/app"]:
        print(f"GET {url} " + client.get(url).content.decode())

    response = client.get("/metrics").content.decode()
    print("GET /metrics\n" + response)

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
    print("GET /metrics\n" + response)

    # Note the modified_handler. It is relative to the instrumented subapp.
    want = '{handler="http://testserver/subapi/sub",modified_handler="/sub"} 1.0\n'
    assert want in response

    want = '{handler="http://testserver/subapi/",modified_handler="none"} 1.0\n'
    assert want in response

    want = '{handler="http://testserver/subapi"'
    assert want not in response

    want = '{handler="http://testserver/app"'
    assert want not in response
