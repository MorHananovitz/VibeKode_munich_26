#!/usr/bin/env bash
# Context injection: print sprint standards and project conventions at session start.
# Fires on sessionStart. Output is shown to the agent as initial context.

CONTEXT_FILE="${CURSOR_PROJECT_ROOT:-.}/.cursor/sprint-context.md"

if [[ -f "$CONTEXT_FILE" ]]; then
  cat "$CONTEXT_FILE"
else
  printf 'No sprint-context.md found at %s.\n' "$CONTEXT_FILE"
  printf 'Create .cursor/sprint-context.md to inject standards, failure output, or sprint goals at session start.\n'
fi

exit 0
