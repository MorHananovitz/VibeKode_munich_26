#!/usr/bin/env bash
# Quality gate: run ruff lint and format check on every edited Python file.
# Fires on afterFileEdit. Returns additional_context with any violations found.

set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.path // empty')

if [[ -z "$file_path" || "$file_path" != *.py ]]; then
  exit 0
fi

if [[ ! -f "$file_path" ]]; then
  exit 0
fi

lint_output=""
format_output=""

if command -v ruff &>/dev/null; then
  lint_output=$(ruff check "$file_path" 2>&1 || true)
  format_output=$(ruff format --check "$file_path" 2>&1 || true)
fi

if [[ -z "$lint_output" && -z "$format_output" ]]; then
  exit 0
fi

context=""
if [[ -n "$lint_output" ]]; then
  context+="RUFF LINT:\n${lint_output}\n"
fi
if [[ -n "$format_output" ]]; then
  context+="RUFF FORMAT:\n${format_output}\n"
fi

printf '{"additional_context": %s}' "$(printf '%s' "$context" | jq -Rs .)"
exit 0
