#!/usr/bin/env bash
#
# security-utils.sh — Common security functions for agency-agents scripts
#
# Provides utilities for:
# - Input validation
# - Shell argument escaping
# - Credential protection
# - Secure defaults
#
# Usage:
#   source "$(dirname "$0")/security-utils.sh"
#   validateAgentName "my-agent"
#   escapedArg=$(escapeShellArg "$userInput")

set -euo pipefail

# Colors for output (respecting NO_COLOR)
if [[ -t 1 && -z "${NO_COLOR:-}" && "${TERM:-}" != "dumb" ]]; then
  RED=$'\033[0;31m'; YELLOW=$'\033[1;33m'; GREEN=$'\033[0;32m'; RESET=$'\033[0m'
else
  RED=''; YELLOW=''; GREEN=''; RESET=''
fi

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

# validateAgentName <name>
# Validates that an agent name contains only safe characters (lowercase, numbers, hyphens)
# Returns 0 if valid, 1 if invalid
validateAgentName() {
  local name="$1"
  if [[ ! "$name" =~ ^[a-z0-9_-]+$ ]]; then
    echo "${RED}[ERR]${RESET} Invalid agent name: \"$name\"" >&2
    echo "      Agent names must contain only lowercase letters, numbers, underscores, and hyphens." >&2
    return 1
  fi
  return 0
}

# validatePath <path> [<base_dir>]
# Validates that a path is safe (no directory traversal, optionally within base_dir)
# If base_dir is provided, ensures path resolves within it
# Returns 0 if valid, 1 if unsafe
validatePath() {
  local path="$1"
  local base_dir="${2:-.}"
  local canonical_path canonical_base

  # Reject paths with obvious traversal attempts
  if [[ "$path" =~ \.\. ]]; then
    echo "${RED}[ERR]${RESET} Path traversal detected: \"$path\"" >&2
    return 1
  fi

  # Reject absolute paths if not explicitly allowed
  if [[ "$path" =~ ^/ ]]; then
    echo "${RED}[ERR]${RESET} Absolute paths not allowed: \"$path\"" >&2
    return 1
  fi

  # Resolve canonical paths and validate containment
  canonical_path="$(cd "$(dirname "$path")" && pwd)/$(basename "$path")"
  canonical_base="$(cd "$base_dir" && pwd)"

  if [[ ! "$canonical_path" =~ ^"$canonical_base" ]]; then
    echo "${RED}[ERR]${RESET} Path escapes base directory: \"$path\"" >&2
    return 1
  fi

  return 0
}

# ============================================================================
# ESCAPING & SANITIZATION
# ============================================================================

# escapeShellArg <arg>
# Safely escapes a shell argument for use in commands
# Handles special characters and makes output safe for eval
escapeShellArg() {
  local arg="$1"
  # Use single quotes and escape any embedded single quotes
  # This is the safest approach for shell escaping
  echo "'${arg//\'/\'\\\'\'}'"
}

# sanitizeForLog <string>
# Removes or masks potentially sensitive information from log output
# Masks: API keys, tokens, passwords, email addresses
sanitizeForLog() {
  local string="$1"
  # Remove common secret patterns
  string="${string//\bgithub_token=[^[:space:]]*/github_token=***MASKED***}"
  string="${string//\btoken=[^[:space:]]*/token=***MASKED***}"
  string="${string//\bpassword=[^[:space:]]*/password=***MASKED***}"
  string="${string//\bAPI[_-]?KEY=[^[:space:]]*/API_KEY=***MASKED***}"
  echo "$string"
}

# ============================================================================
# CREDENTIAL & SECRET PROTECTION
# ============================================================================

# requireEnvVar <var_name> [<description>]
# Checks if an environment variable is set, exits with error if missing
# Useful for required secrets that must come from environment
requireEnvVar() {
  local var_name="$1"
  local description="${2:-$var_name}"
  local var_value

  var_value="${!var_name:-}"
  if [[ -z "$var_value" ]]; then
    echo "${RED}[ERR]${RESET} Required environment variable not set: $var_name" >&2
    echo "      Description: $description" >&2
    echo "      Set via: export $var_name=<value>" >&2
    return 1
  fi
  return 0
}

# requireNotFile <filename>
# Ensures a potentially dangerous file (e.g., .env, .credentials) does not exist
# Returns 0 if file doesn't exist, 1 if it does
requireNotFile() {
  local filename="$1"
  if [[ -f "$filename" ]]; then
    echo "${RED}[ERR]${RESET} Dangerous file found: \"$filename\"" >&2
    echo "      This file should not be committed or used in CI/CD." >&2
    echo "      Use environment variables instead." >&2
    return 1
  fi
  return 0
}

# ============================================================================
# COMMAND EXECUTION SAFETY
# ============================================================================

# validateCommand <command>
# Checks if a command exists and is executable
# Returns 0 if safe, 1 if missing
validateCommand() {
  local cmd="$1"
  if ! command -v "$cmd" &> /dev/null; then
    echo "${RED}[ERR]${RESET} Required command not found: $cmd" >&2
    return 1
  fi
  return 0
}

# safeExec <command> [<args...>]
# Executes a command with proper error handling
# Logs the command (with sanitization) and exits cleanly on error
safeExec() {
  local cmd=("$@")
  local sanitized
  
  sanitized=$(sanitizeForLog "${cmd[*]}")
  echo "${GREEN}[INFO]${RESET} Executing: $sanitized" >&2
  
  if ! "${cmd[@]}"; then
    echo "${RED}[ERR]${RESET} Command failed: $sanitized" >&2
    return 1
  fi
  return 0
}

# ============================================================================
# AUDIT & LOGGING
# ============================================================================

# logSecurityEvent <event_type> <message>
# Logs security-relevant events with timestamp
# Useful for audit trails
logSecurityEvent() {
  local event_type="$1"
  local message="$2"
  local timestamp
  timestamp=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
  echo "[${timestamp}] SECURITY [$event_type] $message" >&2
}

# requireGitClean
# Ensures git working directory is clean (no uncommitted changes)
# Useful before operations that assume a clean state
requireGitClean() {
  if [[ -d ".git" ]] && ! git diff-index --quiet HEAD --; then
    echo "${RED}[ERR]${RESET} Git working directory has uncommitted changes" >&2
    echo "      Please commit or stash changes before continuing." >&2
    return 1
  fi
  return 0
}

# ============================================================================
# DEFAULTS & BEST PRACTICES
# ============================================================================

# Apply strict error handling (already set at top, but documented here)
# set -euo pipefail
# - set -e: exit on any error
# - set -u: error on undefined variables  
# - set -o pipefail: propagate pipe failures

# When sourcing this file, consider adding:
# - Trap to clean up sensitive data on exit: trap "unset SENSITIVE_VAR" EXIT
# - Restrict file permissions: umask 077
# - Use readonly for constants: readonly AGENT_NAME

export SECURITY_UTILS_LOADED=1
