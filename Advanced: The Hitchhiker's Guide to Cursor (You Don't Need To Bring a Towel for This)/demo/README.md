# Demo: Code Review Mechanism Comparison

This demo was presented as part of the **Advanced: The Hitchhiker's Guide to Cursor** session.
It compared three distinct Cursor mechanisms for enforcing code review standards — each invoked
independently by a separate agent against the same buggy file — and then visualised the results
side-by-side in a Cursor Canvas.

---

## The Subject File

**`user_report.py`** — a deliberately broken Python script that fetches user activity from a REST
API, computes engagement scores, and writes a CSV report.

Every violation in the file is intentional and documented in **`user_report_issues.md`**. The full
catalogue covers eight categories:

| Category | Violations |
|---|---|
| `config` | Hardcoded API key, base URL, output path, and call-site team ID |
| `naming` | camelCase function names, non-`UPPER_SNAKE_CASE` constants, single-letter variables |
| `types` | All four public functions lack type annotations |
| `exceptions` | Bare `except` clause; broad `Exception` catch without chaining |
| `logging` | Seven `print()` calls used in place of the `logging` module |
| `SRP` | `calc` mixes score computation with direct CSV file I/O |
| `style` | Unused `import json`; `max_retries` defined but never used |
| `documentation` | Function-level docstrings and narrating code comments (project convention forbids both) |

---

## The Three Mechanisms Under Test

### 1. Rule — `.cursor/rules/code-review.mdc`

A passive, always-available context document. It is attached to every conversation that involves
a Python file and tells the model what to look for, but it does not prescribe a workflow. The
agent must decide on its own when and how to apply the checklist.

- Output saved to: `rules_cr/user_report_review.md`
- Findings: 11 issues across 6 categories

### 2. Command — `.cursor/commands/code-review.mdc`

An explicit slash command (`/code-review`) that runs a structured, step-by-step workflow. It
asks the user to select a scope (staged, branch, or specific file), collects the code, evaluates
it against six categories, and produces findings in a fixed format with a summary line.

- Output saved to: `commands_cr/user_report_review.md`
- Findings: 11 issues across 6 categories (with severity tiers: Critical / High / Medium / Low)

### 3. Skill — `.cursor/skills/code-review/SKILL.md`

A richer, project-aware checklist loaded on demand. It goes beyond the rule and command by also
checking documentation conventions (no function docstrings, no narrating comments) and design
concerns (modularity, over-engineering). It uses `[must-fix]` / `[suggestion]` / `[nit]` labels
and produces a severity-bucketed summary.

- Output saved to: `skills_cr/user_report_review.md`
- Findings: 17 issues (14 `must-fix`, 2 `suggestion`, 1 `nit`)

---

## What Each Mechanism Caught

| Issue | Rule | Command | Skill |
|---|:---:|:---:|:---:|
| Hardcoded `API_KEY` | yes | yes | yes |
| Hardcoded `base_url` / `output_file` | yes | yes | yes |
| Hardcoded team ID at call site | yes | yes | yes |
| `max_retries` never used | — | yes | yes |
| camelCase function names | yes | yes | yes |
| Single-letter variable names | yes | yes | yes |
| Module constants not `UPPER_SNAKE_CASE` | yes | yes | yes |
| Missing type annotations (all 4 functions) | yes | yes | yes |
| Bare `except` clause | yes | yes | yes |
| `except Exception` without chaining | yes | yes | yes |
| `KeyError` risk on `ev["type"]` | — | yes | — |
| `print` instead of `logging` (7 calls) | yes | yes | yes |
| `calc` violates SRP | yes | yes | yes |
| Unused `import json` | — | yes | yes |
| Function-level docstrings (project convention) | — | — | yes |
| Narrating code comments | — | — | yes |
| Non-descriptive function name `calc` | — | yes | yes |

---

## Canvas Comparison

After each agent run, the three outputs were loaded into a **Cursor Canvas** for a live
side-by-side comparison of depth, format, and coverage:

[View the canvas](https://cursor.com/dashboard/shared-canvases?shareId=canvas-YwkBF_lk9-E7EtI3Xmue3msp)

---

## Key Takeaways

- **Rules** provide ambient, zero-friction guidance but rely entirely on the model to self-apply them.
- **Commands** enforce a consistent workflow and output format; they are the most predictable for
  team-wide use and CI-adjacent checks.
- **Skills** offer the deepest coverage by layering project conventions (documentation, design)
  on top of the standard quality checks, at the cost of being the most complex to maintain.

No single mechanism caught every issue. The command uniquely flagged the `KeyError` risk on
`ev["type"]`; the skill uniquely flagged documentation and comment violations. Using a command
or skill — rather than relying on a passive rule — consistently produced more structured and
complete output.
