#!/bin/sh

source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_dir="$(dirname "$source_dir")"

# ------------------------------------------------------------------------------

. "$source_dir/log.sh"

project_name="prometheus_fastapi_instrumentator"
