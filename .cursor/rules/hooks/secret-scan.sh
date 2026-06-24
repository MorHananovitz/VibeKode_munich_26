#!/usr/bin/env bash
# Security: scan shell commands for secret patterns before execution.
# Fires on beforeShellExecution. Asks for confirmation on suspicious patterns.

set -euo pipefail

input=$(cat)
command=$(echo "$input" | jq -r '.command // empty')

if [[ -z "$command" ]]; then
  printf '{"permission": "allow"}'
  exit 0
fi

matched_pattern=""

# Generic high-entropy token patterns (API keys, passwords passed inline)
if echo "$command" | grep -qiE '(api[_-]?key|secret[_-]?key|access[_-]?token|password|passwd|auth[_-]?token)\s*=\s*["\x27]?[A-Za-z0-9+/]{16,}'; then
  matched_pattern="inline credential assignment"
fi

# AWS key patterns
if echo "$command" | grep -qE 'AKIA[0-9A-Z]{16}'; then
  matched_pattern="AWS access key"
fi

# Bearer tokens passed as arguments
if echo "$command" | grep -qiE -- '-H\s+["\x27]?Authorization:\s*Bearer\s+[A-Za-z0-9._-]{20,}'; then
  matched_pattern="Bearer token in HTTP header"
fi

if [[ -n "$matched_pattern" ]]; then
  message="Possible secret detected: ${matched_pattern}. Review the command before proceeding."
  printf '{"permission": "ask", "user_message": %s, "agent_message": %s}' \
    "$(printf '%s' "$message" | jq -Rs .)" \
    "$(printf '%s' "Hook flagged a potential secret in this shell command ($matched_pattern). Do not proceed unless the value is intentionally public." | jq -Rs .)"
  exit 0
fi

printf '{"permission": "allow"}'
exit 0
