#!/usr/bin/env bash
# Security: block destructive shell commands before execution.
# Fires on beforeShellExecution. Denies rm -rf and git force-push patterns.

set -euo pipefail

input=$(cat)
command=$(echo "$input" | jq -r '.command // empty')

if [[ -z "$command" ]]; then
  printf '{"permission": "allow"}'
  exit 0
fi

# Block rm -rf variants
if echo "$command" | grep -qE 'rm\s+-[a-zA-Z]*r[a-zA-Z]*f|rm\s+-[a-zA-Z]*f[a-zA-Z]*r'; then
  printf '%s' '{
    "permission": "deny",
    "user_message": "Blocked: rm -rf detected. Use targeted file removal instead.",
    "agent_message": "Hook blocked this command: rm -rf is not permitted. Remove files individually or use a safer alternative."
  }'
  exit 0
fi

# Block git force-push
if echo "$command" | grep -qE 'git\s+(push|p)\s+.*(-f|--force|--force-with-lease)'; then
  printf '%s' '{
    "permission": "deny",
    "user_message": "Blocked: git force-push detected. Rewrite history only after explicit user approval.",
    "agent_message": "Hook blocked this command: force-push rewrites remote history. Ask the user before proceeding."
  }'
  exit 0
fi

printf '{"permission": "allow"}'
exit 0
