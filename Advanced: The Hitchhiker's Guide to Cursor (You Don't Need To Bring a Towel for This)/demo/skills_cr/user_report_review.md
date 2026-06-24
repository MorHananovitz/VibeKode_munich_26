# Code Review: user_report.py

Reviewed against project standards: type hints, ruff formatting, Google docstrings, error handling, modularity.

---

## Type Annotations

**[must-fix] Lines 18, 31, 58, 70:** No function has type annotations on parameters or return types.

```python
# current
def fetchUsers(teamId):
def calc(u, events):
def getEvents(userId):
def run_report(teamId):

# required
def fetch_users(team_id: str) -> list[dict]:
def calc_engagement(user: dict, events: list[dict]) -> float:
def get_events(user_id: str) -> list[dict]:
def run_report(team_id: str) -> None:
```

---

## Naming

**[must-fix] Line 18:** `fetchUsers` — must be `snake_case`. Use `fetch_users`.

**[must-fix] Line 31:** `calc` — not descriptive. Rename to `calc_engagement` or similar.

**[must-fix] Line 58:** `getEvents` — must be `snake_case`. Use `get_events`.

**[must-fix] Lines 34–36:** Single-letter variables `n`, `e`, `d` inside `calc` are not descriptive. Use `name`, `email`, `created_at`.

**[must-fix] Lines 84–88:** `u`, `uid`, `s` are non-descriptive. Use `user`, `user_id`, `score`.

**[must-fix] Lines 13–15:** `base_url`, `output_file`, `max_retries` are module-level constants but use `snake_case` instead of `UPPER_SNAKE_CASE`.

---

## Hardcoded Configuration

**[must-fix] Line 12:** `API_KEY` is hardcoded as a literal string. This is a secret and must come from an environment variable.

```python
# BAD
API_KEY = "sk-demo-abc123xyz"

# GOOD
import os
API_KEY = os.environ["API_KEY"]
```

**[must-fix] Line 13:** `base_url` is hardcoded. Must come from `os.environ["BASE_URL"]`.

**[must-fix] Line 14:** `output_file` is hardcoded. Must come from `os.environ["OUTPUT_FILE"]`.

---

## Exception Handling

**[must-fix] Line 26:** Bare `except` clause in `fetchUsers`. Catch a specific exception type and log with context.

```python
# BAD
except:
    print("Failed to fetch users")

# GOOD
except requests.HTTPError as exc:
    logger.error("Failed to fetch users: %s", exc)
```

**[must-fix] Line 65:** `except Exception` in `getEvents` silently swallows errors. Should catch `requests.HTTPError` or `requests.RequestException` specifically.

---

## Logging

**[must-fix] Lines 27, 54, 66, 71, 75, 91–92:** All runtime output uses `print`. The `logging` module must be used throughout.

```python
import logging

logger = logging.getLogger(__name__)

# replace every print(...) with:
logger.info(...)
logger.error(...)
```

---

## Single Responsibility

**[must-fix] Lines 31–55:** `calc` violates SRP — it computes an engagement score and writes a CSV row to disk in the same function. IO and business logic must be separated. The score calculation should be a pure function; the CSV write belongs in the caller (`run_report`).

---

## Documentation

**[must-fix] Lines 19, 32:** Function-level docstrings are present. Per project convention, no function-level docstrings are used — remove them.

**[suggestion] Lines 11, 34, 39–40, 49, 78:** Comments like `# pull fields`, `# count events`, `# write directly to disk...`, `# write CSV header` narrate what the code does. Remove them.

---

## Design

**[suggestion] Lines 95–96:** `run_report("team-42")` hardcodes the team ID at the entry point. Accept it from `sys.argv` or an environment variable instead.

**[nit] Line 8:** `import json` is unused — remove it.

---

## Summary

| Severity | Count |
|---|---|
| `must-fix` | 14 |
| `suggestion` | 2 |
| `nit` | 1 |

**Overall assessment:** The file has significant issues across every category. The most critical are the hardcoded secret (`API_KEY`), the bare `except`, pervasive use of `print` instead of `logging`, missing type annotations on all functions, non-`snake_case` function names, and a function (`calc`) that mixes computation with file IO. All `must-fix` items must be resolved before this file is production-ready.
