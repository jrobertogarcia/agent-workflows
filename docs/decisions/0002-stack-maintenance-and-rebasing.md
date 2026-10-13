# 0002. Manual stack maintenance and cascade rebasing

**Status**: Proposed
**Date**: 2026-10-13

## Context

[ADR 0001](0001-orchestrator-subagents.md) authors a stack and stops each layer at `RELEASED`: the layer's PR is open with the correct base. After that point reviewers comment, parents change, and parents merge. Applying that feedback and keeping the layers above a changed layer consistent is stack maintenance.

Maintenance is human-owned and manual. No skill implements it. It uses `gh stack`, which 0001 D3 makes a hard dependency, together with the host's normal editing and the existing `validate-commit` and `create-commit` skills.

## Decision

### D1. Maintenance procedure

Once per clone: `git config rerere.enabled true`. A non-interactive `gh stack init` does not enable it.

For a review comment on any released layer:

1. Run `gh stack checkout`, then `gh stack sync`. The output must end `Stack synced`. `Branches synced`, `Push failed`, or `not in your local stack` mean local and remote disagree despite exit 0. Resolve that before editing.
2. Confirm the layer contains its parent's tip: `git merge-base --is-ancestor <parent> HEAD`. If that fails, run `gh stack rebase --upstack`, which rebases the current layer and then those above. It builds on the local parent as-is, even if the remote parent was rewritten. This check uses git only and does not read `state.json`.
3. Apply the review comments with the host's normal editing, then run `validate-commit` and `create-commit`.
4. Run `gh stack rebase --upstack` to rebase every layer above.
5. Run `validate-commit` on each upstack branch.
6. Push guard: run `git fetch origin`. For each layer, `git merge-base --is-ancestor origin/<b> <b>` must succeed. Otherwise stop and integrate the remote commits. Then run `gh stack push`. It force-pushes with a lease taken from its own fetch, so without this check it silently overwrites remote-only commits. Retry a failed push from the fetch.
7. Merge: a human merges the bottom layer with `gh stack merge <pr> --squash|--rebase|--merge --yes` (web UI unverified). `gh pr merge` is refused for stacked PRs. GitHub retargets the next PR and rewrites the remaining branches server-side, so the next maintenance starts at step 1. Afterwards `git log origin/<trunk>..HEAD` on each layer must list only that layer's commits. Otherwise run `git rebase --onto origin/<trunk> <old parent tip>`.
8. When a PR merges or closes, its branch state is deleted as described in 0001 D4.

### D2. Depth cap

The cap on released-but-unmerged layers is defined in 0001 D3 and is not repeated here.

### D3. Automation

None. If maintenance is automated later, it is a new stack-aware skill, not a port of `pr-address-comments`.

## Consequences

- Maintenance has no automation. Every review cycle is run by hand, and a change low in a deep stack costs one rebase and one `validate-commit` per layer above it.
- Maintenance never touches `state.json`. The guards are the sync output, the parent check, the pre-push remote check, and the post-merge log. A remote commit pushed between the fetch and the push is still lost.
- Anything the procedure needs beyond `gh stack` is the host's own editing and the existing skills.

## Open items

| # | Item | Status | What closes it |
| :-- | :-- | :-- | :-- |
| 1 | Maintenance automation | Deferred | A new stack-aware skill (D3) |
| 2 | Web-UI merge of a stacked PR | Unverified (`gh stack merge` observed for all three methods) | Merge one layer in the UI, then run the step 7 check |
| 3 | `gh stack push` partial failure | Unverified ("not atomic" from its help text) | Trial with a protected layer branch |
