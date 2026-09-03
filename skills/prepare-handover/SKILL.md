---
name: prepare-handover
description: Summarize completed work, key decisions, and verification evidence for a reviewer. Use at the end of an implementation thread.
---

# Prepare Handover

1. **Synthesize Intent & Scope**: Consolidate the completed implementation work. Describe the core problem that was solved, the high-level architecture of the changes, and what was added or modified on this branch.
2. **Document Key Decisions & Trade-offs**: Detail the non-obvious engineering choices made during development. Explain *why* certain approaches were chosen over alternatives, noting any assumptions or constraints that influenced the design.
3. **Record Verification Evidence**: Document how the changes were validated. Provide clear evidence of correctness, including the results of automated test runs, linting checks, and manual verification scenarios.
4. **Identify Review Focus Areas**: Highlight complex modules, high-risk code paths, or specific files that the peer reviewer should inspect with extra attention.
5. **Output Handover Package**: Present a structured, evidence-backed handover in the response, and write the same handover to `~/.agent-workflows/<repo>/<branch>/handover.md`, creating the directory as needed. The file is the transport for `review-branch`, which reads it in a fresh thread; the response is for the human reading now.
   - `~` expands to the home directory; resolve it before writing.
   - `<repo>` is `basename(dirname(git rev-parse --path-format=absolute --git-common-dir))`, so a repository and all of its worktrees share one key.
   - `<branch>` is `git branch --show-current`. When that is empty the checkout is on a detached HEAD, so ask where to write instead of keying on an ambiguous value.
   - One handover per branch: overwrite it on re-run rather than accumulating versions.
   - Record the branch tip the handover describes (`git rev-parse HEAD`) in the file, so a later reader can prefix-match it against the current tip. The verification evidence in step 3 is only valid for that tip.
   - Report the absolute path written.
