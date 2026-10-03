# Architecture Decisions: Stack Maintenance & Upstream Rebasing

**Date**: 2026-09-20  
**Status**: Decided  
**Context**: Protocol for applying review comments to submitted PR layers and synchronizing downstream branches in a stacked PR workflow (`gh-stack`).

---

### 1. Separation of Concerns
* **Feature Orchestrator** ([ADR 0001](0001-orchestrator-subagents.md)): Strictly authors and submits the stack (`RELEASED`).
* **Stack Maintenance** (This ADR): Handles post-submission review cycles and upstream rebasing out-of-band.

---

### 2. Cascade Rebase Protocol
When a submitted layer requires changes from GitHub review:

1. **Target**: Check out the target layer:
   ```bash
   gh stack checkout <branch>
   ```
2. **Apply & Commit**: Apply requested changes and commit with Conventional Commits.
3. **Upstack Cascade**: Rebase all downstream dependent layers onto the new commit:
   ```bash
   gh stack rebase --upstack
   ```
   *Requirement*: Enable `git config --global rerere.enabled true` to avoid redundant conflict resolution across layers.
4. **Downstream Verification**: For each downstream branch, run baseline checks (`validate-commit`) to guarantee contract and test parity.
5. **Sync Remote**: Push updated stack references with lease:
   ```bash
   gh stack sync
   ```

---

### 3. Passive Drift Invariant
At agent startup on any branch, assert:
$$\text{git merge-base HEAD } \langle\text{upstream}\rangle == \text{state.json.git\_anchor.base\_sha}$$
* **Match**: Safe to proceed.
* **Mismatch**: Upstream moved out-of-band. Halt before code edits; run types and tests to identify broken contracts.

---

### 4. Stack Depth Guard
* **Maximum Active Depth**: $\le 3$ unmerged layers per stack.
* Stacks exceeding 3 layers exponentially increase rebase conflict cost upon upstream changes.
