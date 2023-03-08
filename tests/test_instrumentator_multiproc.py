"""
Testing things in multi process mode is super weird, at least to me. I don't
understand how the registries in the Prometheus client library work once multi
process mode is activated. For now I seem to get by trying to reset collectors,
even though it does not fully reset everything.
"""

import asyncio
from datetime import datetime

import pytest
from fastapi import FastAPI
from helpers import utils
from httpx import AsyncClient
from starlette.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator


@pytest.mark.skipif(
    utils.is_prometheus_multiproc_valid(),
    reason="Environment variable must be not set in parent process.",
)
def test_multiproc_dir_not_found(monkeypatch):
    """Tests failing early if env var is set but dir does not exist."""

    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", "/DOES/NOT/EXIST")

    with pytest.raises(ValueError, match="not a directory"):
        Instrumentator().instrument(FastAPI())


@pytest.mark.skipif(
    utils.is_prometheus_multiproc_valid(),
    reason="Environment variable must be not set in parent process.",
)
def test_multiproc_expose_no_dir(monkeypatch):
    """
    Tests that metrics endpoint will raise exception if dir does not exist.
    Method expose that contains closure does not check for existence.
    """

    app = FastAPI()
    instrumentator = Instrumentator()
    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", "/DOES/NOT/EXIST")
    instrumentator.instrument(app).expose(app)

    with pytest.raises(ValueError, match="env PROMETHEUS_MULTIPROC_DIR"):
        TestClient(app).get("/metrics")


@pytest.mark.skipif(
    utils.is_prometheus_multiproc_valid(),
    reason="Environment variable must be not set in parent process.",
)
def test_multiproc_anti_test(monkeypatch, tmp_path):
    """
    Shows weird behavior of Prometheus client library. If env var is monkey
    patched, no errors whatsoever occur, but the metrics endpoint returns
    nothing. Also the internal registry contains no metrics.

    The moment I run this test with the env var set manually in the parent
    process, things start to work.
    """

    app = FastAPI()
    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", str(tmp_path))
    Instrumentator().instrument(app).expose(app)

    client = TestClient(app)
    client.get("/dummy")

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200

    metrics_content = metrics_response.content.decode()
    print("GET /metrics\n" + metrics_content)
    assert len(metrics_content) == 0


@pytest.mark.skipif(
    not utils.is_prometheus_multiproc_valid(),
    reason="Environment variable must be set in parent process.",
)
def test_multiproc_no_default_stuff():
    """Tests that multi process mode is activated.

    It is checked indirectly by asserting that metrics that are not supported in
    multi process mode are not exposed by Prometheus.
    """

    assert utils.is_prometheus_multiproc_valid()
    utils.reset_collectors()

    app = FastAPI()
    Instrumentator().instrument(app).expose(app)
    client = TestClient(app)

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200

    metrics_content = metrics_response.content.decode()
    print("GET /metrics\n" + metrics_content)
    assert "process_open_fds" not in metrics_content


@pytest.mark.skipif(
    not utils.is_prometheus_multiproc_valid(),
    reason="Environment variable must be set in parent process.",
)
def test_multiproc_correct_count():
    """Tests that counter metric has expected value with multi process mode."""

    assert utils.is_prometheus_multiproc_valid()
    utils.reset_collectors()

    app = FastAPI()
    Instrumentator().instrument(app).expose(app)
    client = TestClient(app)

    @app.get("/ping")
    def get_ping():
        return "pong"

    client.get("/ping")
    client.get("/ping")
    client.get("/ping")

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200

    metrics_content = metrics_response.content.decode()
    print("GET /metrics\n" + metrics_content)
    want = 'http_requests_total{handler="/ping",method="GET",status="2xx"} 3.0\n'
    assert want in metrics_content


@pytest.mark.skipif(
    not utils.is_prometheus_multiproc_valid(),
    reason="Environment variable must be set in parent process.",
)
async def test_multiproc_inprogress_metric():
    """
    Tests that in-progress metric is counting correctly in multi process mode.
    Depends on sleeping to get metrics while other requests are still running.
    """

    assert utils.is_prometheus_multiproc_valid()
    utils.reset_collectors()

    app = FastAPI()

    @app.get("/sleep")
    async def get_sleep(seconds: float):
        await asyncio.sleep(seconds)
        return f"Slept for {seconds}s"

    Instrumentator(
        should_instrument_requests_inprogress=True, inprogress_labels=True
    ).instrument(app).expose(app)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        tasks = []
        for i in range(3):
            tasks.append(asyncio.create_task(ac.get("/sleep?seconds=1")))
        print("1:", datetime.utcnow())
        await asyncio.sleep(0.5)
        print("2:", datetime.utcnow())
        metrics_response = await ac.get("/metrics")
        await asyncio.gather(*tasks)

    assert metrics_response.status_code == 200

    metrics_content = metrics_response.content.decode()
    print("3:", datetime.utcnow())
    print("GET /metrics\n" + metrics_content)
    assert (
        'http_requests_inprogress{handler="/sleep",method="GET"} 3.0' in metrics_content
    )
    assert (
        'http_requests_inprogress{handler="/metrics",method="GET"} 1.0' in metrics_content
    )


@pytest.mark.skipif(
    not utils.is_prometheus_multiproc_valid(),
    reason="Environment variable must be set in parent process.",
)
def test_multiproc_no_duplicates():
    """
    Tests that metrics endpoint does not contain duplicate metrics. According to
    documentation of Prometheus client library this can happen if metrics
    endpoint is setup incorrectly and multi process mode is activated.

    Can be done by having an endpoint that uses registry created outside of
    function body.
    """

    assert utils.is_prometheus_multiproc_valid()
    utils.reset_collectors()

    app = FastAPI()
    Instrumentator().instrument(app).expose(app)
    client = TestClient(app)

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200

    metrics_content = metrics_response.content.decode()
    print("GET /metrics\n" + metrics_content)

    substring = "# TYPE http_requests_total counter"
    assert metrics_content.count(substring) == 1
