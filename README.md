# Prometheus FastAPI Exporter

[![PyPI version](https://badge.fury.io/py/prometheus-fastapi-exporter.svg)](https://pypi.python.org/pypi/prometheus-fastapi-exporter/)
[![Maintenance](https://img.shields.io/badge/maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)

[![CI sas](https://github.com/trallnag/prometheus-fastapi-exporter/workflows/CI%20Development/badge.svg)](https://github.com/trallnag/prometheus-fastapi-exporter)
[![CI Production](https://github.com/trallnag/prometheus-fastapi-exporter/workflows/CI%20Production/badge.svg)](https://github.com/trallnag/prometheus-fastapi-exporter)
[![codecov](https://codecov.io/gh/trallnag/prometheus-fastapi-exporter/branch/master/graph/badge.svg)](https://codecov.io/gh/trallnag/prometheus-fastapi-exporter)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Instruments your FastAPI and adds the metrics endpoint to it. Install with:

    pip install prometheus-fastapi-exporter

## Fast Track

```python
from prometheus_fastapi_exporter import PrometheusFastApiExporter
PrometheusFastApiExporter(your_fastapi_app).instrument()
```

With this single line the API is instrumented and metrics are exposed at 
`/metrics`. The exporter includes a single metric only:

`http_request_duration_seconds{handler, method, status}`

With the time series included in this metric you can get everything from total 
requests to the average latency. Here are distinct features of this 
metric, all of them can be configured and deactivated if you wish:

* Status codes are grouped into `2xx`, `3xx` and so on. This reduces 
    cardinality. 
* Requests without a matching template are grouped into the handler `none`.
* If exceptions occur during request processing and no status code was returned 
    it will default to a `500` server error.
* By default, methods (`GET`, `POST`, etc.) are ignored.

## Prerequesites

You can also check the `pyproject.toml` for detailed requirements.

* `python = "^3.6"` (tested with 3.6 and 3.8)
* `fastapi = ">=0.38.1, <=1.0.0"` (tested with 3.8.1 and 0.58.1)
* `prometheus-client = "^0.8.0"` (tested with 0.8.0)

## Example with all parameters

```python
PrometheusFastApiExporter(
    app=app,
    metrics_endpoint="/prometheus/metrics",
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_group_untemplated=False,
    should_ignore_method=False,
    excluded_handlers=["/metrics", "/admin"],
    buckets=[1, 2, 3, 4, 5],
    metric_name="my_custom_metric_name",
    label_names=("method_type", "path", "status_code",),
).instrument()
```

## Development

Developing and building this package on a local machine requires 
[Python Poetry](https://python-poetry.org/). I recommend to run Poetry in 
tandem with [Pyenv](https://github.com/pyenv/pyenv). Once the repository is 
cloned, run `poetry install` and `poetry shell`. From here you may start the 
IDE of your choice.

For formatting, the [black formatter](https://github.com/psf/black) is used.
Run `black .` in the repository to reformat source files. It will respect
the black configuration in the `pyproject.toml`.
