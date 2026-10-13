---
name: plan-implementation
description: Create a detailed implementation plan for a change, including risk-based test scenarios, and surface open questions and assumptions. Use before writing code or tests.
---

# Plan Implementation

1. **Enter Plan Mode**: Switch the session into plan mode (or the host's read-only planning equivalent) before reading anything, and stay in it until the plan is approved. If the host has no such mode, treat this run as read-only.
2. **Ground the Plan**: Read the code you intend to change and the standards that govern it. Reuse context already gathered in this thread rather than re-reading it.
3. **Resolve Uncertainty**: Settle open questions from the codebase first. Ask only what you cannot settle yourself and where different answers would change the plan. Record the rest as explicit assumptions.
4. **Write the Plan**: Cover at minimum:
   - **Goal**: the problem being solved and what "done" looks like.
   - **Changes**: files to add or modify, grouped by module or layer, with the specific edit intended for each.
   - **Sequence**: order of work and dependencies between steps.
   - **Verification**: automated and manual checks that prove it works, with test scenarios proportional to risk: happy paths, boundary conditions, edge cases, error handling, and integration points.
   - **Out of Scope**: what this plan deliberately does not do, including what is deliberately not tested and why.
   - **Open Questions & Assumptions**: from step 3.
   Follow project conventions.
5. **Stop for Approval**: Present the plan and explicitly wait for approval. Do not write implementation code.
6. **Return the Plan**: Return the complete plan text in the response, not a path to a plan file.

