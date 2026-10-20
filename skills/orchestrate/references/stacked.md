# Orchestrate: Stacked Work

Read this when `stack.json` holds more than one layer, or the human replies `register`. It extends the orchestrate `SKILL.md`, whose terms, paths, halt, and BLOCKED rules apply here; each section names where that file points to it.

## Boot

- **Closed layer** (Reconcile, a `CLOSED` layer with a layer above it): halt before deleting, "<PR URL> was closed; reopen it to continue the stack.", and delete only once nothing above depends on it or the human replies `abandon`.
- **Merged target** (end of Reconcile): if the `ACTIVE` layer's `<target>` reads `MERGED`, run Fresh trunk and write `target_branch` = `<trunk>`; drift check 4 then rebases it.
- **Upstack rebase** (drift check 4, when `<target>` is a layer): run the Tracking check and `gh stack rebase --upstack <branch> --no-trunk`.

## Phases

- **Split approval** (`WAITING_SPLIT_APPROVAL`): present each layer's branch and scope and stop for the human: `narrow` per below; `approve` continues only after these checks:
  - `gh stack --version` reports 0.2.1 or later and `git --version` 2.36 or later, else halt: "Stacked work needs gh-stack v0.2.1 or later and Git 2.36 or later (found <versions, or none>): run `gh extension install github/gh-stack` or `gh extension upgrade gh-stack`, or upgrade Git."
  - The first line of `gh api --include 'repos/{owner}/{repo}/stacks'` reports status 200, else halt: "Stacked pull requests are unavailable for this repository (status <status>); they need github.com. Check `gh auth status`, `GH_TOKEN`, `GH_REPO`, and the `origin` remote."

  Either halt also offers to narrow the requirement to one branch. `narrow`: append the narrowed requirement and the note "Exactly one layer." to `requirements.md`, keep only `RELEASED` layers, write `STACK_DECOMPOSITION`, and re-run `decompose`, which follows that note; if it still returns several layers, halt again.
- **`register <PR number>`**, before `LAYERS` with no layer `RELEASED`: `gh pr view <PR> --json state,title,headRefName,baseRefName` must read `OPEN` with base `<trunk>` and a head branch that exists locally, else halt. Insert it as layer 0, `RELEASED` with `pr` and `scope` "registered", renumbering the others, append its title to `requirements.md`, and log it to the stack's `roadblocks.md`.
- **Parent** (Branch creation): the parent is the highest `RELEASED` layer that reads `OPEN` in Reconcile.
- **On a parent** (Branch creation): require the current branch to be the parent, or the branch if it exists, else halt. If a lower layer reads `MERGED`, first: run `git fetch origin`; for each open layer `<b>`, require `git log --oneline --cherry-pick --right-only <b>...origin/<b> --not origin/<trunk>` to be empty, else halt listing the commits to integrate into `<b>`; then run the Tracking check and `gh stack rebase --upstack <lowest open layer>`, and on a conflict run `gh stack rebase --abort` and halt naming the files. Then each open layer `<b>` must equal `origin/<b>`, else halt: "<b> differs from origin/<b>; push the open layers with `git push --atomic origin --force-with-lease=refs/heads/<b>:<SHA> … refs/heads/<b>:refs/heads/<b> …`, then re-invoke.", filling each `<SHA>` with the `origin/<b>` SHA the cherry-pick check read. Next, if the branch does not exist, require the current branch to be the parent, run the Tracking check and `gh stack add <branch>`, and require the current branch to be it and `HEAD` to equal `git rev-parse <parent>`. If it already existed, require instead the current branch to be it and `git rev-list <parent>..HEAD` to be empty. Otherwise halt. `<target>` is the parent.
- **Fresh trunk**: run `git fetch origin <trunk>`. If no worktree in `git worktree list --porcelain` has `<trunk>` checked out, run `git fetch . origin/<trunk>:<trunk>`. Then `<trunk>` must equal `origin/<trunk>`, else halt naming the worktree that has it checked out.
- **Tracking check**: `gh stack view --json` lists every unmerged layer (`ACTIVE`, or `RELEASED` and reading `OPEN`), bottom first and in order, among its `branches[].name`. Otherwise run `gh stack init --base <trunk> <each unmerged layer's branch, bottom first>` and check again; halt if it still fails.

## Release

- **Link** (step 2, when `<target>` is a layer): run `gh stack link --base <trunk> <the PR number of each open layer, bottom first, then this one>`.
- **Stack membership** (step 3, after a link): `gh api 'repos/{owner}/{repo}/stacks?pull_request=<number>'` also lists `<number>` in a stack's `pull_requests[].number`, and for a layer above the first, that same stack also lists the parent layer's PR number.
