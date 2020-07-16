# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
