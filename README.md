# Prometheus FastAPI Instrumentator

[![PyPI version](https://badge.fury.io/py/prometheus-fastapi-instrumentator.svg)](https://pypi.python.org/pypi/prometheus-fastapi-instrumentator/)
[![Maintenance](https://img.shields.io/badge/maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![downloads](https://img.shields.io/pypi/dm/prometheus-fastapi-instrumentator)](https://pypi.org/project/prometheus-fastapi-instrumentator/)

![release](https://github.com/trallnag/prometheus-fastapi-instrumentator/workflows/release/badge.svg)
![test branches](https://github.com/trallnag/prometheus-fastapi-instrumentator/workflows/test%20branches/badge.svg)
[![codecov](https://codecov.io/gh/trallnag/prometheus-fastapi-instrumentator/branch/master/graph/badge.svg)](https://codecov.io/gh/trallnag/prometheus-fastapi-instrumentator)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A configurable and modular Prometheus Instrumentator for your FastAPI. Install with:

    pip install prometheus-fastapi-instrumentator

## Fast Track

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

With this single line FastAPI is instrumented and all Prometheus metrics used 
in the FastAPI app can be scraped via the added `/metrics` endpoint. Out of the 
box a single histogram `http_request_duration_seconds` is exposed. A separate 
`http_requests_total` isn't necessary as the total can be retrieved with the 
`http_requests_total_count` series.

The sensible defaults give you the following:

* Status codes are grouped into `2xx`, `3xx` and so on.
* Requests without a matching template are grouped into the handler `none`.

---

Contents: **[Features](#features)** |
**[Advanced Usage](#advanced-usage)** | 
[Creating the Instrumentator](#creating-the-instrumentator) |
[Adding metrics](#adding-metrics) |
[Creating new metrics](#creating-new-metrics) |
[Perform instrumentation](#perform-instrumentation) |
[Exposing endpoint](#exposing-endpoint) |
**[Prerequesites](#prerequesites)** |
**[Development](#development)**

---

## Features

Beyond the fast track, this instrumentator is **highly configurable**. Here is 
a list of some of these options you may opt-in to:

* Regex patterns to ignore certain routes.
* Completely ignore untemplated routes.
* Control instrumentation and exposition with an env var.
* Rounding of latencies to a certain decimal number.
* Renaming of labels and the metric.

It also features a **modular approach to metrics** that should instrument all 
FastAPI endpoints. You can either choose from a set of already existing metrics 
or create your own. Ready-to-use are:

* Track content length of all requests.
* Track content length of all responses.
* Track content length of all requests / responses combined.

To find out how to configure the instrumentator, add additional metrics or 
create and add your own instrumentation code check out the next chapter.

## Advanced Usage

This chapter contains an example on the advanced usage of the Prometheus 
FastAPI Instrumentator to showcase most of it's features. Fore more concrete 
documentation check out the docstrings / type hints.

### Creating the Instrumentator

We start by creating an instance of the Instrumentator. Notice the additional 
`metrics` import. This will come in handy later.

```python
from prometheus_fastapi_instrumentator import Instrumentator, metrics

instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    env_var_name="ENABLE_METRICS",
)
```

Unlike in the fast track example, now the instrumentation and exposition will 
only take place if the environment variable `ENABLE_METRICS` is `true` at 
run-time. This can be helpful in larger deployments with multiple services
depending on the same base FastAPI.

### Adding metrics

Let's say we also want to instrument the size of requests and responses. For 
this we use the `add()` method. This method does nothing more than taking a
function and adding it to a list. Then during run-time every time FastAPI 
handles a request all functions in this list will be called while giving them 
a single argument that stores useful information like the request and 
response objects. If no `add()` at all is used, the default metric gets added 
in the background. This is what happens in the fast track example.

All instrumentation functions are stored as closures in the `metrics` module. 
Closures come in handy here because it allows us to configure the functions 
within.

```python
instrumentator.add(metrics.latency(buckets=(1, 2, 3,)))
```

This simply adds the metric you also get in the fast track example with a 
modified buckets argument. But we would also like to record the size of 
all requests and responses. 

```python
instrumentator.add(
    metrics.request_size(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
    )
).add(
    metrics.response_size(
        should_include_handler=False,
        should_include_method=False,
        should_include_status=False,
    )
)
```

You can add as many metrics you like to the instrumentator.

### Creating new metrics

As already mentioned, it is possible to create custom functions to pass on to
`add()`. Let's say we want to count the number of times a certain language 
has been requested.

```python
def http_requested_languages_total() -> Callable[[Info], None]:
    METRIC = Counter(
        "http_requested_languages_total", 
        "Number of times a certain language has been requested.", 
        labelnames=("langs",)
    )

    def instrumentation(info: Info) -> None:
        langs = set()
        lang_str = info.request.headers["Accept-Language"]
        for element in lang_str.split(",")
            element = element.split(";")[0].strip().lower()
            langs.add(element)
        for language in langs:
            METRIC.labels(language).inc()

    return instrumentation
```

The function `http_requested_languages_total` is used for persistent elements 
that are stored between all instrumentation executions (for example the 
metric instance itself). Next comes the closure. This function must adhere 
to the shown interface. It will always get an `Info` object that contains 
the request, response and a few other modified informations. For example the 
(grouped) status code or the handler. Finally, the closure is returned.

To use it, we hand over the closure to the instrumentator object.

```python
instrumentator.add(http_requested_languages_total())
```

### Perform instrumentation

Up to this point, the FastAPI has not been touched at all. Everything has been 
stored in the `instrumentator` only. To actually register the instrumentation 
with FastAPI, the `instrument()` method has to be called.

```python
instrumentator.instrument(app)
```

Notice that this will to nothing if `should_respect_env_var` has been set 
during construction of the instrumentator object and the respective env var 
is not found.

### Exposing endpoint

To expose an endpoint for the metrics either follow 
[Prometheus Python Client](https://github.com/prometheus/client_python) and 
add the endpoint manually to the FastAPI or serve it on a separate server.
You can also use the included `expose` method. It will add an endpoint to the 
given FastAPI.

```python
instrumentator.expose(app, include_in_schema=False)
```

Notice that this will to nothing if `should_respect_env_var` has been set 
during construction of the instrumentator object and the respective env var 
is not found.

## API Documentation

## Prerequesites

* `python = "^3.6"` (tested with 3.6 and 3.8)
* `fastapi = ">=0.38.1, <=1.0.0"` (tested with 0.38.1 and 0.61.0)
* `prometheus-client = "^0.8.0"` (tested with 0.8.0)

## Development

Developing and building this package on a local machine requires 
[Python Poetry](https://python-poetry.org/). I recommend to run Poetry in 
tandem with [Pyenv](https://github.com/pyenv/pyenv). Once the repository is 
cloned, run `poetry install` and `poetry shell`. From here you may start the 
IDE of your choice.

Take a look at the Makefile or workflows on how to test this package.
