---
name: review-branch
description: Review the active branch diff against its target branch. Use in a fresh thread before opening a pull request.
---

# Review Branch

1. **Prepare & Sync**: Compare the active branch with its target branch to isolate the diff. Read the handover at `~/.agent-workflows/<repo>/<branch>/handover.md`, where `<repo>` is `basename(dirname(git rev-parse --path-format=absolute --git-common-dir))` and `<branch>` is `git branch --show-current`. Ask for handover context when that file is absent, or when `git branch --show-current` is empty because the checkout is on a detached HEAD.
2. **Quality & Design Audit**: Perform a deep cognitive and design audit of the isolated changes following the principles and checklist below.
3. **Submit Feedback**: Output a structured review report highlighting implementation strengths, potential issues, and improvement opportunities. Cast a final verdict (Approve vs. Request Changes) based on the strict verdict mapping rules below.
4. **Audit Without Fixing**: Do not modify any codebase file while auditing or before the verdict is delivered. Limit the audit's own output to review comments and the final verdict.
5. **Route the Findings**: After delivering the verdict, state where each fix belongs. Small findings are fixed in this thread, then `prepare-handover` and `review-branch` are re-run in a fresh thread to confirm them. Major findings return to the implementation loop in a new thread, which repeats handover and audit before release.

---

<!-- include: shared/review-guidelines.md -->
