---
name: check-alignment
description: Verify that implementation changes match the agreed plan or requirements. Use after implementing a planned change.
---

# Check Alignment

Systematically check the implementation against the agreed plan or requirements. Verify against the actual diff, never against a self-reported summary of what changed.

1. **Scope**: Do the changes match the agreed scope?
2. **Logic**: Does the implementation follow the planned design?
3. **Tests**: Did the planned verification run and pass? Confirm from its actual output, never a claim that it ran, and run it yourself when no such output exists. Report the command and its result.
4. **Resolution**: Report specific alignment gaps with evidence before modifying code or the plan.
