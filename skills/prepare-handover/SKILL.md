---
name: prepare-handover
description: Summarize completed work, key decisions, and verification evidence for a reviewer. Use at the end of an implementation thread.
---

# Prepare Handover

1. **Synthesize Intent & Scope**: Consolidate the completed implementation work. Describe the core problem that was solved, the high-level architecture of the changes, and what was added or modified on this branch.
2. **Document Key Decisions & Trade-offs**: Detail the non-obvious engineering choices made during development. Explain *why* certain approaches were chosen over alternatives, noting any assumptions or constraints that influenced the design.
3. **Record Verification Evidence**: Document how the changes were validated. Provide clear evidence of correctness, including the results of automated test runs, linting checks, and manual verification scenarios.
4. **Identify Review Focus Areas**: Highlight complex modules, high-risk code paths, or specific files that the peer reviewer should inspect with extra attention.
5. **Output Handover Package**: Present a structured, evidence-backed handover in the response, and write the same handover to `~/.agent-workflows/<repo>/<branch>/handover.md`, creating the directory as needed. `<repo>` is the basename of `git rev-parse --show-toplevel` and `<branch>` is `git rev-parse --abbrev-ref HEAD`. The file is the transport for the next thread; the response is for the human reading now.
   - One handover per branch: overwrite it on re-run rather than accumulating versions.
   - `git rev-parse --show-toplevel` resolves to the active worktree, so a worktree gets its own artifact directory and a handover written there is not found by a review thread run from the main checkout.
   - Report the absolute path written.
6. **Hand Off the Thread**: This package feeds `review-branch`, which runs in a fresh thread. State that as the next step.
