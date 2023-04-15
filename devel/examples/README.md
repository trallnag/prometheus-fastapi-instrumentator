# Examples

- **[metrics-diff-port-uvicorn](./metrics-diff-port-uvicorn/):** Instrumented
  FastAPI app run with Uvicorn, but `/metrics` endpoint is exposed on a separate
  endpoint using Prometheus' `start_http_server` function.

- **[prom-multi-proc-gunicorn](./prom-multi-proc-gunicorn/):** How to use
  FastAPI app run with Gunivorn in combination with Prometheus client library.
  Focus on multiprocessing mode.
