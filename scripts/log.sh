#!/bin/sh

# ------------------------------------------------------------------------------

# Logsh. A minimal POSIX compliant logging library.
#
# Usage:
#   Either source the content of this file or just place it directly
#   into your own script. Several functions will be available to you.
#
#   - logdebug
#   - loginfo
#   - logsuccess
#   - logwarning
#   - logerror
#   - logexit
#
# Configuration:
#   Logging is configured via environment variables.
#
#   LOGSH_COLOR:
#     Can either be 'true' or 'false' and defaults to 'true'. Only
#     respected while sourcing logsh. This means you can only
#     switch between 'true' and 'false' by resourcing the script.
#
#   LOGSH_LEVEL:
#     Integer ranging from 0 to 4. Defaults to 3. If the log
#     message level is lower or equal to the selected level,the
#     log message wil be written to stderr. Here are the mappings
#     from integers to text levels:
#
#     0=ERROR
#     1=WARNING
#     2=SUCCESS
#     3=INFO
#     4=DEBUG
#
# Source Repository:
#   https://github.com/trallnag/logsh

# ------------------------------------------------------------------------------

if [ "${LOGSH_COLOR:-true}" = "true" ]; then
  _logsh_default_color='\033[0m'
  _logsh_debug_color='\033[36m'
  _logsh_info_color='\033[34m'
  _logsh_success_color='\033[32m'
  _logsh_warn_color='\033[33m'
  _logsh_error_color='\033[31m'
else
  _logsh_default_color=
  _logsh_debug_color=
  _logsh_info_color=
  _logsh_success_color=
  _logsh_warn_color=
  _logsh_error_color=
fi

log() {
  text="$1"
  level="$2"
  level_as_text="$3"
  color="$4"

  if [ "$level" -le "${LOGSH_LEVEL:-3}" ]; then
    printf '%b[%s] %s%b\n' "$color" "$level_as_text" "$text" "$_logsh_default_color" >&2
  fi
}

logexit() { log "$1" 0 "ERROR" "$_logsh_error_color" && exit 1; }

logerror() { log "$1" 0 "ERROR" "$_logsh_error_color"; }

logwarning() { log "$1" 1 "WARNING" "$_logsh_warn_color"; }

logsuccess() { log "$1" 2 "SUCCESS" "$_logsh_success_color"; }

loginfo() { log "$1" 3 "INFO" "$_logsh_info_color"; }

logdebug() { log "$1" 4 "DEBUG" "$_logsh_debug_color"; }

# ------------------------------------------------------------------------------
