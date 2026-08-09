# Agentic Engineering Workflows

This repository provides a reusable workflow system: a collection of skills, rules, and lifecycle practices for professional software engineering with coding agents.

Agentic engineering is the practice of delivering software through human-directed collaboration with coding agents, using explicit context gathering, planning, implementation, verification, review, and release gates.

These lifecycle workflows keep coding-agent work structured and auditable. Instead of relying on a single "one-shot" generation pass, the repository breaks engineering work into phased steps where developers guide intent, approve transitions, and use specialized skills for planning, context gathering, verification, and review.

---

## The Agentic Engineering Lifecycle

To preserve context window capacity and ensure high-fidelity reviews, this lifecycle is split into discrete steps across thread boundaries.

For a complete walkthrough of context decay strategies, sequential phases, and thread boundaries, see the detailed [LIFECYCLE.md](LIFECYCLE.md) playbook.

---

## Skills Index By Phase

For a structured routing index of all skills and trigger scopes, refer to [AGENTS.md](AGENTS.md). For detailed prompt instructions, inspect the individual `SKILL.md` rules inside the [skills/](skills/) folder.

### 1. Analyzing (Pre-Coding Utilities)
*   **`gather-context`**: Gather and organize context for a given file, folder, or component before planning or coding. Use when starting work on unfamiliar code.
*   **`research-web`**: Research current best practices and trade-offs from authoritative sources. Use when a decision needs external evidence.
*   **`review-story`**: Audit a user story for gaps, conflicts, and missing detail. Use before planning or implementing a requirement.
*   **`root-cause`**: Investigate an issue to identify its root cause with evidence before proposing fixes. Use when debugging.

### 2. Branch & Breakdown
*   **`create-branch`**: Check out the latest default branch and create a new feature branch using Conventional Commits. Use when starting new work.
*   **`phase-breakdown`**: Divide a large change into small, independently verifiable phases. Use before planning implementation of a complex task.

### 3. Implementation & Verification Loop
*   **`plan-implementation`**: Create a detailed implementation plan for a change, surfacing open questions and assumptions. Use before writing code.
*   **`check-alignment`**: Verify that implementation changes match the agreed plan or requirements. Use after implementing a planned change.
*   **`check-compliance`**: Audit changed code against the project's standards and guidelines. Use after changes are written and before review.
*   **`plan-testing`**: Create a risk-based testing plan for a change. Use before writing tests.
*   **`audit-tests`**: Audit an existing test suite for quality anti-patterns and produce a prioritized improvement plan. Use when test quality itself is the subject, not the tests for a specific change.
*   **`refactor-code`**: Audit design problems and apply behavior-preserving cleanup after approval. Use when code needs restructuring without new behavior.

### 4. Handover & Release
*   **`prepare-handover`**: Summarize completed work, key decisions, and verification evidence for a reviewer. Use at the end of an implementation thread.
*   **`review-branch`**: Review the active branch diff against its target branch. Use in a fresh thread before opening a pull request.
*   **`create-pr`**: Push the current branch and open a pull request with a synthesized title and description. Use when a reviewed branch is ready to submit.
*   **`review-pr`**: Review an open pull request and return a structured verdict. Use when auditing submitted changes.

### 5. Ad-Hoc Utilities
*   **`distill-lessons`**: Codify durable lessons from recent work into project guidelines or documentation. Use sparingly, after a notable discovery.
*   **`validate-commit`**: Run formatters, linters, build, and tests to confirm code is ready to commit. Use before committing.

---

## Installation & Mechanics

The repository uses [setup.py](setup.py) to link or compile skills dynamically depending on your agent environment.

### Global Installation (For Claude Code, Antigravity, Copilot, Codex)
Symlinks target workflow files globally to machine-wide configuration directories (e.g. `~/.gemini/config/skills` or `~/.claude/skills`):
```bash
python setup.py link
```
To remove all globally installed links:
```bash
python setup.py unlink
```
By default, global installation skips existing files or directories that were not created by this repository. To intentionally replace unmanaged collisions:
```bash
python setup.py link --force
```
Unlink removes only workflow-managed installed targets.

### Local Project Installation (For Cursor & Windsurf)
Compiles source rules directly into the workspace config directory of a target project:
```bash
python setup.py project --path /path/to/project-directory
```
*   **Cursor**: Compiles skills into Cursor rules (`.cursor/rules/<skill-name>.mdc`).
*   **Windsurf**: Compiles skills into Windsurf rules (`.windsurf/rules/<skill-name>.md`).

### Development Checks
Run the installer regression suite with:
```bash
python3 -m unittest discover -s tests
```
