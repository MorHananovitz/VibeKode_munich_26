# Code Review: `user_report.py`

Reviewed against `.cursor/rules/code-review.mdc`.

---

## Issue 1 — Hardcoded API key secret

**Location**: line 12
**Category**: config
**Issue**: `API_KEY` contains a literal secret. This must never appear in source code.

```python
# BAD
API_KEY = "sk-demo-abc123xyz"

# GOOD
import os
API_KEY = os.environ["API_KEY"]
```

---

## Issue 2 — Hardcoded base URL and output path

**Location**: lines 13–14
**Category**: config
**Issue**: `base_url` and `output_file` are environment-specific values hardcoded in the module.

```python
# GOOD
BASE_URL = os.environ["ANALYTICS_BASE_URL"]
OUTPUT_FILE = os.environ.get("REPORT_OUTPUT_FILE", "/tmp/report.csv")
```

---

## Issue 3 — Non-constant naming for module-level constants

**Location**: lines 13–15
**Category**: naming
**Issue**: `base_url`, `output_file`, and `max_retries` are module-level constants but use `snake_case` instead of `UPPER_SNAKE_CASE`.

```python
# GOOD
BASE_URL = ...
OUTPUT_FILE = ...
MAX_RETRIES = 3
```

---

## Issue 4 — Function names use camelCase

**Location**: lines 18, 58
**Category**: naming
**Issue**: `fetchUsers` and `getEvents` use camelCase. Python functions must use `snake_case`.

```python
# GOOD
def fetch_users(team_id: str) -> list[dict]: ...
def get_events(user_id: str) -> list[dict]: ...
```

---

## Issue 5 — Missing type annotations on all functions

**Location**: lines 18, 31, 58, 70
**Category**: types
**Issue**: No function has parameter or return type annotations.

```python
# GOOD
def fetch_users(team_id: str) -> list[dict[str, object]]:
def calc(user: dict[str, object], events: list[dict[str, object]]) -> float:
def get_events(user_id: str) -> list[dict[str, object]]:
def run_report(team_id: str) -> None:
```

---

## Issue 6 — Bare `except` clause

**Location**: line 26
**Category**: exceptions
**Issue**: `except:` with no exception type catches everything including `SystemExit` and `KeyboardInterrupt`, and silently swallows all error context.

```python
# BAD
except:
    print("Failed to fetch users")

# GOOD
except requests.HTTPError as exc:
    logger.error("Failed to fetch users for team %s: %s", team_id, exc)
    return []
```

---

## Issue 7 — Exception caught but context discarded

**Location**: line 65
**Category**: exceptions
**Issue**: `except Exception` is caught but the exception object is discarded. The original traceback is lost and `print` is used instead of the logger.

```python
# GOOD
except requests.HTTPError as exc:
    logger.error("Could not load events for user %s: %s", user_id, exc)
    return []
```

---

## Issue 8 — `calc` violates single responsibility

**Location**: lines 31–55
**Category**: SRP
**Issue**: `calc` computes an engagement score AND writes a CSV row to disk. IO must be separated from business logic.

```python
# GOOD — split into two functions
def compute_engagement_score(user: dict, events: list[dict]) -> tuple[dict, float]:
    ...  # pure computation, no IO

def write_report_row(writer: csv.writer, row: list) -> None:
    ...  # only IO
```

---

## Issue 9 — Single-letter and cryptic variable names

**Location**: lines 31–88
**Category**: naming
**Issue**: `u`, `n`, `e`, `d`, `s`, `f` are not descriptive. Names must be readable at a glance.

```python
# BAD
n = u.get("name", "unknown")
s = calc(u, events)

# GOOD
name = user.get("name", "unknown")
score = compute_engagement_score(user, events)
```

---

## Issue 10 — `print` used for all runtime output

**Location**: lines 27, 54, 66, 71, 75, 91–92
**Category**: logging
**Issue**: `print` must not be used for operational output. All runtime messages must use the `logging` module.

```python
import logging

logger = logging.getLogger(__name__)

# GOOD
logger.info("Starting report generation...")
logger.warning("No users found for team %s, aborting.", team_id)
logger.info("Report complete. Users: %d, avg score: %.2f", len(scores), avg)
```

---

## Issue 11 — Hardcoded team ID at call site

**Location**: line 96
**Category**: config
**Issue**: The team ID `"team-42"` is hardcoded. It should be read from a CLI argument or environment variable.

```python
import sys

if __name__ == "__main__":
    team_id = sys.argv[1] if len(sys.argv) > 1 else os.environ["DEFAULT_TEAM_ID"]
    run_report(team_id)
```

---

## Summary

| # | Location | Category | Issue |
|---|----------|----------|-------|
| 1 | L12 | config | Hardcoded API key |
| 2 | L13–14 | config | Hardcoded base URL and output path |
| 3 | L13–15 | naming | Module constants use `snake_case` not `UPPER_SNAKE_CASE` |
| 4 | L18, 58 | naming | Function names use camelCase |
| 5 | L18, 31, 58, 70 | types | No type annotations on any function |
| 6 | L26 | exceptions | Bare `except:` clause |
| 7 | L65 | exceptions | Exception silently discarded, no logger context |
| 8 | L31–55 | SRP | `calc` mixes computation with file IO |
| 9 | L31–88 | naming | Single-letter and cryptic variable names |
| 10 | L27+ | logging | `print` used throughout instead of `logging` |
| 11 | L96 | config | Hardcoded team ID at call site |
