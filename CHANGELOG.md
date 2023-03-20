# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0),
and adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0).

## Unreleased

Nothing.

## [6.0.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.11.2...v6.0.0) / 2023-03-20

Small release with a small breaking change leading to an increase of the major
version according to semantic versioning.

Breaking change only affects users that have custom instrumentations that access
`info.response.body`, a feature introduced with [5.10.0](#5100--2023-02-26) few
weeks ago. See below for more information.

Ask or discuss anything quick about the release in the discussion
[#239](https://github.com/trallnag/prometheus-fastapi-instrumentator/discussions/239).

### Added

- **BREAKING:** Disabled passing response body to instrumentation functions.
  Moved behind whitelist that is empty by default. Changes a feature introduced
  with [5.10.0](#5100--2023-02-26). Only affects users that have custom
  instrumentations that access `info.response.body`.

  Opt-in via new parameter `body_handlers` added to instrumentator constructor.
  Parameter takes list of pattern strings to match handlers. For old behavior,
  pass argument `[r".*"]` to match all handlers:

  ```python
  instrumentator = Instrumentator(body_handlers=[r".*"])
  ```

  Motivation for change: Collecting body negatively impacts performance of
  responses with largish body.

  Thanks to [@bbeattie-phxlabs](@bbeattie-phxlabs) for raising this issue in
  [#234](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/234)
  and implementing it in
  [#233](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/233)
  /
  [#238](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/238).

## [5.11.2](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.11.1...v5.11.2) / 2023-03-19

## Fixed

- Fixed `info.response.body` in instrumentation functions being wrongfully empty
  if response is not streamed. Affects a feature that was introduced with
  release [5.10.0](#5100--2023-02-26) few weeks ago. Closed issue
  [#236](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/236)
  and implemented in pull request
  [#237](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/237).

## [5.11.1](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.11.0...v5.11.1) / 2023-03-11

### Fixed

- Improved typing hints and enabled stricter rules for MyPy. Thanks to
  [@tomtom103](https://github.com/tomtom103) for implementing this in
  [#231](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/231).

## [5.11.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.10.0...v5.11.0) / 2023-03-08

Minor release containing several fixes and a small enhancement. Fixes are
related to multi process mode, a regression introduced with the previous
release, and errors that started to occur with current versions of Starlette and
FastAPI.

Ask or discuss anything quick about the release in the discussion
[#221](https://github.com/trallnag/prometheus-fastapi-instrumentator/discussions/221).

### Added

- Adjusted the `add()` method to accept an arbitrary number of instrumentation
  functions as arguments instead of a single one. Non-breaking change.
  Implemented in pull request
  [#230](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/230).

### Fixed

- Fixed multi process mode in `expose()` method that handles the `/metrics`
  endpoint. Due to reusing the registry assigned to the instrumentator it could
  lead to duplicated metrics. Now the endpoint follows recommendation from
  Prometheus client library documentation. Also improved multi process unit
  tests. Closed issue
  [#228](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/228)
  and
  [#227](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/227).
  Fixed in pull request
  [#229](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/229).

- Fixed `NameError` and "Duplicated timeseries..." errors that started to occur
  with latest versions of Starlette / FastAPI in combination with multiple
  middlewares. Instrumentation closures are now optional and the instrumentator
  handles this accordingly. Thanks to [@alexted](https://github.com/alexted) and
  others for reporting errors. Thanks to
  [@frankie567](https://github.com/frankie567) for pointing out the change in
  Starlette. Related to pull request
  [#153](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/153)
  and issue
  [#214](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/214).
  Closed issue
  [#219](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/219).
  Done in pull request
  [#220](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/220).

- Added missing `registry` parameter to remaining metrics functions. This
  enables passing custom registry to other metrics functions than default.
  Related to pull request
  [#153](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/153).
  Closed issue
  [#219](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/219).
  Done in pull request
  [#220](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/220).

## [5.10.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.9.1...v5.10.0) / 2023-02-26

First release in several months. Includes new features and fixes from various
contributors. Notable changes that might have an impact on existing setups is
the automatic instrumentation of mounted apps and the deprecation of the
lowercase `prometheus_multiproc_dir` environment variable.

Ask or discuss anything quick about the release in the discussion
[#221](https://github.com/trallnag/prometheus-fastapi-instrumentator/discussions/221).

### Added

- Added smart **handling of mounted apps**. Previously the URL handler logic did
  not handle mounted apps and always returned just the prefix in that case.
  Based on code from
  [elastic/apm-agent-python](https://github.com/elastic/apm-agent-python)
  licensed under the permissive BSD-3-Clause License. Thanks to
  [@LordGaav](https://github.com/LordGaav) for proposing this enhancement / fix
  and implementing it in
  [#208](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/208).
  Related to issues
  [#31](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/31)
  and
  [#121](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/121).

- Added optional parameters `metric_namespace` and `metric_subsystem` to
  `instrument()` method to **configure namespace and subsystem** for all metric
  names. Check the [`README.md`](README.md#specify-namespace-and-subsystem) for
  more information. Thanks to [@phbernardes](https://github.com/phbernardes) for
  proposing this enhancement and implementing it in
  [#193](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/193).

- Added **passthrough of body** to `info.response`. This enables metrics that
  work based on data in the body. Thanks to everyone who brought this up in
  [#76](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/76)
  and to [@HadilD](https://github.com/HadilD) for implementing it in
  [#203](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/203).

- Allowed **passing a custom registry** to be used instead of using the default
  one. This would be useful in particular when testing multiple FastAPI apps
  (e.g. microservices) in the same tests run. Note that there are issues with
  the current implementation in certain corner cases. Thanks to
  [@tiangolo](https://github.com/tiangolo) for proposing this enhancement and
  implementing it in
  [#153](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/153).

- Environment variable used by `should_respect_env_var` (default
  `ENABLE_METRICS`) now **accepts truthy values** like `1` and `true` and not
  just `True`. Thanks to [@chbndrhnns](https://github.com/chbndrhnns) for
  proposing this enhancement in
  [#27](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/27)
  and implementing it in
  [#28](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/28).

- Added support for **asynchronous instrumentation functions**. The `add()`
  method now accepts them in addition to "normal" functions and the
  instrumentator middleware will await them appropriately. Thanks to
  [@AndreasPB](https://github.com/AndreasPB) for proposing this enhancement and
  implementing it in
  [#61](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/61).
  Thanks to [@Skeen](https://github.com/Skeen) for contributing to the
  discussion.

### Changed

- Licensed part of the project under the BSD-3-Clause License. This is due to
  code being used from a repo licensed under BSD-3-Clause (see the "Added"
  section). The default ISC License and the BSD-3-Clause License are both
  permissive. So there should be no user impact.

### Fixed

- Fixed status code in metric being "Hxx" when `http.HTTPStatus` enumeration is
  used in combination with grouping of status codes. Thanks to
  [@Leem0sh](https://github.com/Leem0sh) and others for raising the issue in
  [#190](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/190).
  Thanks to [@nikstuckenbrock](https://github.com/nikstuckenbrock) and
  [@blag](https://github.com/blag) for fixing it in
  [#192](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/192).

- Fixed documentation in main README on how to use
  prometheus-fastapi-instrumentator with current versions of FastAPI. Related to
  issues
  [#214](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/214)
  and
  [#80](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/80).
  Thanks to [@alfaro28](https://github.com/alfaro28) and
  [@harochau](https://github.com/harochau).

### Deprecated

- Deprecated environment variable `prometheus_multiproc_dir` and replaced it
  with `PROMETHEUS_MULTIPROC_DIR`. This matches the behavior of the Prometheus
  Python client library. This fixes
  [#89](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/89)
  and
  [#50](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/50).
  Thanks to all the people who brought this up. Thanks to
  [@michaelusner](https://github.com/michaelusner) for implementing the
  deprecation in
  [#42](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/42) /
  [#217](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/217).

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
