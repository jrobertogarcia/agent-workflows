---
name: orchestrate-step
description: Execute exactly one self-contained step prompt in the worktree it names and report the result. Use when an orchestrator dispatches a step.
---

# Orchestrate Step

The prompt you were given is the whole task. Run it as written, and do nothing beyond it.

1. **Work where the prompt says**: Run every command in the worktree the prompt names. If it names none, or the path is not a worktree, or the prompt names a branch and `git branch --show-current` differs, stop and report.
2. **Read what it points at**: When the prompt points at a skill file, read it and follow it as the instructions for this step. Resolve each `<!-- include: <path> -->` directive by reading `<path>` relative to the root of the repository that holds that skill's `skills/` directory. Where the prompt and the skill differ, follow the prompt.
3. **Leave orchestrator state alone**: Never write `stack.json`, `state.json`, `plan.md` or `requirements.md` under `~/.agent-workflows/`. Write an evidence file there, such as `handover.md`, only when the prompt, or a skill it points you at, asks for it.
4. **Stop rather than improvise**: If an assumption in the prompt does not hold (a path, branch, commit, file or tool is missing or different), stop and report what you found instead of working around it.
5. **Report**: End with what you did, the files you changed, the checks you ran and their results, and anything left undone. If you committed, include the output of `git rev-parse HEAD`.
