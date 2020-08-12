# Prometheus FastAPI Instrumentator

[![PyPI version](https://badge.fury.io/py/prometheus-fastapi-instrumentator.svg)](https://pypi.python.org/pypi/prometheus-fastapi-instrumentator/)
[![Maintenance](https://img.shields.io/badge/maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![downloads](https://img.shields.io/pypi/dm/prometheus-fastapi-instrumentator)](https://pypi.org/project/prometheus-fastapi-instrumentator/)

![release](https://github.com/trallnag/prometheus-fastapi-instrumentator/workflows/release/badge.svg)
![test branches](https://github.com/trallnag/prometheus-fastapi-instrumentator/workflows/test%20branches/badge.svg)
[![codecov](https://codecov.io/gh/trallnag/prometheus-fastapi-instrumentator/branch/master/graph/badge.svg)](https://codecov.io/gh/trallnag/prometheus-fastapi-instrumentator)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Instrument your FastAPI with Prometheus metrics. Install with:

    pip install prometheus-fastapi-instrumentator

## Fast Track

```python
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

With this single line FastAPI is instrumented and all Prometheus metrics used 
in the FastAPI app can be scraped via the added `/metrics` endpoint. 

The exporter includes the single metric `http_request_duration_seconds` of 
the type Histogram. A separate `http_requests_total` isn't necessary as the 
total can be retrieved with the `http_requests_total_count` series.

The Prometheus FastAPI Instrumentator (any idea for a short hand?) is highly
configurable and has few handy features.

* **Opt-out** (activated by default):
    * Status codes are grouped into `2xx`, `3xx` and so on.
    * Requests without a matching template are grouped into the handler `none`.
    * Regex patterns to ignore certain routes.    
* **Opt-in** (Deactivated by default):
    * Control instrumentation and exposition of FastAPI at runtime by setting 
        an environment variable.
    * Rounding of latencies to a certain decimal number.
    * Completely ignore untemplated routes.
    * Renaming of labels and the metric.


See the *Example with all parameters* for all possible options.

## Example with all parameters

```python
from prometheus_fastapi_instrumentator import PrometheusFastApiInstrumentator
PrometheusFastApiInstrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_group_untemplated=False,
    should_round_latency_decimals=True,
    should_respect_env_var_existence=True,
    excluded_handlers=["/metrics", "/admin"],
    buckets=[1, 2, 3, 4, 5],
    metric_name="my_custom_metric_name",
    label_names=("method_type", "path", "status_code",),
    round_latency_decimals=3,
    env_var_name="PROMETHEUS",
).instrument(app).expose(app, "/prometheus_metrics")
```

`instrument`: Instruments the given FastAPI based on the configuration in 
the constructur of the exporter class.

`expose`: Completely separate from `instrument` and not necessary for 
instrumentation. Just a simple option to expose metrics by adding an endpoint 
to the given FastAPI. Supports multiprocess mode.

## Prerequesites

* `python = "^3.6"` (tested with 3.6 and 3.8)
* `fastapi = ">=0.38.1, <=1.0.0"` (tested with 0.38.1 and 0.59.0)
* `prometheus-client = "^0.8.0"` (tested with 0.8.0)

## Development

Developing and building this package on a local machine requires 
[Python Poetry](https://python-poetry.org/). I recommend to run Poetry in 
tandem with [Pyenv](https://github.com/pyenv/pyenv). Once the repository is 
cloned, run `poetry install` and `poetry shell`. From here you may start the 
IDE of your choice.

For formatting, the [black formatter](https://github.com/psf/black) is used.
Run `black .` in the repository to reformat source files. It will respect
the black configuration in the `pyproject.toml`. For more information just 
take a look at the GitHub workflow files.

