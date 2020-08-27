# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

* Nothing

## [5.2.1] 2020-08-27

### Fixed

* Fix for <https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/7>.
    If a run time error is raised inside the endpoint, FastAPI will not wrap 
    the error in a response object. In addition this instrumentator assumed 
    that `info.response` will always contain the `headers` attribute which is 
    not the case if a runtime error is thrown. Now the metrics check if the 
    response is `None` and that the `headers` attribute actually exists. Tests 
    have been added as well.

### Changed

* Metrics `response_size` and `combined_size` no longer skip if content length 
    is not found. Now the content length will default no zero bytes.

## [5.2.0] 2020-08-22

### Added

* Parameter `should_only_respect_2xx_for_highr` to `default` metrics. Allows 
    you to only put successful requests into the high resolution bucket.

## [5.1.0] 2020-08-19

### Added

* Parameters to set namespace and subsystem to all available metrics.

## [5.0.0] 2020-08-18

### Changed

* Rename instrumentation `full` to `default`.
* Add labels `handler`, `status`, `method` to `http_requests_total` in `default`.
* Rename `http_in_bytes_total` to `http_request_size_bytes`.
* Add label `handler` to `http_request_size_bytes`.
* Rename `http_out_bytes_total` to `http_response_size_bytes`.
* Add label `handler` to `http_response_size_bytes`.
* Rename `http_highr_request_duration_seconds` to 
    `http_request_duration_highr_seconds`.
* Rename `http_lowr_request_duration_seconds` to `http_request_duration_seconds`.
* Remove labels `method` and `status` from `http_request_duration_seconds`.
* Turn `http_request_size_bytes` and `http_response_size_bytes` 
    into summaries.

## [4.0.0] 2020-08-16

* Refactored available metrics. Made them more modular while improving 
    code structure.
* Switched the default fast track metric to a more advanced one.
* Added proper documentation.

## [3.0.0] 2020-08-15

A lot of breaking changes in this release. Prometheus FastAPI Instrumentator 
is now more modular than before and there are multiple different metrics 
one can choose from out of the box or add custom metrics that will be 
automatically applied to the FastAPI.

### Changed

* If you just use the default instrumentator without setting any parameters, 
    nothing changes. The defaults stay the same.
* If you use any of the paramters that were available in the Instrumentator 
    constructor you have to check if they are still available or not. Some of 
    them have been moved to the corresponding `metric` closure / function. I 
    recommend to go through the updated documentation.
* Endpoint `/metrics` is not excluded by default anymore.
* Updated `README.md`.

## [2.0.1] 2020-08-14

### Changed

* Fixed wrong var name in `README.md`.

## [2.0.0] 2020-08-14

### Added

* Option to exclude optional `/metrics` endpoint from schema.

### Changed

* Renamed `should_respect_env_var_existence` to `should_respect_env_var`.
* If `should_respect_env_var` is `True`, the respective env var must be `true` 
    and not just any random value.
* Renamed default env var if `should_respect_env_var` from `PROMETHEUS` to 
    `ENABLE_METRICS`.

## [1.3.0] 2020-08-12

### Added

* Option `should_respect_env_var_existence`. 
    * This makes it possible to only instrument and expose your FastAPI if a 
        given environment variable is set. 
    * Usecase: A base FastAPI app that is used by multiple distinct apps. The 
        apps only have to set the variable to be instrumented.
    * Deactivated by default and the default env var is `PROMETHEUS`.

## [1.2.0] 2020-08-06

### Added

* The observed latency values can now be rounded to a certain number of 
    decimals as an opt-in feature. This can improve bytes per sample required 
    in storage solutions like VictoriaMetrics.

## [1.1.1] 2020-07-19

* Nothing

## [1.1.0] 2020-07-16

### Changed

* Renamed project from *Prometheus FastAPI Exporter* to 
    *Prometheus FastAPI Instrumentator*. Reasoning behind this change: Focus of 
    this project is the instrumentation, not exposition of metrics.

## [1.0.2] 2020-07-15

### Changed

* Updated README.md

## [1.0.1] 2020-07-15

### Changed

* Updated README.md

## [1.0.0] 2020-07-15

### Added

* Explicit method to expose metrics by adding endpoint to an FastAPI app.
* This changelog document.

### Changed

* Switch to SemVer versioning.
* Split instrumentation and exposition into two parts. Why? There exist many 
    ways to expose metrics. Now this package enables the instrumentation of 
    FastAPI without enforcing a certain method of exposition. It is still 
    possible with the new method `expose()`.
* Moved pass of FastAPI object from constructor to `instrument()` method.
* Extended testing.

### Removed

* Exposition of metrics endpoint from `ìnstrument()` call.
* Contribution document. No need for it.

## [20.7.8] [YANKED]

## [20.7.7] [YANKED]

## ... [YANKED]

## Unreleased

* Nothing
