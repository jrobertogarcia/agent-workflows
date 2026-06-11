---
name: prepare-handover
description: Synthesizes completed implementation work, key technical decisions, and verification results into a structured handover package for review.
---

# Prepare Handover

1. **Synthesize Intent & Scope**: Consolidate the completed implementation work. Describe the core problem that was solved, the high-level architecture of the changes, and what was added or modified on this branch.
2. **Document Key Decisions & Trade-offs**: Detail the non-obvious engineering choices made during development. Explain *why* certain approaches were chosen over alternatives, noting any assumptions or constraints that influenced the design.
3. **Record Verification Evidence**: Document how the changes were validated. Provide clear evidence of correctness, including the results of automated test runs, linting checks, and manual verification scenarios.
4. **Identify Review Focus Areas**: Highlight complex modules, high-risk code paths, or specific files that the peer reviewer should inspect with extra attention.
5. **Output Handover Package**: Write this rich architectural context into a unified handover document (e.g., `<handover-file>.md`) at the root of the workspace to serve as the single source of truth for the incoming reviewer. Just leave the file there; do not commit it.
