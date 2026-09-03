---
name: review-branch
description: Review the active branch diff against its target branch. Use in a fresh thread before opening a pull request.
---

# Review Branch

1. **Prepare & Sync**: Compare the active branch with its target branch to isolate the diff, then read the handover at `~/.agent-workflows/<repo>/<branch>/handover.md`, where `<repo>` is `basename(dirname(git rev-parse --path-format=absolute --git-common-dir))` and `<branch>` is `git branch --show-current`.
   - A handover is the implementing agent's self-report. Treat it as context to verify against the diff, never as evidence to accept.
   - Its `Branch tip:` SHA must prefix-match `git rev-parse HEAD`. Treat a mismatch or a missing line as stale and discard the handover's verification claims.
   - Review from the diff alone when the file is absent or `git branch --show-current` is empty, and say which.
   - Read the branch tip's check status through the hosting platform's integration, or note that none has run yet.
2. **Quality & Design Audit**: Perform a deep cognitive and design audit of the isolated changes following the principles and checklist below.
3. **Submit Feedback**: Output a structured review report highlighting implementation strengths, potential issues, and improvement opportunities. Cast a final verdict (Approve vs. Request Changes) based on the strict verdict mapping rules below.
4. **Audit Only**: Do not modify any codebase files to fix issues identified during the review. Limit output to review comments and the final verdict.


---

<!-- include: shared/review-guidelines.md -->
