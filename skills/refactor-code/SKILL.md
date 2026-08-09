---
name: refactor-code
description: Audit design problems and apply behavior-preserving cleanup after approval. Use when code needs restructuring without new behavior.
---

# Refactor Code

## Design Principles
- **SOLID**: Single responsibility, extension points, decoupled layers.
- **Coupling & Cohesion**: High internal cohesion, low external coupling.
- **Simplicity**: Eliminate dead code, premature abstractions (YAGNI/KISS).
- **Readability**: Self-documenting naming, clean control flows.

## Execution
1. **Audit & Plan**: Audit code smells in the target scope and present a structured refactoring plan. **Wait for user approval before modifying code.**
2. **Refactor**: Apply behavior-preserving restructures incrementally to the files under development or modification. Do not add new features or unrelated fixes.
3. **Verify**: Run build, lint, and test commands (e.g., running the project's standard compilation, linting, and testing suites) to confirm no behavioral regressions.
