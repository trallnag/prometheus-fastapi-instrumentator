# Prometheus FastAPI Instrumentator <!-- omit in toc -->

[![pypi-version](https://badge.fury.io/py/prometheus-fastapi-instrumentator.svg)](https://pypi.python.org/pypi/prometheus-fastapi-instrumentator)
[![python-versions](https://img.shields.io/pypi/pyversions/prometheus-fastapi-instrumentator.svg)](https://pypi.python.org/pypi/prometheus-fastapi-instrumentator)
[![downloads](https://pepy.tech/badge/prometheus-fastapi-instrumentator/month)](https://pepy.tech/project/prometheus-fastapi-instrumentator/month)
[![build](https://img.shields.io/github/actions/workflow/status/trallnag/kubestatus2cloudwatch/ci.yaml?branch=master)](https://github.com/trallnag/kubestatus2cloudwatch/actions)
[![codecov](https://codecov.io/gh/trallnag/prometheus-fastapi-instrumentator/branch/master/graph/badge.svg)](https://codecov.io/gh/trallnag/prometheus-fastapi-instrumentator)

A configurable and modular Prometheus Instrumentator for your FastAPI. Install
`prometheus-fastapi-instrumentator` from
[PyPI](https://pypi.python.org/pypi/prometheus-fastapi-instrumentator/). Here is
the fast track to get started with a pre-configured instrumentator. Import the
instrumentator class:

```python
from prometheus_fastapi_instrumentator import Instrumentator
```

Instrument your app with default metrics and expose the metrics:

```python
Instrumentator().instrument(app).expose(app)
```

Depending on your code you might have to use the following instead:

```python
instrumentator = Instrumentator().instrument(app)

@app.on_event("startup")
async def _startup():
    instrumentator.expose(app)
```

With this, your FastAPI is instrumented and metrics are ready to be scraped. The
defaults give you:

- Counter `http_requests_total` with `handler`, `status` and `method`. Total
  number of requests.
- Summary `http_request_size_bytes` with `handler`. Added up total of the
  content lengths of all incoming requests.
- Summary `http_response_size_bytes` with `handler`. Added up total of the
  content lengths of all outgoing responses.
- Histogram `http_request_duration_seconds` with `handler` and `method`. Only a
  few buckets to keep cardinality low.
- Histogram `http_request_duration_highr_seconds` without any labels. Large
  number of buckets (>20).

In addition, following behavior is active:

- Status codes are grouped into `2xx`, `3xx` and so on.
- Requests without a matching template are grouped into the handler `none`.

If one of these presets does not suit your needs you can do one of multiple
things:

- Pick one of the already existing closures from
  [`metrics`](./src/prometheus_fastapi_instrumentator/metrics.py) and pass it to
  the instrumentator instance. See [here](#adding-metrics) how to do that.
- Create your own instrumentation function that you can pass to an
  instrumentator instance. See [here](#creating-new-metrics) to learn how more.
- Don't use this package at all and just use the source code as inspiration on
  how to instrument your FastAPI.

## Table of Contents <!-- omit in toc -->

<!--TOC-->

- [Disclaimer](#disclaimer)
- [Features](#features)
- [Advanced Usage](#advanced-usage)
  - [Creating the Instrumentator](#creating-the-instrumentator)
  - [Adding metrics](#adding-metrics)
  - [Creating new metrics](#creating-new-metrics)
  - [Perform instrumentation](#perform-instrumentation)
  - [Specify namespace and subsystem](#specify-namespace-and-subsystem)
  - [Exposing endpoint](#exposing-endpoint)
- [Contributing](#contributing)
- [Licensing](#licensing)

<!--TOC-->

## Disclaimer

Not made for generic Prometheus instrumentation in Python. Use the Prometheus
client library for that. This packages uses it as well.

All the generic middleware and instrumentation code comes with a cost in
performance that can become noticeable.

## Features

Beyond the fast track, this instrumentator is **highly configurable** and it is
very easy to customize and adapt to your specific use case. Here is a list of
some of these options you may opt-in to:

- Regex patterns to ignore certain routes.
- Completely ignore untemplated routes.
- Control instrumentation and exposition with an env var.
- Rounding of latencies to a certain decimal number.
- Renaming of labels and the metric.
- Metrics endpoint can compress data with gzip.
- Opt-in metric to monitor the number of requests in progress.

It also features a **modular approach to metrics** that should instrument all
FastAPI endpoints. You can either choose from a set of already existing metrics
or create your own. And every metric function by itself can be configured as
well.

## Advanced Usage

This chapter contains an example on the advanced usage of the Prometheus FastAPI
Instrumentator to showcase most of it's features.

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
    custom_labels={"service": "example-label"}
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
handles a request all functions in this list will be called while giving them a
single argument that stores useful information like the request and response
objects. If no `add()` at all is used, the default metric gets added in the
background. This is what happens in the fast track example.

All instrumentation functions are stored as closures in the `metrics` module.

Closures come in handy here because it allows us to configure the functions
within.

```python
instrumentator.add(metrics.latency(buckets=(1, 2, 3,)))
```

This simply adds the metric you also get in the fast track example with a
modified buckets argument. But we would also like to record the size of all
requests and responses.

```python
instrumentator.add(
    metrics.request_size(
        should_include_handler=True,
        should_include_method=False,
        should_include_status=True,
        metric_namespace="a",
        metric_subsystem="b",
        custom_labels={"service": "example-label"}
    )
).add(
    metrics.response_size(
        should_include_handler=True,
        should_include_method=False,
        should_include_status=True,
        metric_namespace="namespace",
        metric_subsystem="subsystem",
        custom_labels={"service": "example-label"}
    )
)
```

You can add as many metrics you like to the instrumentator.

### Creating new metrics

As already mentioned, it is possible to create custom functions to pass on to
`add()`. This is also how the default metrics are implemented.

The basic idea is that the instrumentator creates an `info` object that contains
everything necessary for instrumentation based on the configuration of the
instrumentator. This includes the raw request and response objects but also the
modified handler, grouped status code and duration. Next, all registered
instrumentation functions are called. They get `info` as their single argument.

Let's say we want to count the number of times a certain language has been
requested.

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
        for element in lang_str.split(","):
            element = element.split(";")[0].strip().lower()
            langs.add(element)
        for language in langs:
            METRIC.labels(language).inc()

    return instrumentation
```

The function `http_requested_languages_total` is used for persistent elements
that are stored between all instrumentation executions (for example the metric
instance itself). Next comes the closure. This function must adhere to the shown
interface. It will always get an `Info` object that contains the request,
response and a few other modified informations. For example the (grouped) status
code or the handler. Finally, the closure is returned.

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

Notice that this will do nothing if `should_respect_env_var` has been set during
construction of the instrumentator object and the respective env var is not
found.

### Specify namespace and subsystem

You can specify the namespace and subsystem of the metrics by passing them in
the instrument method.

```python
from prometheus_fastapi_instrumentator import Instrumentator

@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app, metric_namespace='myproject', metric_subsystem='myservice').expose(app)
```

Then your metrics will contain the namespace and subsystem in the metric name.

```sh
# TYPE myproject_myservice_http_request_duration_highr_seconds histogram
myproject_myservice_http_request_duration_highr_seconds_bucket{le="0.01"} 0.0
```

### Exposing endpoint

To expose an endpoint for the metrics either follow
[Prometheus Python Client](https://github.com/prometheus/client_python) and add
the endpoint manually to the FastAPI or serve it on a separate server. You can
also use the included `expose` method. It will add an endpoint to the given
FastAPI. With `should_gzip` you can instruct the endpoint to compress the data
as long as the client accepts gzip encoding. Prometheus for example does by
default. Beware that network bandwith is often cheaper than CPU cycles.

```python
instrumentator.expose(app, include_in_schema=False, should_gzip=True)
```

Notice that this will to nothing if `should_respect_env_var` has been set during
construction of the instrumentator object and the respective env var is not
found.

## Contributing

Please refer to [`CONTRIBUTING.md`](CONTRIBUTING).

Consult [`DEVELOPMENT.md`](DEVELOPMENT.md) for guidance regarding development.

Read [`RELEASE.md`](RELEASE.md) for details about the release process.

## Licensing

The default license for this project is the
[ISC License](https://choosealicense.com/licenses/isc). A permissive license
functionally equivalent to the BSD 2-Clause and MIT licenses, removing some
language that is no longer necessary. See [`LICENSE`](LICENSE) for the license
text.

The [BSD 3-Clause License](https://choosealicense.com/licenses/bsd-3-clause) is
used as the license for the
[`routing`](src/prometheus_fastapi_instrumentator/routing.py) module. This is
due to it containing code from
[elastic/apm-agent-python](https://github.com/elastic/apm-agent-python). BSD
3-Clause is a permissive license similar to the BSD 2-Clause License, but with a
3rd clause that prohibits others from using the name of the copyright holder or
its contributors to promote derived products without written consent. The
license text is included in the module itself.
