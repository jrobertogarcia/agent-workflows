---
name: delegate-plan
description: Generate a self-contained prompt for another agent to execute an approved implementation plan. Use after a plan is approved and before implementation.
---

# Delegate Plan

1. **Locate the Plan**: Establish the absolute path of the approved plan file and the absolute path of the working root (`git rev-parse --show-toplevel`, which resolves to the active worktree). Ask if either is ambiguous.
2. **Do Not Restate the Plan**: The executing agent reads the plan itself. Do not summarize its goal, steps, or file list in the prompt.
3. **Compose the Prompt**: The plan defines the executor's authority. Emit one fenced markdown block containing only:
   - the worktree path to work in and the plan file path to read first;
   - an instruction to execute the plan end to end, including every step it specifies;
   - a scope fence: the plan's stated scope is the boundary. Add nothing it does not call for, drop nothing it does;
   - an instruction to run the verification the plan specifies and report the results;
   - a stop condition: pause when the codebase materially diverges from what the plan assumes, or when a decision the plan does not cover would change its outcome;
   - a closing instruction to summarize what changed.
4. **Output Only**: Print the prompt block and stop. Do not execute the plan, modify code, or create files.
