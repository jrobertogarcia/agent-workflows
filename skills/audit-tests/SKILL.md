---
name: audit-tests
description: Audit an existing test suite for quality anti-patterns and produce a prioritized improvement plan. Use when test quality itself is the subject, not the tests for a specific change.
---

# Audit Tests

## Anti-Patterns
- **Tautological**: Assertions guaranteed to pass by definition, including re-deriving expected values from the production code under test.
- **Over-Mocking**: Excessive mocking where tests validate the framework or mock definitions instead of actual logic. Mock only true external boundaries and nondeterminism (time, randomness, generated IDs); do not mock the logic under test.
- **Incidental Coverage**: Weak or missing assertions written solely to hit execution lines for vanity metrics.
- **Assertion Roulette**: Multiple unlabelled assertions in a single test block, masking root causes upon failure.
- **Sleeping Tests**: Using arbitrary hardcoded pauses instead of explicit event or state polling.
- **Test Pollution**: Tests that pass or fail unpredictably based on execution order due to leaked shared state.
- **Ice Cream Cone**: Heavy reliance on end-to-end UI tests with anemic unit and integration coverage.
- **Duplicated Blocks**: Near-identical test blocks that differ only in inputs or expected outputs and should be consolidated via parametrization.

## Execution
1. **Enter Plan Mode**: Switch the session into plan mode (or the host's read-only planning equivalent) before reading anything, and stay in it until the plan is approved. If the host has no such mode, treat this run as read-only.
2. **Scope**: Establish which suite, package, or directory is under audit. Ask if it is ambiguous. Reuse context already gathered in this thread rather than re-reading it.
3. **Audit**: Read the tests in scope. Judge each against F.I.R.S.T. (Fast, Independent, Repeatable, Self-Validating, Timely) and whether it asserts observable behavior rather than internal implementation, recording concrete instances of the anti-patterns above with file and line references. Report the absence of a problem as readily as its presence. Name any area you could not assess rather than implying it passed.
4. **Prioritize**: Group the findings into Quick Wins (low effort, high impact), Core Enhancements (medium effort, high impact), and Structural (high effort, high impact, including overall test shape). Omit any group with no findings.
5. **Stop for Approval**: Present the audit and the plan, then wait for approval. Do not rewrite tests, change assertions, or add coverage. Create a file only when requested.
