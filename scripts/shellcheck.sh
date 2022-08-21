#!/bin/sh

help() {
  cat << EOF
Wrapper for running shellcheck.
EOF
}

case $1 in -h | --help | help) help && exit ;; esac

# shellcheck disable=SC1007
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

. "$script_dir/base.sh"

cd "$PROJECT_DIR" || exit 1

# ------------------------------------------------------------------------------

shellcheck \
  --check-sourced \
  --color=always \
  --format=tty \
  --shell=sh \
  --source-path=SCRIPTDIR \
  scripts/*.sh
