# Agent Capabilities Index

<!-- Focus: AI Agent Parser Entry Point -->
This file contains the structured skills registry and routing index for AI developer agents parsing this repository.

*   **For Human Onboarding & Installation**: Refer to [README.md](README.md).
*   **For Workflow Lifecycle & Thread Boundary Guidelines**: Refer to [LIFECYCLE.md](LIFECYCLE.md).

---

## 1. Directory Structure

*   `skills/`: Contain individual agent skill prompt manifests. Each subdirectory represents a skill and contains a `SKILL.md` file.
*   `setup.py`: Compilation and linking script for the target IDE environments (Cursor rules `.cursor/rules/`, Windsurf rules `.windsurf/rules/`, and global agent configuration files).

---

## 2. Core Agent Skills Registry

Below is the structured list of the 17 core SDLC workflows managed by this repository. Agents should trigger these prompts when performing the corresponding tasks.

| Skill Name (Identifier) | Target Globs | Focus & Prompt Trigger Condition | Prompt Manifest |
| :--- | :--- | :--- | :--- |
| **`gather-context`** | `**/*` | Mapping system dependency and exploring directory trees. | [SKILL.md](skills/gather-context/SKILL.md) |
| **`research-web`** | `**/*` | Conducting lookups for best practices, libraries, or specs. | [SKILL.md](skills/research-web/SKILL.md) |
| **`review-story`** | `**/*` | Analyzing gaps or logic conflicts in requirements/user stories. | [SKILL.md](skills/review-story/SKILL.md) |
| **`root-cause`** | `**/*` | Exploring evidence, stack traces, and logs to find bug root causes. | [SKILL.md](skills/root-cause/SKILL.md) |
| **`create-branch`** | `**/*` | Creating and configuring clean feature Git branches. | [SKILL.md](skills/create-branch/SKILL.md) |
| **`phase-breakdown`** | `**/*` | Breaking down large implementation tasks into phased roadmap milestones. | [SKILL.md](skills/phase-breakdown/SKILL.md) |
| **`plan-implementation`** | `**/*` | Creating step-by-step technical blueprints (`implementation_plan.md`). | [SKILL.md](skills/plan-implementation/SKILL.md) |
| **`check-alignment`** | `**/*` | Verifying actual implementation changes align 100% with the plan. | [SKILL.md](skills/check-alignment/SKILL.md) |
| **`check-compliance`** | `**/*` | Validating code changes against project-wide coding standards. | [SKILL.md](skills/check-compliance/SKILL.md) |
| **`plan-testing`** | `**/*` | Formulating automated and manual verification plans. | [SKILL.md](skills/plan-testing/SKILL.md) |
| **`refactor-code`** | `**/*` | Improving structural design (SOLID/KISS) without functional changes. | [SKILL.md](skills/refactor-code/SKILL.md) |
| **`prepare-handover`** | `**/*` | Synthesizing changes and test outcomes into review summaries. | [SKILL.md](skills/prepare-handover/SKILL.md) |
| **`review-branch`** | `**/*` | Auditing local branch diffs for edge cases prior to PR creation. | [SKILL.md](skills/review-branch/SKILL.md) |
| **`create-pr`** | `**/*` | Pushing local branches and preparing pull request descriptions. | [SKILL.md](skills/create-pr/SKILL.md) |
| **`review-pr`** | `**/*` | Reviewing PR branches and returning rating/pass-fail verdicts. | [SKILL.md](skills/review-pr/SKILL.md) |
| **`distill-lessons`** | `**/*` | Reflection utility to document high-leverage guidelines and patterns. | [SKILL.md](skills/distill-lessons/SKILL.md) |
| **`validate-commit`** | `**/*` | Performing final local quality checks before completing Git commits. | [SKILL.md](skills/validate-commit/SKILL.md) |
