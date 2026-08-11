# Agentic Engineering Capabilities Index

<!-- Focus: AI Agent Parser Entry Point -->
This file contains the structured skills registry and routing index for coding agents using this repository.

*   **For Human Onboarding & Installation**: Refer to [README.md](README.md).
*   **For Agentic Engineering Lifecycle & Thread Boundary Guidelines**: Refer to [LIFECYCLE.md](LIFECYCLE.md).

---

## 1. Directory Structure

*   `skills/`: Contain individual coding-agent skill prompt manifests. Each subdirectory represents a skill and contains a `SKILL.md` file.
*   `setup.py`: Platform-agnostic installation utility script (refer to [README.md](README.md) for execution commands).

Frontmatter `model` and `effort` in each SKILL.md are Claude Code extensions, not part of the portable Agent Skills spec. The Cursor and Windsurf compilers strip them by design; Copilot, Codex, and Gemini receive them via symlink passthrough but do not define them. Plan-mode direction in plan-producing skills is prose, not frontmatter, and is expected to no-op on hosts without such a mode.

---

## 2. Core Agent Skills Registry

Below is the structured list of the 20 core skills managed by this repository. Coding agents should trigger these prompts when performing the corresponding lifecycle tasks.

Frontmatter `description` in each SKILL.md is authoritative; keep this table and README in sync when editing descriptions.

| Skill Name (Identifier) | Target Globs | Focus & Prompt Trigger Condition | Prompt Manifest |
| :--- | :--- | :--- | :--- |
| **`gather-context`** | `**/*` | Gather and organize context for a given file, folder, or component before planning or coding. Use when starting work on unfamiliar code. | [SKILL.md](skills/gather-context/SKILL.md) |
| **`research-web`** | `**/*` | Research current best practices and trade-offs from authoritative sources. Use when a decision needs external evidence. | [SKILL.md](skills/research-web/SKILL.md) |
| **`review-story`** | `**/*` | Audit a user story for gaps, conflicts, and missing detail. Use before planning or implementing a requirement. | [SKILL.md](skills/review-story/SKILL.md) |
| **`root-cause`** | `**/*` | Investigate an issue to identify its root cause with evidence before proposing fixes. Use when debugging. | [SKILL.md](skills/root-cause/SKILL.md) |
| **`create-branch`** | `**/*` | Check out the latest default branch and create a new feature branch using Conventional Commits. Use when starting new work. | [SKILL.md](skills/create-branch/SKILL.md) |
| **`phase-breakdown`** | `**/*` | Divide a large change into small, independently verifiable phases. Use before planning implementation of a complex task. | [SKILL.md](skills/phase-breakdown/SKILL.md) |
| **`plan-implementation`** | `**/*` | Create a detailed implementation plan for a change, surfacing open questions and assumptions. Use before writing code. | [SKILL.md](skills/plan-implementation/SKILL.md) |
| **`delegate-plan`** | `**/*` | Generate a self-contained prompt for another agent to execute an approved implementation plan. Use after a plan is approved and before implementation. | [SKILL.md](skills/delegate-plan/SKILL.md) |
| **`check-alignment`** | `**/*` | Verify that implementation changes match the agreed plan or requirements. Use after implementing a planned change. | [SKILL.md](skills/check-alignment/SKILL.md) |
| **`check-compliance`** | `**/*` | Audit changed code against the project's standards and guidelines. Use after changes are written and before review. | [SKILL.md](skills/check-compliance/SKILL.md) |
| **`plan-testing`** | `**/*` | Create a risk-based testing plan for a change. Use before writing tests. | [SKILL.md](skills/plan-testing/SKILL.md) |
| **`audit-tests`** | `**/*` | Audit an existing test suite for quality anti-patterns and produce a prioritized improvement plan. Use when test quality itself is the subject, not the tests for a specific change. | [SKILL.md](skills/audit-tests/SKILL.md) |
| **`simplify-diff`** | `**/*` | Audit the work in flight for over-engineering and unnecessary code, and report the cuts that would shrink the diff. Use when a change is correct but larger than it needs to be. | [SKILL.md](skills/simplify-diff/SKILL.md) |
| **`refactor-code`** | `**/*` | Audit design problems and apply behavior-preserving cleanup after approval. Use when code needs restructuring without new behavior. | [SKILL.md](skills/refactor-code/SKILL.md) |
| **`prepare-handover`** | `**/*` | Summarize completed work, key decisions, and verification evidence for a reviewer. Use at the end of an implementation thread. | [SKILL.md](skills/prepare-handover/SKILL.md) |
| **`review-branch`** | `**/*` | Review the active branch diff against its target branch. Use in a fresh thread before opening a pull request. | [SKILL.md](skills/review-branch/SKILL.md) |
| **`create-pr`** | `**/*` | Push the current branch and open a pull request with a synthesized title and description. Use when a reviewed branch is ready to submit. | [SKILL.md](skills/create-pr/SKILL.md) |
| **`review-pr`** | `**/*` | Review an open pull request and return a structured verdict. Use when auditing submitted changes. | [SKILL.md](skills/review-pr/SKILL.md) |
| **`distill-lessons`** | `**/*` | Codify durable lessons from recent work into project guidelines or documentation. Use sparingly, after a notable discovery. | [SKILL.md](skills/distill-lessons/SKILL.md) |
| **`validate-commit`** | `**/*` | Run formatters, linters, build, and tests to confirm code is ready to commit. Use before committing. | [SKILL.md](skills/validate-commit/SKILL.md) |
