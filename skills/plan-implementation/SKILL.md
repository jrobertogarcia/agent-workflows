---
name: plan-implementation
description: Create a detailed implementation plan for a change, surfacing open questions and assumptions. Use before writing code.
model: opus
effort: medium
---

# Plan Implementation

1. **Ground the Plan**: Read the code you intend to change and the standards that govern it. Reuse context already gathered in this thread rather than re-reading it.
2. **Resolve Uncertainty**: Settle open questions from the codebase first. Ask only what you cannot settle yourself and where different answers would change the plan. Record the rest as explicit assumptions.
3. **Write the Plan**: Cover at minimum:
   - **Goal**: the problem being solved and what "done" looks like.
   - **Changes**: files to add or modify, grouped by module or layer, with the specific edit intended for each.
   - **Sequence**: order of work and dependencies between steps.
   - **Verification**: automated and manual checks that prove it works.
   - **Out of Scope**: what this plan deliberately does not do.
   - **Open Questions & Assumptions**: from step 2.
   Follow project conventions. Create a file only when requested.
4. **Stop for Approval**: Present the plan and explicitly wait for approval. Do not write implementation code.
