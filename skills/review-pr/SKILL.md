---
name: review-pr
description: Review an open pull request and return a structured verdict. Use when auditing submitted changes.
---

# Review PR

1. **Prepare & Sync**: Fetch the target Pull Request or Merge Request's diff and check status through the hosting platform's integration. Check out the branch locally only when the diff cannot be understood without the surrounding code.
2. **Quality & Design Audit**: Perform a deep cognitive and design audit of the changes following the principles and checklist below.
3. **Submit Feedback**: Return a structured review highlighting strengths, issues, and improvement opportunities, with a final verdict. Publish feedback only when requested.
4. **Review Only**: Do not modify any codebase files to fix the issues identified during the review. Limit output to review comments and the final verdict.

---

<!-- include: shared/review-guidelines.md -->
