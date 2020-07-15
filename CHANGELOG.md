# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Calendar Versioning](https://calver.org/).

## [Unreleased]

* Nothing

## [20.7.9]

### Added

* Explicit method to expose metrics by adding endpoint to an FastAPI app.
* This changelog document.

### Changed

* Split instrumentation and exposition into two parts. Why? There exist many 
    ways to expose metrics. Now this package enables the instrumentation of 
    FastAPI without enforcing a certain method of exposition. It is still 
    possible with the new method `expose()`.
* Moved pass of FastAPI object from constructor to `instrument()` method.
* Extended testing.

### Removed

* Exposition of metrics endpoint from `ìnstrument()` call.
* Contribution document. No need for it.

