import asyncio
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator

# ------------------------------------------------------------------------------
# Setup


def create_fastapi_app() -> FastAPI:
    app = FastAPI()

    @app.get("/")
    def read_root():
        return "Hello World!"

    @app.get("/sleep")
    async def sleep(seconds: float):
        await asyncio.sleep(seconds)
        return f"I have slept for {seconds}s"

    @app.get("/always_error")
    def read_always_error():
        raise HTTPException(status_code=404, detail="Not really error")

    @app.get("/ignore")
    def read_ignore():
        return "Should be ignored"

    @app.get("/items/{item_id}")
    def read_item(item_id: int, q: Optional[str] = None):
        return {"item_id": item_id, "q": q}

    @app.get("/just_another_endpoint")
    def read_just_another_endpoint():
        return "Green is my pepper"

    @app.post("/items")
    def create_item(item: Dict[Any, Any]):
        return None

    return app


def create_starlette_app() -> Starlette:
    async def homepage(request):
        return PlainTextResponse("Homepage")

    return Starlette(routes=[Route("/", endpoint=homepage)])


def reset_prometheus() -> None:
    from prometheus_client import REGISTRY

    # Unregister all collectors.
    collectors = list(REGISTRY._collector_to_names.keys())
    print(f"before unregister collectors={collectors}")
    for collector in collectors:
        REGISTRY.unregister(collector)
    print(f"after unregister collectors={list(REGISTRY._collector_to_names.keys())}")

    # Import default collectors.
    from prometheus_client import gc_collector, platform_collector, process_collector

    # Re-register default collectors.
    process_collector.ProcessCollector()
    platform_collector.PlatformCollector()
    gc_collector.GCCollector()


# ------------------------------------------------------------------------------
# Tests


def test_expose_default_content_type():
    reset_prometheus()
    app = create_fastapi_app()
    Instrumentator().instrument(app).expose(app)
    client = TestClient(app)

    response = client.get("/metrics")
    print(response.headers.items())
    assert (
        "text/plain; version=0.0.4; charset=utf-8; charset=utf-8"
        not in response.headers.values()
    )


def test_fastapi_app_expose():
    reset_prometheus()
    app = create_fastapi_app()
    Instrumentator().instrument(app).expose(app)
    client = TestClient(app)

    response = client.get("/metrics")

    assert response.status_code == 200


def test_starlette_app_expose():
    reset_prometheus()
    app = create_starlette_app()
    Instrumentator().instrument(app).expose(app)
    client = TestClient(app)

    response = client.get("/metrics")

    assert response.status_code == 200
