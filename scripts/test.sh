#!/bin/sh

help() {
    cat << EOF
Wrapper for running tests with Pytest.

- Includes code coverage report generation.
- Used within GitHub Actions workflows.
- Used for local and interactive development.

Options:
  -f, --fast, fast    Only run fast tests.
  -s, --slow, slow    Only run slow tests.
EOF
}

case $1 in -h | --help | help) help && exit ;; esac

# shellcheck disable=SC1007
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

. "$script_dir/base.sh"

cd "$PROJECT_DIR" || exit 1

# ------------------------------------------------------------------------------

_run_fast_tests() {
  loginfo "Running only fast tests with Pytest..."

  poetry run pytest \
    --cov-report=term-missing:skip-covered \
    --cov-report=xml \
    --cov=src/$PACKAGE_NAME \
    -m "not slow" \
    tests/
}

_run_slow_tests() {
  loginfo "Running only slow tests with Pytest..."

  poetry run pytest \
    --cov-report=term-missing:skip-covered \
    --cov-report=xml \
    --cov=src/$PACKAGE_NAME \
    -m "slow" \
    tests/
}

_run_all_tests() {
  loginfo "Running all tests with Pytest..."

  poetry run pytest \
    --cov-report=term-missing:skip-covered \
    --cov-report=xml \
    --cov=src/$PACKAGE_NAME \
    tests/
}

if [ $# -eq 1 ]; then
  case $1 in
  -f | --fast | fast) _run_fast_tests ;;
  -s | --slow | slow) _run_slow_tests ;;
  *) help ;;
  esac
else
  _run_all_tests
fi
