import os

from fastapi import FastAPI
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    generate_latest,
    multiprocess,
)
from starlette.responses import Response

if "PROMETHEUS_MULTIPROC_DIR" not in os.environ:
    raise ValueError("PROMETHEUS_MULTIPROC_DIR must be set to existing empty dir.")


PING_TOTAL = Counter("ping", "Number of pings calls.")
METRICS_TOTAL = Counter("metrics", "Number of metrics calls.")

MAIN_TOTAL = Counter("main", "Counts of main executions.")
MAIN_TOTAL.inc()


app = FastAPI()


@app.get("/ping")
def get_ping():
    PING_TOTAL.inc()
    return "pong"


@app.get("/metrics")
def get_metrics():
    METRICS_TOTAL.inc()

    # Note the ephemeral registry being used here. This follows the Prometheus
    # client library documentation. It comes with multiple caveats. Using a
    # persistent registry might work on first glance but it will lead to issues.
    # For a long time PFI used a persistent registry, which was wrong.
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    resp = Response(content=generate_latest(registry))

    resp.headers["Content-Type"] = CONTENT_TYPE_LATEST
    return resp
