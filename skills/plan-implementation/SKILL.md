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
   - **Make It Addressable**: `delegate-plan` consumes the plan by path, so the plan must end up addressable. It is addressable only if you can state an absolute filesystem path to it; if you cannot, it is not addressable regardless of how complete it looks in the conversation.
   - When the session's plan mode persists the plan to disk, that file is the artifact. Do not copy it anywhere. Report its absolute path in the output.
   - When the host does not persist plans, say so explicitly and note that delegation is unavailable on this host.
   - Exactly one plan artifact exists. Never create a second copy.
5. **Stop for Approval**: Present the plan and explicitly wait for approval. Do not write implementation code.
