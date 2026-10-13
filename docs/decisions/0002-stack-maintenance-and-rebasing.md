# 0002. Manual stack maintenance and cascade rebasing

**Status**: Proposed
**Date**: 2026-10-13

## Context

[ADR 0001](0001-orchestrator-subagents.md) authors a stack and stops each layer at `RELEASED`: the layer's PR is open with the correct base. After that point reviewers comment, parents change, and parents merge. Applying that feedback and keeping the layers above a changed layer consistent is stack maintenance.

Maintenance is human-owned and manual. No skill implements it. It uses `gh stack`, which 0001 D3 makes a hard dependency, together with the host's normal editing and the existing `validate-commit` and `create-commit` skills.

## Decision

### D1. Maintenance procedure

For a review comment on any released layer:

1. Check out the layer with `gh stack checkout <branch>`, then run `gh stack sync` so local branches match the remote.
2. Confirm the layer contains its parent's tip: `git merge-base --is-ancestor <parent> HEAD`. If that fails, run `gh stack rebase --upstack` first, so the edit lands on the current parent. This check uses git only and does not read `state.json`.
3. Apply the review comments with the host's normal editing, then run `validate-commit` and `create-commit`.
4. Run `gh stack rebase --upstack` to rebase every layer above. `gh stack init` enables `rerere` for the repository, so a conflict resolved once is replayed on the layers above.
5. Run `validate-commit` on each upstack branch.
6. Run `gh stack push`. It is not atomic. If it fails part-way, re-run it unchanged.
7. When a PR merges or closes, its branch state is deleted as described in 0001 D4.

`gh stack push` is used instead of `gh stack sync` for pushing because sync belongs at the start of maintenance (step 1), where it picks up remote changes.

### D2. Depth cap

The cap on released-but-unmerged layers is defined in 0001 D3 and is not repeated here.

## Consequences

- Maintenance has no automation. Every review cycle is run by hand, and a change low in a deep stack costs one rebase and one `validate-commit` per layer above it.
- Branch state is read-only after `RELEASED`, so maintenance edits never touch `state.json`. The drift check in step 2 is the only guard against editing on a stale parent.
- Anything the procedure needs beyond `gh stack` is the host's own editing and the existing skills.

## Open items

| # | Item | Status | What closes it |
| :-- | :-- | :-- | :-- |
| 1 | `gh stack rebase --upstack` after a parent was squash-merged | Unverified | Scratch-repo trial |
| 2 | Review-comment automation | Deferred | Port `pr-address-comments` (dropping its host-specific tools and using `gh stack push`) if needed |
| 3 | `gh stack rebase --upstack` rebases the current layer onto its parent (step 2), not only the layers above it | Unverified | Scratch-repo trial |
