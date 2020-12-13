<!-- omit in toc -->
# Prometheus FastAPI Instrumentator

[![PyPI version](https://badge.fury.io/py/prometheus-fastapi-instrumentator.svg)](https://pypi.python.org/pypi/prometheus-fastapi-instrumentator/)
[![Maintenance](https://img.shields.io/badge/maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![PyPI](https://img.shields.io/pypi/pyversions/prometheus-fastapi-instrumentator.svg)](https://pypi.python.org/pypi/prometheus-fastapi-instrumentator)
[![downloads](https://pepy.tech/badge/prometheus-fastapi-instrumentator/month)](https://pepy.tech/project/prometheus-fastapi-instrumentator/month)
[![docs](https://img.shields.io/badge/docs-here-blue)](https://trallnag.github.io/prometheus-fastapi-instrumentator/)

![release](https://github.com/trallnag/prometheus-fastapi-instrumentator/workflows/release/badge.svg)
![commit](https://github.com/trallnag/prometheus-fastapi-instrumentator/workflows/commit/badge.svg)
![CodeQL](https://github.com/trallnag/prometheus-fastapi-instrumentator/workflows/CodeQL/badge.svg?branch=master)
[![codecov](https://codecov.io/gh/trallnag/prometheus-fastapi-instrumentator/branch/master/graph/badge.svg)](https://codecov.io/gh/trallnag/prometheus-fastapi-instrumentator)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A configurable and modular Prometheus Instrumentator for your FastAPI. Install 
`prometheus-fastapi-instrumentator` from 
[PyPI](https://pypi.python.org/pypi/prometheus-fastapi-instrumentator/). Here 
is the fast track to get started with a preconfigured instrumentator:

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

With this, your FastAPI is instrumented and metrics ready to be scraped. The defaults give you:

- Counter `http_requests_total` with `handler`, `status` and `method`. Total 
    number of requests.
- Summary `http_request_size_bytes` with `handler`. Added up total of the 
    content lengths of all incoming requests.
- Summary `http_response_size_bytes` with `handler`. Added up total of the 
    content lengths of all outgoing responses.
- Histogram `http_request_duration_seconds` with `handler`. Only a few buckets 
    to keep cardinality low.
- Histogram `http_request_duration_highr_seconds` without any labels. Large 
    number of buckets (>20).

In addition, following behaviour is active:

- Status codes are grouped into `2xx`, `3xx` and so on.
- Requests without a matching template are grouped into the handler `none`.

If one of these presets does not suit your needs you can multiple things:

- Pick one of the already existing closures from 
    [`metrics`](https://trallnag.github.io/prometheus-fastapi-instrumentator/metrics.html)
    and pass it to the instrumentator instance. See [here](#adding-metrics) how to do that.
- Create your own instrumentation function that you can pass to an instrumentator
    instance. See [here](#creating-new-metrics) to learn how more.
- Don't use this package at all and just use the sorce code as inspiration on
    how to instrument your FastAPI.

Important: This package is not made for generic Prometheus instrumentation in
Python. Use the Prometheus client library for that. This packages uses it as well.

<!-- omit in toc -->
## Table of Contents

- [Features](#features)
- [Advanced Usage](#advanced-usage)
  - [Creating the Instrumentator](#creating-the-instrumentator)
  - [Adding metrics](#adding-metrics)
  - [Creating new metrics](#creating-new-metrics)
  - [Perform instrumentation](#perform-instrumentation)
  - [Exposing endpoint](#exposing-endpoint)
- [Prerequesites](#prerequesites)
- [Development](#development)

## Features

Beyond the fast track, this instrumentator is **highly configurable** and it 
is very easy to customize and adapt to your specific use case. Here is 
a list of some of these options you may opt-in to:

* Regex patterns to ignore certain routes.
* Completely ignore untemplated routes.
* Control instrumentation and exposition with an env var.
* Rounding of latencies to a certain decimal number.
* Renaming of labels and the metric.
* Metrics endpoint can compress data with gzip.
* Opt-in metric to monitor the number of requests in progress.

It also features a **modular approach to metrics** that should instrument all 
FastAPI endpoints. You can either choose from a set of already existing metrics 
or create your own. And every metric function by itself can be configured as 
well. You can see ready to use metrics [here](https://trallnag.github.io/prometheus-fastapi-instrumentator/metrics.html).

## Advanced Usage

This chapter contains an example on the advanced usage of the Prometheus 
FastAPI Instrumentator to showcase most of it's features. Fore more concrete 
info check out the 
[automatically generated documentation](https://trallnag.github.io/prometheus-fastapi-instrumentator/).

### Creating the Instrumentator

We start by creating an instance of the Instrumentator. Notice the additional 
`metrics` import. This will come in handy later.

```python
from prometheus_fastapi_instrumentator import Instrumentator, metrics

instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="inprogress",
    inprogress_labels=True,
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
Fore more concrete info check out the [automatically generated documentation](https://trallnag.github.io/prometheus-fastapi-instrumentator/).

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
        should_include_handler=True,
        should_include_method=False,
        should_include_status=True,
        metric_namespace="a",
        metric_subsystem="b",
    )
).add(
    metrics.response_size(
        should_include_handler=True,
        should_include_method=False,
        should_include_status=True,
        metric_namespace="namespace",
        metric_subsystem="subsystem",
    )
)
```

You can add as many metrics you like to the instrumentator.

### Creating new metrics

As already mentioned, it is possible to create custom functions to pass on to
`add()`. This is also how the default metrics are implemented. The 
documentation and code [here](https://trallnag.github.io/prometheus-fastapi-instrumentator/metrics.html) 
is helpful to get an overview.

The basic idea is that the instrumentator creates an `info` object that 
contains everything necessary for instrumentation based on the configuration 
of the instrumentator. This includes the raw request and response objects 
but also the modified handler, grouped status code and duration. Next, all 
registered instrumentation functions are called. They get `info` as their 
single argument.

Let's say we want to count the number of times a certain language 
has been requested.

```python
from typing import Callable
from prometheus_fastapi_instrumentator.metrics import Info
from prometheus_client import Counter

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

**Important:** The response object inside `info` can either be the response 
object or `None`. In addition, errors thrown in the handler are not caught by 
the instrumentator. I recommend to check the documentation and/or the source 
code before creating your own metrics.

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

Notice that this will do nothing if `should_respect_env_var` has been set 
during construction of the instrumentator object and the respective env var 
is not found.

### Exposing endpoint

To expose an endpoint for the metrics either follow 
[Prometheus Python Client](https://github.com/prometheus/client_python) and 
add the endpoint manually to the FastAPI or serve it on a separate server.
You can also use the included `expose` method. It will add an endpoint to the 
given FastAPI. With `should_gzip` you can instruct the endpoint to compress the 
data as long as the client accepts gzip encoding. Prometheus for example does 
by default. Beware that network bandwith is often cheaper than CPU cycles.

```python
instrumentator.expose(app, include_in_schema=False, should_gzip=True)
```

Notice that this will to nothing if `should_respect_env_var` has been set 
during construction of the instrumentator object and the respective env var 
is not found.

## Prerequesites

You can always check [`pyproject.toml`](/pyproject.toml) for dependencies.

* `python = "^3.6"` (tested with 3.6 and 3.9)
* `fastapi = ">=0.38.1, <=1.0.0"` (tested with 0.38.1 and 0.61.0)

## Development

Please refer to ["DEVELOPMENT.md"](DEVELOPMENT.md).
