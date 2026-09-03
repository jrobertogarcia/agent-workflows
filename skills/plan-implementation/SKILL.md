---
name: plan-implementation
description: Create a detailed implementation plan for a change, surfacing open questions and assumptions. Use before writing code.
---

# Plan Implementation

1. **Enter Plan Mode**: Switch the session into plan mode (or the host's read-only planning equivalent) before reading anything, and stay in it until the plan is approved. If the host has no such mode, treat this run as read-only.
2. **Ground the Plan**: Read the code you intend to change and the standards that govern it. Reuse context already gathered in this thread rather than re-reading it.
3. **Resolve Uncertainty**: Settle open questions from the codebase first. Ask only what you cannot settle yourself and where different answers would change the plan. Record the rest as explicit assumptions.
4. **Write the Plan**: Cover at minimum:
   - **Goal**: the problem being solved and what "done" looks like.
   - **Changes**: files to add or modify, grouped by module or layer, with the specific edit intended for each.
   - **Sequence**: order of work and dependencies between steps.
   - **Verification**: automated and manual checks that prove it works.
   - **Out of Scope**: what this plan deliberately does not do.
   - **Open Questions & Assumptions**: from step 3.
   Follow project conventions.
5. **Stop for Approval**: Present the plan and explicitly wait for approval. Do not write implementation code.
6. **Report the Plan Artifact**: `delegate-plan` consumes the approved plan by path, so make it addressable. Locate the host's plan storage, which is often one directory shared by every session rather than one scoped to this project. Filenames there are machine-generated, so never derive one: read back candidates newest first until you find the file holding this plan, then report its absolute path.
   - Addressability is what you read back, not what you assert. A path you have not read is a self-report.
   - Do not copy the host's file. Exactly one plan artifact exists.
   - When plan storage exists but no candidate holds this plan, report that the plan file could not be located and ask where it was written. Do not conclude anything about the host.
   - When the host has no plan storage at all, say so, and add that delegation is unavailable only when delegation has been requested, since `delegate-plan` is optional. Write a plan file yourself only when asked to, at the path the user names; that file is then the single artifact.
