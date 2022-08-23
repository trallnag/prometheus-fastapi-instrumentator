# Changelog

## [5.9.1](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.9.0...v5.9.1) (2022-08-23)


### 🍀 Summary 🍀

No bug fixes or new features. Just an important improvement of the documentation.


### ✨ Highlights ✨

* Fix / Improve documentation of how to use package ([#168](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/168)). Instrumentation should happen in a function decorated with `@app.on_event("startup")` to prevent crashes on startup. Thanks to @mdczaplicki and others.


### CI/CD

* Pin poetry version and improve caching configuration ([6337459](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/6337459156a9cd87d868953e6c6c8dabea064eb1))


### Docs

* Improve example in README on how to instrument app ([#168](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/168)) ([dc36aac](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/dc36aac1a530faa3970b19c1c68be4ee18c7c34b))


## [5.9.0](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.8.2...v5.9.0) (2022-08-23)


### 🍀 Summary 🍀

This release fixes a small but annoying bug. Beyond that the release includes small internal improvements and bigger changes to CI/CD.


### ✨ Highlights ✨

* Removed print statement polluting logs ([#157](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/157)). Thanks to all the people raising this issue and to @nikstuckenbrock for fixing it.
* Added `py.typed` file to package to improve typing annotations ([#137](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/137)). Thanks to @mmaslowskicc for proposing and implementing this.
* Changed license from MIT to ISC, which is just like MIT but shorter.
* Migrated from Semantic Release to Release Please as release management tool.
* Overall refactoring of project structure to match my (@trallnag) template Python repo.
* Several improvements to the documentation. Thanks to @jabertuhin, @frodrigo, and @murphp15.
* Coding style improvements ([#155](https://github.com/trallnag/prometheus-fastapi-instrumentator/pull/155)). Replaced a few for loops with list comprehensions. Defaulting an argument to None instead of an empty list. Thanks to @yezz123.


### Features

* Add py.typed for enhanced typing annotations ([#37](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/37)) ([0c67d1b](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/0c67d1b8f51348979c00fd00d9457d3dd238df87))


### Bug Fixes

* Remove print statement from middleware ([#157](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/157)) ([f89792b](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/f89792b63d286e2ffd9241dc0b04c927f1102d07))


### Build

* **deps-dev:** bump devtools from 0.8.0 to 0.9.0 ([#172](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/172)) ([24bb060](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/24bb060a44b82b3b8d621d01af66dbd39773f2c7))
* **deps-dev:** bump flake8 from 4.0.1 to 5.0.4 ([#179](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/179)) ([8f72053](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/8f7205320ed648ef07fa21d7f699cf06cef3d4eb))
* **deps-dev:** bump mypy from 0.950 to 0.971 ([#174](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/174)) ([60e324f](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/60e324fb24f262f01f3d36be38c4e5e705523425))


### Docs

* Add missing colon to README ([#33](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/33)) ([faef24c](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/faef24c5aa4794cf1564ba871b15b736de303a86))
* Adjust changelog formatting ([b8b7b3e](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/b8b7b3ea2319947d8d5f9b8fb10c559267838516))
* Fix small typo in readme ([#154](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/154)) ([a569d4e](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/a569d4e58147a707c43e0fb698457c7ec7e13150))
* Move docs-internal to docs/devel and adjust contributing ([1b446ca](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/1b446ca3283514dcfbdaf9a1c5aa0f3a031ace45))
* Remove obsolete DEVELOPMENT.md ([1c18ff7](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/1c18ff72df97892680c9da7c0193997c6795dc83))
* Switch license from MIT to ISC ([1b0294a](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/1b0294ac03b3369cae9b6cc675b9c94e1a4c0d76))


### CI/CD

* Add .tool-versions ([255ba97](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/255ba97ee3dfbdada5fe300362b2725c075da0f8))
* Add codecov.yaml ([008ef61](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/008ef6136eba8d133a69de6f15ff14c39966fa2f))
* Add explicit codecov token ([b264184](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/b264184cea3bfdb318fb007ed0972814a41014eb))
* Adjust commitlint to allow more subject case types ([8b630aa](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/8b630aa2734696effe78e95ab638b08fb594c908))
* Correct default branch name ([5f141c5](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/5f141c59cc1b34b4cdbb2a77ba0edfc6c757356e))
* Improve and update scripts ([e1d9982](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/e1d998213b811c20f09e9c717efd2a97165b7939))
* Move to Release Please and refactor overall CI approach ([9977665](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/99776659515910a7c1369bcc7db916d440590ee7))
* Remove flake8 ignore W503 ([6eab3b8](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/6eab3b87fac913cf36b0266255304a917dec7b4f))
* Remove traces of semantic-release ([f0ab8ff](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/f0ab8ff070b620e5c9e6f69b3e5111e52f830427))
* Remove unnecessary include of py.typed from pyproject.toml ([#37](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/37)) ([bbad45e](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/bbad45ec1ab5baa0aca02e06857ee97ad466ab19))
* Rename poetry repo for TestPyPI ([3f1c500](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/3f1c500a69e90300056b7098b7a85ebe3efc19b5))
* Restructure poetry project layout ([b439ceb](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/b439ceb073703804156fcd42734cae3c7ffee59e))
* Update gitignore ([e0fa528](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/e0fa5286f841daac6486c0c3758c7edc1c30796e))
* Update pre-commit config ([e725750](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/e72575009fc628e9ccc8f39b74b16cd2028dd1f8))


### Refactor

* Improve coding style ([#155](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/155)) ([623d83b](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/623d83b86278d2627084b9fe9547f1af07531042))


## [5.8.2](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.8.1...v5.8.2) (2022-06-12)

Refactored the middleware to an ASGI implementation ([#139](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/139)). Thanks to @Kludex and @adriangb for the proposal and implementation.


## [5.8.1](https://github.com/trallnag/prometheus-fastapi-instrumentator/compare/v5.8.0...v5.8.1) (2022-05-03)

Fixed a regression that made the required FastAPI version too strict for no reason ([#136](https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/136)) ([36bc045](https://github.com/trallnag/prometheus-fastapi-instrumentator/commit/36bc045c5eb247fa7a83c25cc161f95b5d4b314d)). Thanks to @graipher for raising this issue.
