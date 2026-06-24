#!/usr/bin/env bash
# Security: scan changed files for OWASP Top 10 patterns before a PR is created.
# Fires on beforeShellExecution when the command matches "gh pr create".
# Asks for confirmation when issues are found; allows the command when none are detected.

set -euo pipefail

input=$(cat)
command=$(echo "$input" | jq -r '.command // empty')

if [[ -z "$command" ]]; then
  printf '{"permission": "allow"}'
  exit 0
fi

if ! echo "$command" | grep -q "gh pr create"; then
  printf '{"permission": "allow"}'
  exit 0
fi

# Resolve the merge base against origin/main or origin/master to find all PR commits.
base=$(git merge-base HEAD origin/main 2>/dev/null \
  || git merge-base HEAD origin/master 2>/dev/null \
  || echo "HEAD~1")

# Collect added/modified files in the PR branch.
changed_files=$(git diff "$base" HEAD --name-only --diff-filter=AM 2>/dev/null || true)

if [[ -z "$changed_files" ]]; then
  printf '{"permission": "allow"}'
  exit 0
fi

findings=()

scan_file() {
  local file="$1"
  local content
  content=$(git show "HEAD:${file}" 2>/dev/null) || return

  # A03 - Injection: shell=True in subprocess calls
  if echo "$content" | grep -qE 'subprocess\.(run|Popen|call|check_output)\s*\(.*shell\s*=\s*True'; then
    findings+=("A03 Injection: shell=True in subprocess call in ${file}")
  fi

  # A03 - Injection: os.system usage
  if echo "$content" | grep -qE 'os\.system\s*\('; then
    findings+=("A03 Injection: os.system() found in ${file}")
  fi

  # A03 - Injection: eval/exec on potentially dynamic input
  if echo "$content" | grep -qE '^\s*(eval|exec)\s*\('; then
    findings+=("A03 Injection: eval()/exec() found in ${file}")
  fi

  # A03 - Injection: raw SQL string formatting
  if echo "$content" | grep -qE 'execute\s*\(\s*(f["\x27]|["\x27].*%s.*["\x27]\s*%|"\s*\+|format\s*\()'; then
    findings+=("A03 Injection: possible raw SQL string interpolation in ${file}")
  fi

  # A02 - Cryptographic Failures: weak hash algorithms
  if echo "$content" | grep -qiE 'hashlib\.(md5|sha1)\s*\('; then
    findings+=("A02 Cryptographic Failure: weak hash (MD5/SHA1) used in ${file}")
  fi

  # A02 - Cryptographic Failures: TLS verification disabled
  if echo "$content" | grep -qE 'verify\s*=\s*False'; then
    findings+=("A02 Cryptographic Failure: TLS verification disabled (verify=False) in ${file}")
  fi

  # A02 - Cryptographic Failures: plain HTTP URLs in code
  if echo "$content" | grep -qE '"http://[^l]|'"'"'http://[^l]'; then
    findings+=("A02 Cryptographic Failure: plain HTTP URL (non-localhost) in ${file}")
  fi

  # A05 - Security Misconfiguration: debug mode enabled
  if echo "$content" | grep -qiE 'DEBUG\s*=\s*True'; then
    findings+=("A05 Security Misconfiguration: DEBUG=True found in ${file}")
  fi

  # A05 - Security Misconfiguration: wildcard ALLOWED_HOSTS
  if echo "$content" | grep -qE "ALLOWED_HOSTS\s*=\s*\[.*['\"]?\*['\"]?.*\]"; then
    findings+=("A05 Security Misconfiguration: ALLOWED_HOSTS wildcard (*) in ${file}")
  fi

  # A05 - Security Misconfiguration: hardcoded secret key
  if echo "$content" | grep -qiE "SECRET_KEY\s*=\s*['\"][^'\"]{8,}['\"]"; then
    findings+=("A05 Security Misconfiguration: hardcoded SECRET_KEY in ${file}")
  fi

  # A07 - Identification/Auth Failures: hardcoded passwords
  if echo "$content" | grep -qiE 'password\s*=\s*["\x27][^"\x27]{4,}["\x27]'; then
    findings+=("A07 Auth Failure: hardcoded password literal in ${file}")
  fi

  # A08 - Software/Data Integrity: insecure deserialization
  if echo "$content" | grep -qE 'pickle\.loads?\s*\('; then
    findings+=("A08 Integrity Failure: pickle.load(s) used in ${file} — unsafe with untrusted data")
  fi

  # A08 - Software/Data Integrity: unsafe YAML loading
  if echo "$content" | grep -qE 'yaml\.load\s*\([^,)]*\)'; then
    if ! echo "$content" | grep -qE 'yaml\.load\s*\(.*Loader\s*='; then
      findings+=("A08 Integrity Failure: yaml.load() without explicit Loader in ${file}")
    fi
  fi

  # A10 - SSRF: requests with variable URL
  if echo "$content" | grep -qE 'requests\.(get|post|put|delete|patch|head)\s*\(\s*[^"\x27]'; then
    findings+=("A10 SSRF: requests call with dynamic URL in ${file} — validate the URL origin")
  fi

  # A01 - Broken Access Control: overly permissive file modes
  if echo "$content" | grep -qE 'os\.chmod\s*\(.*0o?777'; then
    findings+=("A01 Broken Access Control: chmod 777 in ${file}")
  fi
}

while IFS= read -r file; do
  [[ -z "$file" ]] && continue
  scan_file "$file"
done <<< "$changed_files"

if [[ ${#findings[@]} -eq 0 ]]; then
  printf '{"permission": "allow"}'
  exit 0
fi

# Build a readable findings list for the messages.
findings_text=""
for item in "${findings[@]}"; do
  findings_text+="- ${item}\n"
done

user_msg="OWASP Top 10 scan found ${#findings[@]} potential issue(s) in this PR:\n\n${findings_text}\nReview and resolve these before merging."
agent_msg="The owasp-check hook detected ${#findings[@]} OWASP Top 10 finding(s). Address them or confirm they are false positives before proceeding with the PR."

printf '{"permission": "ask", "user_message": %s, "agent_message": %s}' \
  "$(printf '%b' "$user_msg" | jq -Rs .)" \
  "$(printf '%b' "$agent_msg" | jq -Rs .)"
exit 0
