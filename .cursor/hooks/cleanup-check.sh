#!/usr/bin/env bash
# Cleanup: scan the workspace for stray console.logs and temp files after a run.
# Fires on stop. Returns a followup_message listing findings for the agent to address.

set -euo pipefail

ROOT="${CURSOR_PROJECT_ROOT:-.}"

console_log_files=()
temp_files=()

while IFS= read -r -d '' f; do
  console_log_files+=("$f")
done < <(grep -rl --include="*.py" --include="*.js" --include="*.ts" \
  -E 'console\.(log|warn|error|debug)\(' "$ROOT" \
  --exclude-dir=".git" --exclude-dir="node_modules" --exclude-dir=".cursor" \
  -Z 2>/dev/null || true)

while IFS= read -r -d '' f; do
  temp_files+=("$f")
done < <(find "$ROOT" -maxdepth 4 \
  \( -name "*.tmp" -o -name "*.bak" -o -name "debug_*.py" -o -name "test_scratch*" \) \
  -not -path "*/.git/*" -not -path "*/node_modules/*" \
  -print0 2>/dev/null || true)

if [[ ${#console_log_files[@]} -eq 0 && ${#temp_files[@]} -eq 0 ]]; then
  exit 0
fi

msg=""

if [[ ${#console_log_files[@]} -gt 0 ]]; then
  msg+="Stray console.log/warn/error calls found in:\n"
  for f in "${console_log_files[@]}"; do
    msg+="  - ${f#$ROOT/}\n"
  done
  msg+="\n"
fi

if [[ ${#temp_files[@]} -gt 0 ]]; then
  msg+="Temp/scratch files found:\n"
  for f in "${temp_files[@]}"; do
    msg+="  - ${f#$ROOT/}\n"
  done
fi

printf '{"followup_message": %s}' "$(printf '%b' "$msg" | jq -Rs .)"
exit 0
