# Agentic Engineering Workflows

Skills for delivering software with coding agents through explicit, human-gated phases: context gathering, planning, implementation, verification, fresh-thread review, and release. Use the skills one by one, or let `orchestrate` drive a requirement end to end, on one branch or a stack of branches.

*   [LIFECYCLE.md](LIFECYCLE.md): the phases, thread boundaries, orchestrated mode, and stack maintenance.
*   [AGENTS.md](AGENTS.md): the routing index for coding agents.

---

## Skills Index

### Analyze
*   **`gather-context`**: Gather and organize context for a given file, folder, or component before planning or coding. Use when starting work on unfamiliar code.
*   **`research-web`**: Research current best practices and trade-offs from authoritative sources. Use when a decision needs external evidence.
*   **`review-story`**: Audit a user story for gaps, conflicts, and missing detail. Use before planning or implementing a requirement.
*   **`root-cause`**: Investigate an issue to identify its root cause with evidence before proposing fixes. Use when debugging.

### Branch and break down
*   **`create-branch`**: Check out the latest default branch and create a new feature branch using Conventional Commits. Use when starting new work.
*   **`phase-breakdown`**: Divide a large change into small, independently verifiable phases. Use before planning implementation of a complex task.

### Plan, implement, verify
*   **`plan-implementation`**: Create a detailed implementation plan for a change, including risk-based test scenarios, and surface open questions and assumptions. Use before writing code or tests.
*   **`delegate-plan`**: Generate a self-contained prompt for another agent to execute an approved implementation plan. Use after a plan is approved and before implementation.
*   **`check-alignment`**: Verify the actual diff against the agreed plan and the project's standards, and report ALIGNED or GAPS without editing. Use after implementing a change and before review.
*   **`simplify-diff`**: Audit the work in flight for over-engineering and unnecessary code, and report the cuts that would shrink the diff without applying them. Use when a change is correct but larger than it needs to be.
*   **`refactor-code`**: Audit structural design problems and apply the behavior-preserving restructure after approval. Use when code needs restructuring rather than subtraction.
*   **`audit-tests`**: Audit an existing test suite for quality anti-patterns and produce a prioritized improvement plan. Use when test quality itself is the subject, not the tests for a specific change.
*   **`validate-commit`**: Run formatters, linters, build, and tests to confirm code is ready to commit. Use before committing.
*   **`create-commit`**: Stage the in-scope changes and commit them with a message matching the repository's convention. Use after a logical piece of work is complete and verified.

### Hand over, review, release
*   **`prepare-handover`**: Summarize completed work, key decisions, and verification evidence for a reviewer. Use at the end of an implementation thread.
*   **`review-branch`**: Review the active branch diff against its target branch. Use in a fresh thread before opening a pull request.
*   **`create-pr`**: Push the current branch and open a pull request with a synthesized title and description. Use when a reviewed branch is ready to submit.
*   **`distill-lessons`**: Codify durable lessons from recent work into project guidelines or documentation. Use sparingly, after a notable discovery.

### Orchestrate
*   **`orchestrate`**: Drive one requirement from story review to open pull requests, on one branch or a stack of branches, dispatching each lifecycle step to a fresh subagent and stopping for plan and release approval. Use to run the whole lifecycle end to end.

---

## Installation

```bash
python3 setup.py install --ref <tag>
```

`install` clones this repository into `~/.local/share/agent-workflows`, checks out the release tag detached, and links from there, so what you run is pinned and does not move with a development checkout. Re-run it with a newer tag to update.

If you installed with `link` from a development checkout, switch over once: run `python3 setup.py unlink` from that checkout, then `python3 setup.py install --ref <tag>`. To link a checkout directly instead (for development), use `python3 setup.py link`.

For each host whose config directory already exists, `install` and `link` install every skill and the `orchestrate-step` agent that `orchestrate` dispatches to:

| Host | Skills | `orchestrate-step` agent |
| :--- | :--- | :--- |
| Claude Code | `~/.claude/skills/` | `~/.claude/agents/orchestrate-step.md` |
| Antigravity | `~/.gemini/config/skills/` | `~/.gemini/config/agents/orchestrate-step/` |
| Copilot | `~/.copilot/skills/` | `~/.copilot/agents/orchestrate-step.agent.md` |
| Codex | `~/.agents/skills/` | `~/.codex/agents/orchestrate-step.toml` (generated) |

Skills are symlinked, or copied where symlinks fail. Existing entries this repository did not create are skipped unless you pass `--force`:

```bash
python3 setup.py link --force   # `install` takes --force too
python3 setup.py unlink        # removes only what this repository installed
```

Cursor and Windsurf read project rules instead. Compile the skills into a project with:

```bash
python3 setup.py project --path /path/to/project   # writes .cursor/rules/<skill>.mdc and .windsurf/rules/<skill>.md
python3 setup.py project --path /path/to/project --clean
```

`project` skips `orchestrate`, which needs subagents. It refuses to overwrite rule files it did not write unless you pass `--force`.

`orchestrate` is verified on Claude Code; other hosts are untested.

## Development

```bash
python3 -m unittest discover -s tests
```
