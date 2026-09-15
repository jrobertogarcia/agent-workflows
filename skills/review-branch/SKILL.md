---
name: review-branch
description: Review the active branch diff against its target branch. Use in a fresh thread before opening a pull request.
---

# Review Branch

1. **Prepare & Sync**: Compare the active branch with its target branch to isolate the diff. If a handover artifact is available at `~/.agent-workflows/<repo>/<branch>/handover.md`, read it as optional context to verify against the diff. If absent or stale (does not cover the current branch tip), review from the diff alone.
2. **Quality & Design Audit**: Perform a deep cognitive and design audit of the isolated changes following the principles and checklist below.
3. **Submit Feedback**: Output a structured review report highlighting implementation strengths, potential issues, and improvement opportunities. Cast a final verdict (Approve vs. Request Changes) based on the strict verdict mapping rules below.
4. **Audit Only**: Do not modify any codebase files to fix issues identified during the review. Limit output to review comments and the final verdict.


---

<!-- include: shared/review-guidelines.md -->
