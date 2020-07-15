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

With this single line FastAPI is instrumented and all Prometheus metrics used 
in the FastAPI app can be exported via the `/metrics` endpoint. 

The exporter includes the single metric `http_request_duration_seconds`. 
Basically everything around it can be configured and deactivated. These 
options include:

* Status codes are grouped into `2xx`, `3xx` and so on.
* Requests without a matching template are grouped into the handler `none`.
* Renaming of labels and the metric.
* Regex patterns to ignore certain routes.

See the *Example with all parameters* for all possible options or check 
out the documentation itself.

## Example with all parameters

```python
PrometheusFastApiExporter(
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

## Prerequesites

* `python = "^3.6"` (tested with 3.6 and 3.8)
* `fastapi = ">=0.38.1, <=1.0.0"` (tested with 3.8.1 and 0.58.1)
* `prometheus-client = "^0.8.0"` (tested with 0.8.0)

## Development

Developing and building this package on a local machine requires 
[Python Poetry](https://python-poetry.org/). I recommend to run Poetry in 
tandem with [Pyenv](https://github.com/pyenv/pyenv). Once the repository is 
cloned, run `poetry install` and `poetry shell`. From here you may start the 
IDE of your choice.

For formatting, the [black formatter](https://github.com/psf/black) is used.
Run `black .` in the repository to reformat source files. It will respect
the black configuration in the `pyproject.toml`.
