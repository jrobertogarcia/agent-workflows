# Agent Workflows and Skills Repository

Welcome to the centralized Agent Workflows and Skills repository. This repository defines standardized developer agent behavior rules, workflows, and automated capabilities. 

---

## 1. Directory Structure

*   `AGENTS.md` (This file): Root entrypoint routing file.
*   `setup.py`: Platform-agnostic script to install, manage, and uninstall these rules globally or copy them locally to a specific project.
*   `skills/`: The canonical storage folder for skills.
    *   Each skill resides in its own lowercase, hyphenated subdirectory (e.g., `skills/refactor-code/`).
    *   Inside each subdirectory, a `SKILL.md` contains the trigger rules (YAML frontmatter) and system prompt instructions.

---

## 2. Core Skills Library

Below is a summary of the 17 core SDLC skills managed by this repository:

| Skill Directory Name | Purpose | Description |
| :--- | :--- | :--- |
| **`check-alignment`** | Plan Alignment Verification | Confirms the implementation aligns with the original `implementation_plan.md`. |
| **`check-compliance`** | Compliance & Standards Audit | Ensures the implementation meets project-specific requirements and standards. |
| **`create-branch`** | Git Feature Branch Creation | Standardizes git branching using Conventional Commits patterns. |
| **`create-pr`** | Pull Request Initialization | Automates pushing code changes and initializing pull requests with clean metadata. |
| **`distill-lessons`** | Lesson Codification | Gathers best practices and reflections to codify them into documentation. |
| **`gather-context`** | Dependency & Context Mapping | Explores system file hierarchies and relationships before coding. |
| **`phase-breakdown`** | Milestone Phasing Plan | Deconstructs large changes into incremental, atomic execution steps. |
| **`plan-implementation`** | Technical Strategic Planning | Creates detailed `implementation_plan.md` blueprints. |
| **`plan-testing`** | Automated/Manual Test Planning | Formulates robust testing strategies covering boundary and edge cases. |
| **`prepare-handover`** | Handover Documentation | Compiles architectural and verification notes for incoming peer review. |
| **`refactor-code`** | Clean Design Refactoring | Incrementally improves design using SOLID and KISS principles without regressions. |
| **`research-web`** | 2026 Web Best Practices Research | Gathers authoritative technical documentation and real-world trade-offs. |
| **`review-branch`** | Local Code Quality Audit | Conducts strict quality and edge-case code reviews on local branch diffs. |
| **`review-pr`** | Pull Request Code Review | Performs pull request analysis, returning structured ratings and PASS/FAIL verdicts. |
| **`review-story`** | User Story Gap Analysis | Audits user stories for logical conflicts or system gaps before planning. |
| **`root-cause`** | Evidence-based Debugging | Pinpoints root causes of errors without assuming quick-fixes. |
| **`validate-commit`** | Local Verification Parity | Executes linting, formatting auto-fixes, and test compilations before committing. |

---

## 3. How to Use

### Global Installation (For Claude Code, Antigravity, Copilot, Codex, etc.)
To link these skills to your local machine-wide configuration directory:
```bash
python setup.py link
```

To clean up all globally installed skills:
```bash
python setup.py unlink
```

### Local Project Installation (For Cursor & Windsurf)
To copy or compile these rules to the rules directory of an active project workspace:
```bash
python setup.py project --path /path/to/project-directory
```
This generates:
*   `.cursor/rules/<skill-name>.mdc` (using Cursor's MDC metadata format)
*   `.windsurf/rules/<skill-name>.md` (using Windsurf's rule directory format)
