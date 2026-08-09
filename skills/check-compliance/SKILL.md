---
name: check-compliance
description: Audit changed code against the project's standards and guidelines. Use after changes are written and before review.
model: sonnet
effort: medium
---

# Check Compliance

Systematically audit the implementation against project standards:

1. **Identify**: Identify the guidelines, design standards, and requirements that govern the files you changed.
2. **Read**: Reuse standards already read in this thread rather than re-reading them. Review only what you have not yet seen.
3. **Verify**: Verify the changed code against those rules. Name any standard you could not evaluate rather than silently assuming a pass.
4. **No Premature Fixes**: If compliance violations are found, do not fix them directly. Document the issues and propose the fixes as part of a formal implementation plan.
