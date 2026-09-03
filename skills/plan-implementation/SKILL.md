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
6. **Report the Plan Artifact**: `delegate-plan` consumes the approved plan by path, so make it addressable. Host plan filenames are machine-generated, so find the file the host wrote rather than deriving its name: search the host's plan storage for the most recently written entry, read it back, and confirm it holds this plan. Report that absolute path.
   - Addressability is what you read back, not what you assert. A path you have not read is a self-report.
   - Do not copy the host's file. Exactly one plan artifact exists.
   - When no file holding this plan can be read back, say so and note that delegation is unavailable on this host. Write a plan file yourself only when asked to, at the path the user names; that file is then the single artifact.
