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
*   **`gather-context`**: Maps file hierarchies and system dependencies.
*   **`research-web`**: Gathers authoritative documentation and real-world trade-offs.
*   **`review-story`**: Audits user stories for logical conflicts or system gaps.
*   **`root-cause`**: Conducts evidence-based debugging of errors without assuming quick-fixes.

### 2. Branch & Breakdown
*   **`create-branch`**: Standardizes feature branching using Conventional Commits patterns.
*   **`phase-breakdown`**: Deconstructs large changes into atomic execution steps/phases.

### 3. Implementation & Verification Loop
*   **`plan-implementation`**: Creates detailed step-by-step blueprints (`implementation_plan.md`).
*   **`check-alignment`**: Verifies that actual changes match the implementation plan.
*   **`check-compliance`**: Ensures code satisfies relevant compliance and coding standards.
*   **`plan-testing`**: Formulates robust automated and manual test strategies.
*   **`refactor-code`**: Cleans code patterns (SOLID/KISS) incrementally without regressions.

### 4. Handover & Release
*   **`prepare-handover`**: Packages context and verification results for review.
*   **`review-branch`**: Audits local branch diffs for edge cases in a clean thread context.
*   **`create-pr`**: Pushes code and initializes pull requests with rich, structured metadata.
*   **`review-pr`**: Conducts automated builds and checks on open PRs.

### 5. Ad-Hoc Utilities
*   **`distill-lessons`**: Codifies high-leverage lessons and guidelines to improve future workflows.
*   **`validate-commit`**: Performs linting, styling auto-fixes, and test compilation prior to commit.

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
