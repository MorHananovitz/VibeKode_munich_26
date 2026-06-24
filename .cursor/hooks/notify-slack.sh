#!/usr/bin/env bash
# Notifications: post a Slack message when the agent finishes a run.
# Fires on stop. Reads SLACK_WEBHOOK_URL from the environment.
# Fails open — missing webhook is not an error.

input=$(cat)
summary=$(echo "$input" | jq -r '.summary // "Agent run completed."')
project=$(basename "${CURSOR_PROJECT_ROOT:-.}")
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [[ -z "${SLACK_WEBHOOK_URL:-}" ]]; then
  exit 0
fi

payload=$(jq -n \
  --arg text "*[${project}]* Agent run finished at ${timestamp}" \
  --arg summary "$summary" \
  '{text: $text, blocks: [{type: "section", text: {type: "mrkdwn", text: $text}}, {type: "section", text: {type: "mrkdwn", text: $summary}}]}')

curl -s -o /dev/null -X POST \
  -H "Content-Type: application/json" \
  -d "$payload" \
  "$SLACK_WEBHOOK_URL" || true

exit 0
