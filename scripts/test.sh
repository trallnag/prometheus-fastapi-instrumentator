#!/bin/sh

help() {
    cat <<EOF
Run tests.

Options:
    -f, --fast, fast        Only run fast tests.
    -s, --slow, slow        Only run slow tests.
EOF
}

case $1 in -h|--help|help) help && exit ;; esac

source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_dir="$(dirname "$source_dir")"

. "$source_dir/main.sh"

# ------------------------------------------------------------------------------

set -eu

cd "$repo_dir"

_run_fast_tests() {
    loginfo "Run fast tests with Pytest."

    poetry run pytest -m "not slow" --cov=./ --cov-report=xml
}

_run_slow_tests() {
    loginfo "Run slow tests with Pytest."

    poetry run pytest -m "slow" --cov=./ --cov-report=xml
}

_run_tests() {
    _run_fast_tests
    _run_slow_tests
}

if [ $# -eq 1 ]; then
    case $1 in
        -f|--fast|fast)     _run_fast_tests ;;
        -s|--slow|slow)     _run_slow_tests ;;
        *)                  help
    esac
else
    _run_tests
fi
