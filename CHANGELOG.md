# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

* Refactored available metrics. Made them more modular while improving 
    code structure.

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
    decimals as an opt-in feature. This can improve bytes per sample required in 
    storage solutions like VictoriaMetrics.

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
