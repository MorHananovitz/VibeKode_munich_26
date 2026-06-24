# user_report.py — Intentional Code Review Issues

This file documents every deliberate violation in `user_report.py`.
Use it to verify that the code review rule, command, and skill each catch the expected findings.

---

## config — Hardcoded configuration values

**Lines 13–16**

```python
API_KEY = "sk-demo-abc123xyz"
base_url = "https://analytics.internal.mycompany.com:8080"
output_file = "/tmp/report.csv"
max_retries = 3
```

All four values are hardcoded. They must come from environment variables (e.g. `os.environ["API_KEY"]`).

---

## naming — camelCase function names

**Line 20:** `fetchUsers` — must be `fetch_users`

**Line 44:** `getEvents` — must be `get_events`

---

## naming — Non-descriptive / single-letter variable names

**Lines 29–31 (inside `calc`):** `n`, `e`, `d` — should be `name`, `email`, `created_at`

**Line 28:** `u` (parameter) — should be `user`

**Line 57:** `s` — should be `score`

**Line 65:** `r` (inside `fetchUsers`) — named `r` in the original draft; kept as a short alias

---

## naming — Constant not in UPPER_SNAKE_CASE

**Line 16:** `max_retries = 3` — module-level constant should be `MAX_RETRIES`

---

## types — Missing type annotations

None of the four public functions carry type annotations.

| Function | Expected signature |
|---|---|
| `fetchUsers(teamId)` | `def fetch_users(team_id: str) -> list[dict]` |
| `calc(u, events)` | `def calc(user: dict, events: list[dict]) -> float` |
| `getEvents(userId)` | `def get_events(user_id: str) -> list[dict]` |
| `run_report(teamId)` | `def run_report(team_id: str) -> None` |

---

## exceptions — Bare `except` clause

**Lines 26–28 (inside `fetchUsers`):**

```python
except:
    print("Failed to fetch users")
    return []
```

Catches every possible exception including `KeyboardInterrupt` and `SystemExit`. Must use a specific type and chain the original error.

---

## exceptions — `Exception` caught without chaining

**Lines 50–52 (inside `getEvents`):**

```python
except Exception:
    print(f"Could not load events for user {userId}")
    return []
```

Two problems: `Exception` is too broad when `requests.HTTPError` is available, and there is no `from exc` chaining to preserve the original traceback.

---

## logging — `print()` used for runtime output

The `logging` module must be used instead of `print`. Occurrences:

| Line | Statement |
|---|---|
| 25 | `print("Failed to fetch users")` |
| 39 | `print(f"Processed user {n}: score={score}")` |
| 43 | `print(f"Could not load events for user {userId}")` |
| 59 | `print("Starting report generation...")` |
| 64 | `print("No users found, aborting.")` |
| 68 | `print(f"Report complete. ...")` |
| 69 | `print(f"Output written to {output_file}")` |

---

## SRP — `calc` mixes business logic with file I/O

**Lines 28–43**

`calc` both computes an engagement score (business logic) and writes a CSV row directly to disk (I/O). These are two separate responsibilities and must be split into distinct functions.

```python
# business logic only
def compute_score(logins: int, purchases: int) -> float:
    return (logins * 1.0) + (purchases * 5.0)

# I/O only
def write_row(writer: csv.writer, user: dict, logins: int, purchases: int, score: float) -> None:
    writer.writerow([user["name"], user["email"], user["created_at"], logins, purchases, score])
```
