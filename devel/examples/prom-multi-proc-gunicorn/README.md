# Example `prom-multi-proc-gunicorn`

Minimal example that shows integration of FastAPI (Gunicorn) with the Prometheus
client library in multi process mode without Prometheus FastAPI Instrumentator.
Highlights missing metrics that are not supported in multi process mode.

To run the example, you must have run `poetry install` and `poetry shell` in the
root of this repository. The following commands are executed relative to this
directory.

Set environment variable to an unused location:

```shell
export PROMETHEUS_MULTIPROC_DIR=/tmp/python-testing-pfi/560223ba-887f-429a-9c48-933df56a68ba
```

Start the app with Gunicorn using two Uvicorn workers:

```shell
rm -rf "$PROMETHEUS_MULTIPROC_DIR"
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
gunicorn main:app \
  --config gunicorn.conf.py \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8080
```

Interact with app:

```shell
for i in {1..5}; do curl localhost:8080/ping; done
curl localhost:8080/metrics
```

You should see something like this:

```txt
# TYPE ping_total counter
ping_total 5.0
# HELP metrics_total Number of metrics calls.
# TYPE metrics_total counter
metrics_total 1.0
# HELP main_total Counts of main executions.
# TYPE main_total counter
main_total 2.0
```

Check the returned metrics:

- `main_total` is `2`, because Gunicorn is using two workers.
- There are no `created_by` metrics. These are not supported by the Prometheus
  client library in multi process mode.
- No metrics for things like CPU and memory. They come from components like the
  `ProcessCollector` and `PlatformCollector` which are not supported by the
  Prometheus client library in multi process mode.

Links:

- <https://github.com/prometheus/client_python#multiprocess-mode-eg-gunicorn>
- <https://docs.gunicorn.org/en/stable/settings.html>
