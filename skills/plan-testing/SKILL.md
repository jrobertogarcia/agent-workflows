---
name: plan-testing
description: Create a risk-based testing plan for a change. Use before writing tests.
---

# Plan Testing

1. **Ground the Plan**: Reuse context already gathered in this thread rather than re-reading it.
2. **Define Scenarios**: Outline test scenarios proportional to risk, covering happy paths, boundary conditions, edge cases, negative/error-handling paths, and integration points. State explicitly what was deliberately not tested.
3. **Write the Plan**: Cover at minimum:
   - **Scope**: what is under test and what is excluded.
   - **Scenarios**: the cases to run, grouped by risk or area.
   - **Approach**: automated vs manual, tools, and data setup.
   - **Not Tested**: what was deliberately left out and why.
4. **Approval**: Present the plan to the user for feedback and explicitly stop to wait for approval before implementing any tests.
