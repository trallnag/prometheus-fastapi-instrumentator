# Examples

- **[metrics-diff-port-uvicorn](./metrics-diff-port-uvicorn/):** Instrumented
  FastAPI app run with Uvicorn, but `/metrics` endpoint is exposed on a separate
  endpoint using Prometheus' `start_http_server` function.

- **[default-metrics-diff-labels](./default-metrics-diff-labels/):** Usage of
  PFI with a custom instrumentation function that mimics the default metrics but
  with custom label names.

- **[prom-multi-proc-gunicorn](./prom-multi-proc-gunicorn/):** How to use
  FastAPI app run with Gunivorn in combination with Prometheus client library.
  Focus on multiprocessing mode.
