# Agent Workflows and Skills Repository

This repository contains a collection of developer agent workflows and skills. It provides standardized behavior rules, verification checks, and utility prompts for AI-assisted software development lifecycles (SDLC).

These workflows are designed to be run as utility rules under developer supervision (human-in-the-loop). Rather than fully automating the SDLC, developers invoke specific skills for planning, context gathering, verification, and code review as needed.

---

## The Agentic Workflow Lifecycle

To preserve context window capacity and ensure high-fidelity reviews, the software development lifecycle (SDLC) is split into discrete steps across thread boundaries. 

For a complete walkthrough of context decay strategies, sequential phases, and thread boundaries, see the detailed [LIFECYCLE.md](LIFECYCLE.md) playbook.

---

## Skills Index By Phase

For detailed instructions on each skill, refer to [AGENTS.md](AGENTS.md) or inspect the individual `SKILL.md` rules inside the [skills/](skills/) folder.

### 1. Analyzing (Pre-Coding Utilities)
*   **`gather-context`**: Maps file hierarchies and system dependencies.
*   **`research-web`**: Gathers authoritative documentation and real-world trade-offs.
*   **`review-story`**: Audits user stories for logical conflicts or system gaps.
*   **`root-cause`**: Conducts evidence-based debugging of errors without assuming quick-fixes.

### 2. Branch & Breakdown
*   **`create-branch`**: Standardizes feature branching using Conventional Commits patterns.
*   **`phase-breakdown`**: Deconstructs large changes into atomic execution steps/phases.

### 3. Execution & Verification Loop
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
*   **`distill-lessons`**: Codifies high-leverage lessons and guidelines to optimize future workflows.
*   **`validate-commit`**: Performs linting, styling auto-fixes, and test compilation prior to commit.

---

## Installation & Mechanics

The repository uses [setup.py](setup.py) to link or compile skills dynamically depending on your environment.

### Global Installation (For Claude Code, Antigravity, Copilot, Codex)
Symlinks target workflow files globally to machine-wide configuration directories (e.g. `~/.gemini/config/skills` or `~/.claude/skills`):
```bash
python setup.py link
```
To remove all globally installed links:
```bash
python setup.py unlink
```

### Local Project Installation (For Cursor & Windsurf)
Compiles source rules directly into the workspace config directory of a target project:
```bash
python setup.py project --path /path/to/project-directory
```
*   **Cursor**: Compiles skills into Cursor rules (`.cursor/rules/<skill-name>.mdc`).
*   **Windsurf**: Compiles skills into Windsurf rules (`.windsurf/rules/<skill-name>.md`).

