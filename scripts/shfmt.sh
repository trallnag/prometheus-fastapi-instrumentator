#!/bin/sh

help() {
  cat << EOF
Wrapper for running shfmt.
EOF
}

case $1 in -h | --help | help) help && exit ;; esac

# shellcheck disable=SC1007
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

. "$script_dir/base.sh"

cd "$PROJECT_DIR" || exit 1

# ------------------------------------------------------------------------------

shfmt \
  --binary-next-line \
  --diff \
  --indent=2 \
  --keep-padding \
  --list \
  --posix \
  --simplify \
  --space-redirects \
  --write \
  scripts/*.sh
