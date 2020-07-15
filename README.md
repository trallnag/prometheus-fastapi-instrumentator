# Prometheus FastAPI Exporter

[![PyPI version](https://badge.fury.io/py/prometheus-fastapi-exporter.svg)](https://pypi.python.org/pypi/prometheus-fastapi-exporter/)
[![Maintenance](https://img.shields.io/badge/maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![downloads](https://img.shields.io/pypi/dm/prometheus-fastapi-exporter)](https://pypi.org/project/prometheus-fastapi-exporter/)

![release](https://github.com/trallnag/prometheus-fastapi-exporter/workflows/release/badge.svg)
![test branches](https://github.com/trallnag/prometheus-fastapi-exporter/workflows/test%20branches/badge.svg)
[![codecov](https://codecov.io/gh/trallnag/prometheus-fastapi-exporter/branch/master/graph/badge.svg)](https://codecov.io/gh/trallnag/prometheus-fastapi-exporter)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Instruments your FastAPI. Install with:

    pip install prometheus-fastapi-exporter

## Fast Track

```python
from prometheus_fastapi_exporter import PrometheusFastApiExporter
PrometheusFastApiExporter().instrument(app).expose(app)
```

With this single line the API is instrumented and metrics are exposed at 
`/metrics`. The exporter includes a single metric:

`http_request_duration_seconds{handler, method, status}`

With the time series included in this metric you can get everything from total 
requests to the average latency. Here are distinct features of this 
metric, all of them can be **configured and deactivated** if you wish:

* Status codes are grouped into `2xx`, `3xx` and so on. This reduces 
    cardinality. 
* Requests without a matching template are grouped into the handler `none`.
* If exceptions occur during request processing and no status code was returned 
    it will default to a `500` server error.

## Prerequesites

You can also check the `pyproject.toml` for detailed requirements.

* `python = "^3.6"` (tested with 3.6 and 3.8)
* `fastapi = ">=0.38.1, <=1.0.0"` (tested with 3.8.1 and 0.58.1)
* `prometheus-client = "^0.8.0"` (tested with 0.8.0)

## Example with all parameters

```python
PrometheusFastApiExporter(
    metrics_endpoint="/prometheus/metrics",
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_group_untemplated=False,
    excluded_handlers=["/metrics", "/admin"],
    buckets=[1, 2, 3, 4, 5],
    metric_name="my_custom_metric_name",
    label_names=("method_type", "path", "status_code",),
).instrument(app).expose(endpoint="/prometheus_metrics")
```

`instrument`: Instruments the given FastAPI based on the configuration based in 
the constructur of the exporter class.

`expose`: Completely separate from `instrument` and not necessary for 
instrumentation. Just a simple option to expose metrics by adding an endpoint 
to the given FastAPI. Supports multiprocess mode. 

## Multiprocess Mode

Remember that additional configuration is necessary if the instrumented FastAPI 
is run with a pre-fork server like Gunicorn. See the official guideline for 
this [here](https://github.com/prometheus/client_python). I recommend have 
something along this in your gunicorn config module:

```python
def on_starting(server):
    """Called just before the master process is initialized."""

    prometheus_multiproc_dir = os.environ.get("prometheus_multiproc_dir")

    if prometheus_multiproc_dir is None:
        raise OSError("Environment variable 'prometheus_multiproc_dir' must be set.")
    
    log.info("Prepare Prometheus for Gunicorn usage. Wipe registry directory.")
    subprocess.run(["rm", "-rf", prometheus_multiproc_dir])
    subprocess.run(["mkdir", "-p", prometheus_multiproc_dir])

    log.info(f"Prometheus multiprocess registry at {prometheus_multiproc_dir}.")

def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)
```

While it is possible to set the environment variable from within code, it is 
not recommended. In some setups it will work fine, in others it will not. The 
environment variable MUST be set before any import of Prometheus stuff occures.

## Development

Developing and building this package on a local machine requires 
[Python Poetry](https://python-poetry.org/). I recommend to run Poetry in 
tandem with [Pyenv](https://github.com/pyenv/pyenv). Once the repository is 
cloned, run `poetry install` and `poetry shell`. From here you may start the 
IDE of your choice.

For formatting, the [black formatter](https://github.com/psf/black) is used.
Run `black .` in the repository to reformat source files. It will respect
the black configuration in the `pyproject.toml`.
