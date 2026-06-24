# Code Review: `user_report.py`

> Reviewed with `/code-review` command against the project Python and code-review rules.

Issues are ordered by severity.

---

## CRITICAL

### 1. Hardcoded secret — Line 12

- **Category:** config
- **Issue:** `API_KEY` is a real-looking secret embedded directly in source code. This will be committed to version control and is a security risk.
- **Fix:**
```python
import os
API_KEY = os.environ["API_KEY"]
```

---

## HIGH

### 2. Bare `except` clause — Line 26

- **Category:** exceptions
- **Issue:** `except:` swallows every possible exception including `SystemExit`, `KeyboardInterrupt`, and `MemoryError`. The real error is silently discarded.
- **Fix:**
```python
except requests.exceptions.RequestException as exc:
    logger.error("Failed to fetch users for team %s: %s", team_id, exc)
    return []
```

### 3. Single Responsibility violation in `calc` — Lines 31–55

- **Category:** SRP
- **Issue:** `calc` does three unrelated things: it extracts user fields, computes an engagement score, and performs file I/O by appending directly to a CSV. This makes the function untestable in isolation and couples score logic to a specific output path.
- **Fix:** Split into two functions — one that computes and returns a `dict` row, and one that handles writing.

### 4. Hardcoded configuration — Lines 13–15

- **Category:** config
- **Issue:** `base_url`, `output_file`, and `max_retries` are module-level hardcoded values. They must come from environment variables.
- **Fix:**
```python
BASE_URL = os.environ["ANALYTICS_BASE_URL"]
OUTPUT_FILE = os.environ.get("REPORT_OUTPUT_FILE", "/tmp/report.csv")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
```

### 5. `KeyError` risk on event dict access — Lines 42, 44

- **Category:** exceptions
- **Issue:** `ev["type"]` will raise `KeyError` if any event dict is missing the `"type"` key (e.g. malformed API response). No validation is performed on the response shape.
- **Fix:**
```python
event_type = ev.get("type")
if event_type == "login":
    logins += 1
elif event_type == "purchase":
    purchases += 1
```

---

## MEDIUM

### 6. Missing type annotations on all functions — Lines 18, 31, 58, 70

- **Category:** types
- **Issue:** No function has parameter or return type annotations. This is required by the project standard.
- **Fix:**
```python
def fetch_users(team_id: str) -> list[dict]:
    ...

def get_events(user_id: str) -> list[dict]:
    ...

def calculate_engagement_score(user: dict, events: list[dict]) -> float:
    ...

def run_report(team_id: str) -> None:
    ...
```

### 7. `print` used throughout instead of `logging` — Lines 27, 54, 71, 75, 91, 92

- **Category:** logging
- **Issue:** All runtime output uses `print`. The project standard requires the `logging` module for observability and log level control.
- **Fix:**
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Starting report generation...")
logger.warning("No users found, aborting.")
logger.error("Failed to fetch users")
```

### 8. Naming convention violations — Lines 18, 31, 58

- **Category:** naming
- **Issue:**
  - `fetchUsers` and `getEvents` are camelCase; Python functions must be `snake_case`.
  - `teamId` and `userId` are camelCase parameters; must be `team_id` and `user_id`.
  - `calc` is too short and non-descriptive; rename to `calculate_engagement_score`.
  - Module-level values `base_url`, `output_file`, `max_retries` are constants and must be `UPPER_SNAKE_CASE`.
  - Single-letter variables `n`, `e`, `d`, `r`, `u`, `s`, `f` are non-descriptive.

---

## LOW

### 9. Unused import — Line 7

- **Category:** style
- **Issue:** `import json` is present but never used.
- **Fix:** Remove the import.

### 10. `max_retries` defined but never used — Line 15

- **Category:** style
- **Issue:** `max_retries = 3` is defined but retry logic is never implemented. Either implement it or remove the variable.

### 11. Hardcoded `team_id` at call site — Line 96

- **Category:** config
- **Issue:** `run_report("team-42")` hardcodes the team ID at the entry point. It should be supplied via CLI argument or environment variable.
- **Fix:**
```python
if __name__ == "__main__":
    import sys
    team_id = sys.argv[1] if len(sys.argv) > 1 else os.environ["TEAM_ID"]
    run_report(team_id)
```

---

## Summary

| Severity | Count | Categories |
|----------|-------|------------|
| Critical | 1     | config (hardcoded secret) |
| High     | 4     | exceptions, SRP, config, exceptions |
| Medium   | 3     | types, logging, naming |
| Low      | 3     | style, style, config |

The two most urgent fixes are the **hardcoded API key** (security) and the **bare `except`** (silent failure masking). The **`calc` SRP violation** is the most important structural issue — it makes the score logic impossible to unit test in isolation.
