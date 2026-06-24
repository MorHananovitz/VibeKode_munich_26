---
name: pr-code-review
description: Performs a thorough code review on a GitHub pull request by checking out the PR locally, analyzing the diff in full repository context, and posting inline review comments via the GitHub MCP tool requesting changes. Use when the user wants to review a PR, provides a GitHub pull request URL, or asks for a code review on a pull request.
---

# PR Code Review

## Overview

Full code review workflow: fetch the PR, analyze it deeply in repo context, post inline comments via GitHub MCP with `REQUEST_CHANGES`.

---

## Step 1 — Parse the PR URL

Extract `owner`, `repo`, and `pull_number` from the URL.

Pattern: `https://github.com/{owner}/{repo}/pull/{pull_number}`

---

## Step 2 — Fetch the PR locally (bash only)

```bash
gh pr checkout {PR_URL}
```

Then collect the diff and context:

```bash
# Full diff of the PR
gh pr diff {PR_URL}

# PR metadata
gh pr view {PR_URL}

# Head commit SHA (needed for create_pull_request_review)
gh pr view {PR_URL} --json headRefOid --jq '.headRefOid'
```

---

## Step 3 — Gather full context via GitHub MCP

Call these MCP tools in parallel:

1. `get_pull_request` — get PR description, title, base branch, head commit SHA
2. `get_pull_request_files` — get the list of changed files with their patches (diffs)

Then for each changed file, read its **full content** from the local checkout using the Read tool to understand surrounding code, not just the diff hunk.

Also explore related files (imported modules, tests, types, configs) to understand the full impact of changes.

---

## Step 4 — Analyze the changes

Review every changed file against all dimensions below. For each issue found, record:
- `path`: relative file path
- `line`: the line number in the **new version** of the file
- `body`: a clear, actionable comment

### Review dimensions

**Security**
- Injection risks (SQL, command, path traversal, template injection)
- Exposed secrets, API keys, tokens, or credentials
- Missing input validation or sanitization
- Authentication/authorization checks bypassed or missing
- Insecure deserialization, unsafe use of `eval`/`exec`
- Sensitive data logged or returned in responses

**Logic & Correctness**
- Off-by-one errors, incorrect boundary conditions
- Unhandled null/None/undefined cases
- Race conditions or concurrency issues
- Incorrect assumptions about data types or formats
- Missing early returns or guard clauses
- Business logic that contradicts the PR description

**Error Handling**
- Exceptions swallowed silently
- Generic catch-all handlers hiding real errors
- Missing error propagation to the caller
- No cleanup on failure (resources, locks, temp files)

**Clean Code**
- Functions doing more than one thing (violates SRP)
- Duplicated logic that should be extracted
- Names that are misleading, too generic (`data`, `temp`, `result`), or abbreviated
- Magic numbers or strings without named constants
- Deeply nested conditionals that could be flattened

**Parameters & Interfaces**
- Parameters that are too broad (accepting `any`, `dict`, `object`) when a specific type is possible
- Boolean parameters that should be separate functions
- Long parameter lists that should be grouped into an object/dataclass
- Optional parameters with surprising defaults
- Public API changes that break backward compatibility

**Tests**
- Tests that assert implementation details rather than behavior
- Missing test cases for the happy path, edge cases, or error cases
- Tests that never actually fail (always pass even if the code is wrong)
- Mocks that are too permissive or incorrect
- Test descriptions that don't match what the test actually does
- Missing tests for the new code added in this PR

**Comments & Documentation**
- Comments that describe *what* the code does instead of *why*
- Comments that are outdated and no longer match the code
- Missing docstrings on public functions/classes introduced or modified
- TODO/FIXME left without context (no ticket, no explanation)

**Performance**
- N+1 query patterns (database calls inside loops)
- Unnecessary copies of large data structures
- Missing indexes or inefficient lookups
- Synchronous blocking calls that should be async

**Consistency**
- Style inconsistencies with the rest of the codebase
- Different patterns used for the same problem elsewhere in the repo
- Imports or dependencies not aligned with project conventions

---

## Step 5 — Post the review via GitHub MCP

Use `create_pull_request_review` with:
- `event`: `"REQUEST_CHANGES"` if any critical or significant issues found; `"COMMENT"` if only minor suggestions
- `body`: A high-level summary — what the PR does, overall assessment, key concerns, what must be addressed before merging
- `comments`: Array of inline comments, each with `path`, `line`, and `body`

### Comment body format

Each inline comment should be:
- Specific and actionable — explain what to change and ideally how
- Categorized at the start:
  - `[security]` — must fix
  - `[bug]` — must fix  
  - `[logic]` — must fix
  - `[test]` — must fix
  - `[suggestion]` — consider improving
  - `[nit]` — minor style/naming

Example comments:
```
[security] This query is vulnerable to SQL injection. Use parameterized queries: `cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))`

[bug] `user_list` can be None here if the API returns null, which will cause an AttributeError on the next line. Add a null check or default to an empty list.

[test] This test will always pass because `mock_send.return_value` is never checked after calling `process()`. Assert that `mock_send.assert_called_once_with(expected_payload)`.

[suggestion] The parameter `flag` is a boolean that changes the behavior completely. Consider splitting this into two functions: `process_with_validation()` and `process_without_validation()` to make call sites more readable.
```

### Summary body format

```
## Review Summary

**PR**: {title}

**Assessment**: {one sentence overall verdict}

### Must fix before merge
- {critical issue 1}
- {critical issue 2}

### Suggestions
- {suggestion 1}

### What looks good
- {positive feedback}
```

---

## Step 6 — Verify the review was posted

After calling `create_pull_request_review`, confirm success and tell the user:
- The review was posted with N inline comments
- The PR URL where they can see the review
- A brief summary of the most critical issues found
