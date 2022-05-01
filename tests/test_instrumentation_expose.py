import asyncio
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from starlette.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator

# ------------------------------------------------------------------------------
# Setup


def create_app() -> FastAPI:
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
    app = create_app()
    Instrumentator().instrument(app).expose(app)
    client = TestClient(app)

    response = client.get("/metrics")
    print(response.headers.items())
    assert (
        "text/plain; version=0.0.4; charset=utf-8; charset=utf-8"
        not in response.headers.values()
    )
