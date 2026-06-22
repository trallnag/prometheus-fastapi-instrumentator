import asyncio
import sys

from requests import Response as TestClientResponse
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator
from helpers import utils

# Explicitly unload fastapi to ensure this module tests Starlette in isolation
if "fastapi" in sys.modules:
    del sys.modules["fastapi"]

setattr(TestClientResponse, "__test__", False)

# ------------------------------------------------------------------------------
# Setup


def create_starlette_app() -> Starlette:
    """Create a pure Starlette application for testing.

    Returns:
        Starlette: A Starlette application with several test routes.
    """

    utils.reset_collectors()

    # Define route handlers
    async def homepage(request):
        return PlainTextResponse("Hello from Starlette!")

    async def sleep_endpoint(request):
        seconds = float(request.query_params.get("seconds", 0.1))
        await asyncio.sleep(seconds)
        return JSONResponse({"message": f"Slept for {seconds}s"})

    async def error_endpoint(request):
        return JSONResponse(
            {"error": "Not found"}, status_code=404
        )

    async def item_endpoint(request):
        item_id = request.path_params.get("item_id")
        q = request.query_params.get("q")
        return JSONResponse({"item_id": item_id, "q": q})

    async def post_data_endpoint(request):
        try:
            data = await request.json()
            return JSONResponse({"received": data})
        except Exception:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    async def ignore_endpoint(request):
        return PlainTextResponse("Should be ignored")

    async def custom_response_endpoint(request):
        return PlainTextResponse("Custom response", status_code=201)

    # Define routes
    routes = [
        Route("/", homepage, methods=["GET"]),
        Route("/sleep", sleep_endpoint, methods=["GET"]),
        Route("/error", error_endpoint, methods=["GET"]),
        Route("/items/{item_id}", item_endpoint, methods=["GET"]),
        Route("/post", post_data_endpoint, methods=["POST"]),
        Route("/ignore", ignore_endpoint, methods=["GET"]),
        Route("/custom", custom_response_endpoint, methods=["GET"]),
    ]

    # Create Starlette app
    app = Starlette(routes=routes)

    return app


def test_starlette_instrumentation_basic():
    """Test basic instrumentation of a Starlette app."""
    app = create_starlette_app()
    Instrumentator().instrument(app).expose(app)
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200

    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"http_request_duration_seconds_count" in response.content


def test_starlette_different_paths():
    """Test instrumentation tracks different paths separately."""
    app = create_starlette_app()
    Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app)
    client = TestClient(app)

    # Make requests to different paths
    client.get("/")
    client.get("/")
    client.get("/sleep?seconds=0.01")
    client.get("/custom")

    response = client.get("/metrics")
    assert response.status_code == 200

    # Check that different handlers are tracked
    assert b'handler="/"' in response.content
    assert b'handler="/sleep"' in response.content
    assert b'handler="/custom"' in response.content


def test_starlette_http_methods():
    """Test instrumentation tracks different HTTP methods."""
    app = create_starlette_app()
    Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app)
    client = TestClient(app)

    # Make requests with different methods
    client.get("/")
    client.post("/post", json={"test": "data"})
    client.get("/")

    response = client.get("/metrics")
    assert response.status_code == 200

    # Check that methods are tracked
    assert b'method="GET"' in response.content
    assert b'method="POST"' in response.content


def test_starlette_status_codes():
    """Test instrumentation tracks status codes."""
    app = create_starlette_app()
    Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app)
    client = TestClient(app)

    # Make requests that result in different status codes
    client.get("/")  # 200
    client.get("/custom")  # 201
    client.get("/error")  # 404

    response = client.get("/metrics")
    assert response.status_code == 200

    # Check that status codes are tracked
    assert b'status="2xx"' in response.content
    assert b'status="4xx"' in response.content


def test_starlette_excluded_handlers():
    """Test that excluded handlers are not tracked."""
    app = create_starlette_app()
    Instrumentator(excluded_handlers=["/ignore", "/metrics"]).instrument(app).expose(app)
    client = TestClient(app)

    # Make requests
    client.get("/")
    client.get("/ignore")
    client.get("/")

    response = client.get("/metrics")
    assert response.status_code == 200

    # /ignore should not appear in metrics
    content = response.content.decode()
    assert 'handler="/ignore"' not in content


def test_starlette_custom_endpoint():
    """Test that metrics can be exposed on a custom endpoint."""
    app = create_starlette_app()
    Instrumentator().instrument(app).expose(app, endpoint="/prometheus_metrics")
    client = TestClient(app)

    # Make a request
    client.get("/")

    # Check custom metrics endpoint
    response = client.get("/prometheus_metrics")
    assert response.status_code == 200
    assert b"http_request_duration_seconds" in response.content

    # Check that default metrics endpoint doesn't exist
    response = client.get("/metrics")
    assert response.status_code == 404


def test_starlette_path_parameters():
    """Test that path parameters are tracked correctly."""
    app = create_starlette_app()
    Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app)
    client = TestClient(app)

    # Make requests with different path parameters
    client.get("/items/123")
    client.get("/items/456?q=test")
    client.get("/items/789")

    response = client.get("/metrics")
    assert response.status_code == 200

    # Check that the parametrized path is tracked as a single handler
    content = response.content.decode()
    assert 'handler="/items/{item_id}"' in content


def test_starlette_gzip_support():
    """Test that metrics endpoint supports gzip compression."""
    app = create_starlette_app()
    Instrumentator().instrument(app).expose(app, should_gzip=True)
    client = TestClient(app)

    # Make a request
    client.get("/")

    # Request with gzip encoding
    response = client.get("/metrics", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200
    assert response.headers.get("Content-Encoding") == "gzip"

    # Request explicitly opting out of gzip encoding
    response = client.get("/metrics", headers={"Accept-Encoding": "identity"})
    assert response.status_code == 200
    assert response.headers.get("Content-Encoding") != "gzip"
