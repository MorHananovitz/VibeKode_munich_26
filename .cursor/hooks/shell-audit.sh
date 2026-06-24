#!/usr/bin/env bash
# Observability: append every executed shell command to an audit log.
# Fires on afterShellExecution. Fails open — never blocks the agent.

AUDIT_LOG="${CURSOR_PROJECT_ROOT:-.}/.cursor/hooks/audit.log"

input=$(cat)
command=$(echo "$input" | jq -r '.command // empty')
exit_code=$(echo "$input" | jq -r '.exit_code // "unknown"')
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [[ -z "$command" ]]; then
  exit 0
fi

printf '[%s] exit=%s  %s\n' "$timestamp" "$exit_code" "$command" >> "$AUDIT_LOG" 2>/dev/null || true

exit 0
