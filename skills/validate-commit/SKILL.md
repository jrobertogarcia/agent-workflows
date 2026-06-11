---
name: validate-commit
description: Comprehensive verification workflow to ensure code is ready for commit and passes all commit checks and hooks.
---

# Validation Workflow

Run this workflow before concluding a task or when validation is requested to prevent commit hooks from failing.

1. **Automated Fixes**: Format and fix automated violations.
   - Run the project's formatting and linting auto-fixers (e.g., linters, formatters, code cleaners).

2. **CI-Parity Health Check**: Run the main build, lint, and test validation checks.
   - Run the project's standard compilation and test suites to mimic remote CI execution.

3. **Resolution & Completion**: Resolve any failures immediately. If formatting errors exist outside of touched files, fix them to unblock the PR commit queue. Only consider a task ready for submission when a 100% green (Exit 0) status is achieved.
