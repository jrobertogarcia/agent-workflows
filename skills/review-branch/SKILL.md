---
name: review-branch
description: Review the active branch changes using the local handover document and target branch diff.
---

# Review Branch

1. **Prepare & Sync**: Read the local handover document (e.g., `<handover-file>.md` or equivalent) and compare the active local feature branch against its target base branch to isolate the incoming code diff.
2. **Quality & Design Audit**: Perform a deep cognitive and design audit of the isolated changes following the principles and checklist below.
3. **Submit Feedback**: Output a structured review report highlighting implementation strengths, potential issues, and improvement opportunities. Cast a final verdict (Approve vs. Request Changes) based on the strict verdict mapping rules below.
4. **Review Only**: Do not modify any codebase files to fix the issues identified during the review. Limit output to review comments and the final verdict.

---

<!-- include: shared/review-guidelines.md -->
