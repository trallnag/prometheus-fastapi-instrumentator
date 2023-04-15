from fastapi import FastAPI
from prometheus_client import Counter, start_http_server

from prometheus_fastapi_instrumentator import Instrumentator

start_http_server(9000)

PING_TOTAL = Counter("ping", "Number of pings calls.")

app = FastAPI()

Instrumentator().instrument(app).expose(app)


@app.get("/ping")
def get_ping():
    PING_TOTAL.inc()
    return "pong"
