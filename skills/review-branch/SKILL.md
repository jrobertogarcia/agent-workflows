---
name: review-branch
description: Review the active branch diff against its target branch. Use in a fresh thread before opening a pull request.
---

# Review Branch

1. **Prepare & Sync**: Compare the active branch with its target branch to isolate the diff, then read the handover at `~/.agent-workflows/<repo>/<branch>/handover.md`, where `~` expands to the home directory, `<repo>` is `basename(dirname(git rev-parse --path-format=absolute --git-common-dir))`, and `<branch>` is `git branch --show-current`.
   - A handover is the implementing agent's self-report. Treat it as context to verify against the diff, never as evidence to accept.
   - Confirm it is current: the branch tip it records must match `git rev-parse HEAD`. On a mismatch the handover is stale, so say so and discard its verification claims.
   - When the file is absent, or `git branch --show-current` is empty because the checkout is on a detached HEAD, note the absence and review from the diff alone.
2. **Quality & Design Audit**: Perform a deep cognitive and design audit of the isolated changes following the principles and checklist below.
3. **Submit Feedback**: Output a structured review report highlighting implementation strengths, potential issues, and improvement opportunities. Cast a final verdict (Approve vs. Request Changes) based on the strict verdict mapping rules below.
4. **Audit Without Fixing**: Do not modify any codebase file while auditing or before the verdict is delivered. Limit the audit's own output to review comments and the final verdict. Fixing afterwards is in scope here because this is your own pre-PR branch, whereas `review-pr` stays read-only throughout because it audits work someone else has already submitted.
5. **Route the Findings**: After delivering the verdict, route the blocking findings, meaning the Critical and Important ones. Critical and architectural findings go to a new implementation thread. The rest are fixed in this thread, which then re-runs `prepare-handover` itself, and a fresh thread re-runs `review-branch` to confirm them. Report Suggestions and Nitpicks without gating release on them.

---

<!-- include: shared/review-guidelines.md -->
