---
name: prepare-handover
description: Summarize completed work, key decisions, and verification evidence for a reviewer. Use at the end of an implementation thread.
---

# Prepare Handover

1. **Synthesize Intent & Scope**: Consolidate the completed implementation work. Describe the core problem that was solved, the high-level architecture of the changes, and what was added or modified on this branch.
2. **Document Key Decisions & Trade-offs**: Detail the non-obvious engineering choices made during development. Explain *why* certain approaches were chosen over alternatives, noting any assumptions or constraints that influenced the design.
3. **Record Verification Evidence**: Document how the changes were validated. Provide clear evidence of correctness, including the results of automated test runs, linting checks, and manual verification scenarios.
4. **Identify Review Focus Areas**: Highlight complex modules, high-risk code paths, or specific files that the peer reviewer should inspect with extra attention.
5. **Output Handover Package**: Present a structured, evidence-backed handover in the response, and write the same handover to `~/.agent-workflows/<repo>/<branch>/handover.md`, where `<repo>` is `basename(dirname(git rev-parse --path-format=absolute --git-common-dir))` and `<branch>` is `git branch --show-current`, creating directories as needed. Stop and say so when `git branch --show-current` is empty.
   - Record the tip only when the working tree is clean; otherwise stop and say the evidence would cover uncommitted changes. Make the first line `Branch tip: <SHA>`, the full `git rev-parse HEAD` output that the verification evidence covers.
   - Overwrite on re-run and report the absolute path written.

