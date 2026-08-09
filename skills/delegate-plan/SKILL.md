---
name: delegate-plan
description: Generate a self-contained prompt for another agent to execute an approved implementation plan. Use after a plan is approved and before implementation.
model: sonnet
effort: low
---

# Delegate Plan

1. **Locate the Plan**: Establish the absolute path of the approved plan file and the absolute path of the working root (`git rev-parse --show-toplevel`, which resolves to the active worktree). Ask if either is ambiguous.
2. **Do Not Restate the Plan**: The executing agent reads the plan itself. Do not summarize its goal, steps, or file list in the prompt.
3. **Compose the Prompt**: Emit one fenced markdown block containing only:
   - the worktree path to work in and the plan file path to read first;
   - an instruction to execute the plan end to end exactly as written;
   - a scope fence: no unplanned refactors, unrelated fixes, commits, or pull requests;
   - an instruction to run the verification the plan specifies and report the results;
   - a stop condition: pause and ask when the plan is ambiguous or the codebase diverges from what it assumes;
   - a closing instruction to summarize what changed.
4. **Output Only**: Print the prompt block and stop. Do not execute the plan, modify code, or create files.
