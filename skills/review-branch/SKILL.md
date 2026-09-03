---
name: review-branch
description: Review the active branch diff against its target branch. Use in a fresh thread before opening a pull request.
---

# Review Branch

1. **Prepare & Sync**: Compare the active branch with its target branch to isolate the diff. Read the handover at `~/.agent-workflows/<repo>/<branch>/handover.md`, where `<repo>` is the basename of `git rev-parse --show-toplevel` (which resolves to the active worktree) and `<branch>` is `git rev-parse --abbrev-ref HEAD`. Ask for handover context when that file is absent.
2. **Quality & Design Audit**: Perform a deep cognitive and design audit of the isolated changes following the principles and checklist below.
3. **Submit Feedback**: Output a structured review report highlighting implementation strengths, potential issues, and improvement opportunities. Cast a final verdict (Approve vs. Request Changes) based on the strict verdict mapping rules below.
4. **Review Only**: Do not modify any codebase files to fix the issues identified during the review. Limit output to review comments and the final verdict.
5. **Route the Findings**: State where the fixes belong once the review is delivered. Small findings are fixed in this thread, then `prepare-handover` and `review-branch` are re-run in a fresh thread to confirm them. Major findings return to the implementation loop in a new thread, which repeats handover and audit before release.

---

<!-- include: shared/review-guidelines.md -->
