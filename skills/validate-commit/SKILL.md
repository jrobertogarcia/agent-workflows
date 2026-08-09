---
name: validate-commit
description: Run formatters, linters, build, and tests to confirm code is ready to commit. Use before committing.
model: sonnet
effort: low
---

# Validate Commit

Run this workflow before concluding a task or when validation is requested to prevent commit hooks from failing.

1. **Automated Fixes**: Fix automated violations within the requested scope.
   - Run the project's formatting and linting auto-fixers (e.g., linters, formatters, code cleaners).

2. **CI-Parity Health Check**: Run the main build, lint, and test validation checks.
   - Run the project's standard compilation and test suites to mimic remote CI execution.

3. **Resolution & Completion**: Resolve in-scope failures and report unrelated failures without modifying them. Require all in-scope checks to pass before submission.
