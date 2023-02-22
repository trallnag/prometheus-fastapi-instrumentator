# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0),
and adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0).

## Unreleased

### Added

- Added smart handling of mounted apps. Previously the URL handler logic did not
  handle mounted apps and always returned the prefix in that case. This is based
  on code from
  [elastic/apm-agent-python](https://github.com/elastic/apm-agent-python)
  licensed under the permissive BSD-3-Clause License. Thanks to
  [@LordGaav](https://github.com/LordGaav) for proposing this enhancement and
  implementing it in
  [#208](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/208).
- Added optional parameters `metric_namespace` and `metric_subsystem` to
  `instrument()` method to configure namespace and subsystem for all metric
  names. Check the [`README.md`](README.md#specify-namespace-and-subsystem) for
  more information. Thanks to [@phbernardes](https://github.com/phbernardes) for
  proposing this enhancement and implementing it in
  [#193](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/193).
- Added passthrough of body to `info.response`. This enables metrics that work
  based on data in the body. Thanks to everyone who brought this up in
  [#76](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/76)
  and to [@HadilD](https://github.com/HadilD) for implementing it in
  [#203](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/203).

### Changed

- Licensed part of the project under the BSD-3-Clause License. This is due to
  code being used from a repo licensed under BSD-3-Clause (see the "Added"
  section). The default ISC License and the BSD-3-Clause License are permissive.

### Fixed

- Fixed status code in metric being "Hxx" when `http.HTTPStatus` enumeration is
  used in combination with grouping of status codes. Thanks to
  [@Leem0sh](https://github.com/Leem0sh) and others for raising the issue in
  [#190](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/190).
  Thanks to [@nikstuckenbrock](https://github.com/nikstuckenbrock) and
  [@blag](https://github.com/blag) for fixing it in
  [#192](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/192).

## [5.9.1](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.9.0...v5.9.1) / 2022-08-23

### Fixed

- Corrected documention on how to use package. Instrumentation should happen in
  a function decorated with `@app.on_event("startup")` to prevent crashes on
  startup in certain situations. Done in
  [#168](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/168).
  Thanks to [@mdczaplicki](https://github.com/mdczaplicki) and others.

## [5.9.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.8.2...v5.9.0) / 2022-08-23

### Added

- Added `py.typed` file to package to improve typing annotations. Done in
  [#137](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/137).
  Thanks to [@mmaslowskicc](https://github.com/mmaslowskicc) for proposing and
  implementing this.

### Changed

- Changed license from MIT to ISC, which is just like MIT but shorter.
- Coding style improvements. Replaced a few for loops with list comprehensions.
  Defaulting an argument to `None` instead of an empty list. Done in
  [#155](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/155).
  Thanks to [@yezz123](https://github.com/yezz123).
- Several improvements to the documentation. Thanks to
  [@jabertuhin](https://github.com/jabertuhin),
  [@frodrigo](https://github.com/frodrigo), and
  [@murphp15](https://github.com/murphp15).

### Fixed

- Removed print statement polluting logs. Done in
  [#157](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/157).
  Thanks to [@nikstuckenbrock](https://github.com/nikstuckenbrock) and others.

## [5.8.2](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.8.1...v5.8.2) / 2022-06-12

### Changed

- Refactored the middleware to an ASGI implementation. Related to
  [#139](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/139).
  Thanks to [@Kludex](https://github.com/Kludex) and
  [@adriangb](https://github.com/adriangb) for the proposal and implementation.

## [5.8.1](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.8.0...v5.8.1) / 2022-05-03

### Fixed

- Fixed a regression that made the required FastAPI version too strict for no
  reason. Related to
  [#136](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/136).
  Thanks to [@graipher](https://github.com/graipher) for raising this issue.

## [5.8.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.7.1...v5.8.0) / 2022-05-01

### Removed

- **BREAKING:** Dropped support for Python 3.6 which is has reached end-of-life.

## [5.7.1](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.7.0...v5.7.1) / 2021-01-12

### Fixed

- Updated `prometheus-client` dependency version constraint `^0.8.0` that only
  allows versions in the range `[0.8.0, 0.9.0[`. This is not correct and leads
  to conflicts when you want to install the newest prometheus client library
  version and this package. Switched to explicit contraints to ensure this does
  not happen again.

## [5.7.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.6.0...v5.7.0) / 2020-12-13

## Added

- Added passthrough of Kwargs to FastAPI route that exposes metrics.

## [5.6.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.5.1...v5.6.0) / 2020-12-03

### Added

- Added parameter `tags` to method `expose()`. Passthrough to FastAPI to support
  tagging. Related to
  [#17](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/17).
  Thanks to [@chisaipete](https://github.com/chisaipete) for proposing this
  enhancement.

## [5.5.1](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.5.0...v5.5.1) / 2020-11-13

### Fixed

- Fixed error "Duplicate mime type charset=utf-8 on Response Header". Done by
  changing the way the content type header is set. Seems like when Starlette's
  `media_type` parameter is used to provide content type, the charset is
  appended again automatically even if it already is part of `Content-Type`.
  Thanks to [@flobaader](https://github.com/flobaader) for raising this issue in
  [#16](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/16).

## [5.5.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.4.1...v5.5.0) / 2020-11-01

### Added

- Added new metrics closure `requests`. Thanks to
  [@jpslopes](https://github.com/jpslopes) for proposing this enhancement in
  [#15](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/15).

### Changed

- Adjusted docstrings.

## [5.4.1](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.4.0...v5.4.1) / 2020-10-22

### Fixed

- Fixed dependency regression introduced in 5.4.0 by pinning FastAPI dependency
  to `fastapi = "0.38.1, <=1.0.0"` instead of `fastapi = ">=0.38.1, <=1.0.0"`.
  Thanks to [@PaulFlanaganGenscape](https://github.com/PaulFlanaganGenscape) for
  raising this issue in
  [#14](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/14).

## [5.4.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.3.1...v5.4.0) / 2020-10-20

### Added

- Added new metric that monitors the number of requests in progress. Can be
  configured to have the labels `handler` and `method`. It can be activated with
  `should_instrument_requests_inprogress` and configured with `inprogress_name`
  and `inprogress_labels`.

## [5.3.1](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.3.0...v5.3.1) / 2020-09-25

### Fixed

- Fixed `expose` method in the instrumentator ignoring the `endpoint` argument
  and always creating the endpoint with on the `/metrics` path. Variable was
  missing. Thanks to [@funkybase](https://github.com/funkybase) for raising this
  issue in
  [#9](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/9).

## [5.3.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.2.3...v5.3.0) / 2020-09-09

### Added

- Added parameter `should_gzip` to `expose` method. It will check for `gzip` in
  the `Accepted-Encoding` header and gzip the metrics data. You can expect a
  reduction of around 90 % in bytes.

## [5.2.3](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.2.2...v5.2.3) / 2020-09-03

### Changed

- Improved `README.md`.

## [5.2.2](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.2.1...v5.2.2) / 2020-09-03

### Changed

- Improved `README.md`.

## [5.2.1](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.2.0...v5.2.1) / 2020-08-27

### Fixed

- Fixed lack of error wrapping of a runtime error is raised inside the endpoint.
  In addition this instrumentator assumed that `info.response` will always
  contain the `headers` attribute which is not the case if a runtime error is
  thrown. Now the metrics check if the response is `None` and that the `headers`
  attribute actually exists. Tests have been added as well. Thanks to
  [@stepf](https://github.com/stepf) for raising this issue in
  [#7](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/7).

### Changed

- Adjusted behavior Metrics `response_size` and `combined_size` no longer skip
  if content length is not found. Now the content length will default no zero
  bytes.

## [5.2.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.1.0...v5.2.0) / 2020-08-22

### Added

- Added parameter `should_only_respect_2xx_for_highr` to `default` metrics.
  Allows you to only put successful requests into the high resolution bucket.

## [5.1.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.0.0...v5.1.0) / 2020-08-19

### Added

- Added parameters to set namespace and subsystem to all available metrics.

## [5.0.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v4.0.0...v5.0.0) / 2020-08-18

### Added

- Added labels `handler`, `status`, `method` to `http_requests_total` in
  `default`.
- Added label `handler` to `http_request_size_bytes`.
- Added label `handler` to `http_response_size_bytes`.

### Changed

- **BREAKING:** Renamed instrumentation `full` to `default`.
- **BREAKING:** Renamed `http_in_bytes_total` to `http_request_size_bytes`.
- **BREAKING:** Renamed `http_out_bytes_total` to `http_response_size_bytes`.
- **BREAKING:** Renamed `http_highr_request_duration_seconds` to
  `http_request_duration_highr_seconds`.
- **BREAKING:** Renamed `http_lowr_request_duration_seconds` to
  `http_request_duration_seconds`.
- **BREAKING:** Turned `http_request_size_bytes` and `http_response_size_bytes`
  into summaries.

### Removed

- **BREAKING:** Removed labels `method` and `status` from
  `http_request_duration_seconds`.

## [4.0.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v3.0.0...v4.0.0) / 2020-08-16

### Added

- Added proper documentation.

### Changed

- **BREAKING:** Switched the default fast track metric to a more advanced one.
- **BREAKING:** Reworked available metrics. Made them more modular while
  improving code structure.

## [3.0.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v2.0.1...v3.0.0) / 2020-08-15

A lot of breaking changes in this release. Prometheus FastAPI Instrumentator is
now more modular than before and there are multiple different metrics one can
choose from out of the box or add custom metrics that will be automatically
applied to the FastAPI.

If you just use the default instrumentator without setting any parameters,
nothing changes. The defaults stay the same.

If you use any of the paramters that were available in the Instrumentator
constructor you have to check if they are still available or not. Some of them
have been moved to the corresponding `metric` closure / function.

### Changed

- **BREAKING:** Endpoint `/metrics` is not excluded by default anymore.
- **BREAKING:** Rework instrumentator layout.

## [2.0.1](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v2.0.0...v2.0.1) / 2020-08-14

### Changed

- Fixed wrong var name in `README.md`.

## [2.0.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v1.3.0...v2.0.0) / 2020-08-14

### Added

- Added option to exclude optional `/metrics` endpoint from schema.

### Changed

- **BREAKING:** Renamed `should_respect_env_var_existence` to
  `should_respect_env_var`.
- **BREAKING:** If `should_respect_env_var` is `True`, the respective env var
  must be `true` and not just any random value.
- **BREAKING:** Renamed default env var if `should_respect_env_var` from
  `PROMETHEUS` to `ENABLE_METRICS`.

## [1.3.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v1.2.0...v1.3.0) / 2020-08-12

### Added

- Added option `should_respect_env_var_existence`. This makes it possible to
  only instrument and expose your FastAPI if a given environment variable is
  set. Use case: A base FastAPI app that is used by multiple distinct apps. The
  apps only have to set the variable to be instrumented. Deactivated by default
  and the default env var is `PROMETHEUS`.

## [1.2.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v1.1.1...v1.2.0) / 2020-08-06

### Added

- The observed latency values can now be rounded to a certain number of decimals
  as an opt-in feature. This can improve bytes per sample required in storage
  solutions like VictoriaMetrics.

## [1.1.1](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v1.1.0...v1.1.1) / 2020-07-19

Nothing. Dummy release.

## [1.1.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v1.0.2...v1.1.0) / 2020-07-16

### Changed

- Renamed project from *Prometheus FastAPI Exporter* to *Prometheus FastAPI
  Instrumentator*. Reasoning behind this change: Focus of this project is the
  instrumentation, not exposition of metrics.

## [1.0.2](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v1.0.1...v1.0.2) / 2020-07-15

### Changed

- Updated README.md

## [1.0.1](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v1.0.0...v1.0.1) / 2020-07-15

### Changed

- Updated README.md

## [1.0.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/1d4421f66e0e3600e3607f353cf183096bc09304...v1.0.0) / 2020-07-15

### Added

- Explicit method to expose metrics by adding endpoint to an FastAPI app.

### Changed

- **BREAKING:** Switched to semantic versioning. All older versions have been
  yanked.
- **BREAKING:** Split instrumentation and exposition into two parts. Why? There
  exist many ways to expose metrics. Now this package enables the
  instrumentation of FastAPI without enforcing a certain method of exposition.
  It is still possible with the new method `expose()`.
- **BREAKING:** Moved pass of FastAPI object from constructor to `instrument()`
  method.

### Removed

- **BREAKING:** Exposition of metrics endpoint from `ìnstrument()` call.
