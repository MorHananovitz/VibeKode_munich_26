---
name: code-review
description: Review Python code in the current workspace against project standards (type hints, ruff formatting, Google docstrings, error handling, modularity). Use when the user asks to review code, check code quality, or audit a file or set of files in the workspace.
---

# Code Review

Review Python code against the project's standards. Use this for workspace files, not GitHub PRs (use `pr-code-review` for those).

## Workflow

1. Identify the files to review (ask the user if not specified).
2. Read each file in full.
3. Evaluate against the checklist below.
4. Report findings grouped by file, ordered by severity.

## Review Checklist

**Type Annotations**
- All functions, methods, and class members have type annotations.
- Types are as specific as possible (avoid `Any`, bare `dict`, `list` without generics).
- `typing` module used correctly (e.g., `Optional`, `Union`, `list[str]`, etc.).

**Code Quality**
- Descriptive snake_case names for variables and functions.
- No magic numbers or strings — use named constants.
- Single responsibility: functions and modules do one thing.
- No duplicated logic — reuse via functions or utilities.
- No bare `except` clauses; exception types are specific and informative.
- Logging uses the `logging` module, not `print`.

**Documentation**
- File-level Google-style docstring present and accurate.
- No function-level docstrings (project convention).
- No comments that narrate what the code does — only non-obvious intent or constraints.

**Error Handling**
- Exceptions are caught at the right level.
- Custom exception classes used where appropriate.
- Resources are cleaned up on failure.

**Style & Formatting**
- Ruff-compliant formatting and linting.
- No inline CSS (for UI files); styles in dedicated files.
- No hardcoded configuration — values come from environment variables.
- No emojis in code, comments, or output strings.

**Design**
- Modular: logic split across models, services, utilities as appropriate.
- No over-engineering; favors simplicity.
- Scalable schema design if database models are involved.

## Output Format

Group findings by file. For each issue, use:

- `[must-fix]` — violates project rules or correctness
- `[suggestion]` — improvement worth considering
- `[nit]` — minor style or naming

Example:

```
## src/services/user_service.py

[must-fix] Line 42: `process_data` has no return type annotation.
[must-fix] Line 78: Bare `except` clause — catch a specific exception type.
[suggestion] Line 55: `result` is too generic a variable name; prefer `user_records`.
[nit] Line 12: Unused import `os`.
```

End with a brief summary: total issues by severity and overall assessment.
