---
name: plan-testing
description: Create a risk-based testing plan for a change. Use before writing tests.
---

# Plan Testing

1. **Enter Plan Mode**: Switch the session into plan mode (or the host's read-only planning equivalent) before reading anything, and stay in it until the plan is approved. If the host has no such mode, treat this run as read-only.
2. **Ground the Plan**: Reuse context already gathered in this thread rather than re-reading it.
3. **Define Scenarios**: Outline test scenarios proportional to risk, covering happy paths, boundary conditions, edge cases, negative/error-handling paths, and integration points. State explicitly what was deliberately not tested.
4. **Write the Plan**: Cover at minimum:
   - **Scope**: what is under test and what is excluded.
   - **Scenarios**: the cases to run, grouped by risk or area.
   - **Approach**: automated vs manual, tools, and data setup.
   - **Not Tested**: what was deliberately left out and why.
5. **Approval**: Present the plan to the user for feedback and explicitly stop to wait for approval before implementing any tests.
