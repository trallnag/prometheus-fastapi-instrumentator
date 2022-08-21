#!/bin/sh

# shellcheck disable=SC1007
script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

# ------------------------------------------------------------------------------

. "$script_dir/log.sh"

PROJECT_DIR="$(dirname "$script_dir")"
export PROJECT_DIR

PACKAGE_NAME=prometheus_fastapi_instrumentator
export PACKAGE_NAME
