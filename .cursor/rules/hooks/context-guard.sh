#!/usr/bin/env bash
# Cost guard: warn the agent before reading files that exceed a size threshold.
# Fires on preToolUse (Read matcher). Fails open — never blocks the read.

set -euo pipefail

WARN_THRESHOLD_KB="${CONTEXT_GUARD_THRESHOLD_KB:-100}"

input=$(cat)
file_path=$(echo "$input" | jq -r '.input.path // .path // empty')

if [[ -z "$file_path" || ! -f "$file_path" ]]; then
  exit 0
fi

file_size_kb=$(( $(wc -c < "$file_path") / 1024 ))

if (( file_size_kb >= WARN_THRESHOLD_KB )); then
  msg="Large file warning: '${file_path}' is ${file_size_kb}KB (threshold: ${WARN_THRESHOLD_KB}KB). Reading it will consume significant context. Consider reading only the relevant section."
  printf '{"agent_message": %s}' "$(printf '%s' "$msg" | jq -Rs .)"
fi

exit 0
