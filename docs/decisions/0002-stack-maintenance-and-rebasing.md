# 0002. Manual stack maintenance and cascade rebasing

**Status**: Proposed
**Date**: 2026-10-13

## Context

[ADR 0001](0001-orchestrator-subagents.md) authors a stack and stops each layer at `RELEASED`: the layer's PR is open with the correct base. After that point reviewers comment, parents change, and parents merge. Applying that feedback and keeping the layers above a changed layer consistent is stack maintenance.

Maintenance is human-owned and manual. No skill implements it. It runs only while no orchestrator run is acting on the stack (D1), and it never writes `stack.json` or `state.json`; the orchestrator re-anchors on its next boot ([0001 D10](0001-orchestrator-subagents.md) step 3b). It uses `gh stack`, which 0001 D3 makes a hard dependency, together with the host's normal editing and the existing `validate-commit` and `create-commit` skills.

## Decision

### D1. Maintenance procedure

**Precondition**: no orchestrator run is acting on the stack. That means no layer is `ACTIVE`, or the active layer's phase is `WAITING_PLAN_APPROVAL`, `WAITING_RELEASE_APPROVAL`, or `BLOCKED`. Read `stack.json` and `state.json` to check this; write neither.

Once per clone: `git config rerere.enabled true`. A non-interactive `gh stack init` does not enable it (observed).

A layer checked out in a linked worktree can be edited only in that worktree. `gh stack rebase --upstack` refuses while any affected worktree is dirty and rebases a clean one in place (observed).

For a review comment on any released layer:

1. Run `gh stack checkout`, then `git fetch origin`. For each unmerged layer `<b>`, `git log --oneline --cherry-pick --right-only <b>...origin/<b> --not origin/<trunk>` must be empty. Otherwise stop and integrate the remote commits. After a merge, GitHub's server-side rewrite carries a remote-only commit into the layers above, so the check reports it on each of them (observed after merge-commit, squash, and rebase merges). Then run `gh stack rebase --upstack` from the bottom layer. It fast-forwards trunk and skips merged layers (observed after merge-commit and rebase merges; gh-stack issue #512, replay of merged commits from a stale local branch, did not reproduce). Do not run `gh stack sync` or `gh stack push` in maintenance: both force-push with leases taken from their own fetch, and `push` is not atomic.
2. Confirm the layer contains its parent's tip: `git merge-base --is-ancestor <parent> HEAD`. If that fails, stop. This check uses git only and does not read `state.json`.
3. Apply the review comments with the host's normal editing, then run `validate-commit` and `create-commit`.
4. Run `gh stack rebase --upstack` to rebase every layer above.
5. Run `validate-commit` on each upstack branch.
6. Push: run `git fetch origin`, then the step 1 check. Record `git rev-parse origin/<b>` for every unmerged layer. Then run one atomic push over all unmerged layers with no fetch in between:
   `git push --atomic --force-with-lease=refs/heads/<b>:<sha> ... origin refs/heads/<b>:refs/heads/<b> ...`
   Afterwards `git ls-remote origin` must equal each local tip. A rejection pushes nothing (exit 1); retry from the fetch.
7. Merge: a human merges the bottom layer with `gh stack merge <pr> --squash|--rebase|--merge --yes`. A bare number is tried as a stack number first, then as a PR number, so confirm it does not collide with a stack number. `gh pr merge` and the plain REST `PUT pulls/<n>/merge` are refused for stacked PRs (403); `PUT pulls/<n>/merge-async` with `merge_method` `merge|squash|rebase` works (observed). After each merge GitHub retargets the next PR to trunk and rewrites the branches above (observed for all three methods), so the next maintenance starts at step 1. Afterwards `git log origin/<trunk>..HEAD` on each layer must list only that layer's commits (observed). Otherwise run `git rebase --onto origin/<trunk> <merged PR headRefOid>` (observed working). Use the PR's `headRefOid`, because after a rebase merge neither the local branch nor trunk holds that layer's SHAs.
8. When a PR merges or closes, its branch state is deleted as described in 0001 D4.

### D2. Depth cap

The cap on released-but-unmerged layers is defined in 0001 D3 and is not repeated here.

### D3. Automation

None. If maintenance is automated later, it is a new stack-aware skill, not a port of `pr-address-comments`.

## Consequences

- Maintenance has no automation. Every review cycle is run by hand, and a change low in a deep stack costs one rebase and one `validate-commit` per layer above it.
- Maintenance runs only while no orchestrator run is acting on the stack, and never writes a state file. The guards are the remote-only-commit check before rebase and before push, the parent check, and the post-merge log.
- The atomic push with per-ref leases pushes all layers or none. A remote commit pushed after the fetch makes the push fail with "stale info" and nothing is pushed (observed). A layer protected by a ruleset makes the push reject every ref with nothing pushed (observed). `gh stack push` under the same protection updated five branches, rejected one, exited 1, and left the remote stack inconsistent (observed).
- Anything the procedure needs beyond `gh stack` and git is the host's own editing and the existing skills.

## Open items

| # | Item | Status | What closes it |
| :-- | :-- | :-- | :-- |
| 1 | Maintenance automation | Deferred until one authored stack has been maintained by hand and the procedure proves error-prone | A read-only stack-check as the first scope (D3) |
| 2 | Web-UI merge of a stacked PR (the API path is observed for all three methods) | Unverified | Merge one layer in the web UI, then run the step 1 and step 7 checks |
| 3 | Auto-merge for stacks | Untested | Trial |
