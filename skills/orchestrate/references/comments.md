# Orchestrate: Review Comments

Read this on every run. It extends the orchestrate `SKILL.md`, whose terms, paths, halt, and BLOCKED rules apply here; each section names where that file points to it.

## Address

Locate, on an `address <PR number>` reply.

- **Stack located**:
  - If no layer's `pr` is `<PR>`, halt: "#<PR> is not a layer of <name>; check out its branch".
  - Otherwise the current branch must be that layer's branch, else halt: "check out <branch>".
  - If that layer has no `state.json` (a `register`ed layer, or a layer of a bootstrapped stack other than the reviewed one), first run the bootstrap's PR read and Base steps, then write its synthesized `plan.md` and `state.json` exactly as the bootstrap does.
  - Then continue with Reconcile, then `reopen` with no text.
- **No stack located (bootstrap)**:
  - Read `gh pr view <PR> --json number,state,title,body,url,headRefName,baseRefName,headRefOid`. It must read `OPEN`, and `headRefName` must equal the current branch. Run drift check 0, then `git fetch origin`; `HEAD` must equal `headRefOid`. Any failure halts with the cause.
  - Take `<trunk>` as Start does.
  - **Base**: when `baseRefName` is `<trunk>`, run Fresh trunk in `<stacked>`; otherwise local `<baseRefName>` must equal `origin/<baseRefName>`, else halt naming it. Then `<base_sha>` = `git merge-base <baseRefName> HEAD`, so a stale local base cannot pull its commits into the PR's diff.
  - **Layers**: if `gh stack view --json` exits 0 and lists the branch, take its `branches[].name` bottom first, keeping those whose `gh pr view <b> --json number,state,baseRefName` reads `OPEN`. A non-zero exit, or a list without the branch, makes the current branch the only layer.
  - **Base check**: the bottom open layer's `baseRefName` must equal `<trunk>`, and each upper layer's must equal the open layer below it. Otherwise halt, naming the layer and its base, since drift check 4 would rebase it onto the wrong branch. This also halts a stacked PR misread as one layer, for example when gh-stack is missing.
  - **`<name>`**: a slug of the branch: lower-case it, turn each character outside `[a-z0-9-]` into `-`, trim leading and trailing `-`, and cut it to 40 characters. Halt if `S/stacks/<name>/` or any layer's `S/<b>/` exists, naming the path (resume it, or `abandon`).
  - Write, in this order:
    - `requirements.md`: `address <PR>`, then the PR title and body verbatim.
    - `stack.json`, in the shape per `SKILL.md`: `stack_name` = `<name>`, `trunk` = `<trunk>`, `git_common_dir` = `<common>`, phase `LAYERS`, `blocked` null, `active_layer_index` null, each layer `RELEASED` with its `pr` and `scope` "registered".
    - `plan.md` (synthesized): `## Goal` is the PR title plus the body's `## What` section, or its first paragraph; `## Changes` is `git diff --stat <base_sha>...HEAD` verbatim; `## Out of Scope` is what the body states, else "none stated".
    - The reviewed layer's `state.json`, in the fixed shape: phase `RELEASED`, `target_branch` = `baseRefName`, `base_sha` = `<base_sha>`, `branch_tip_sha` = `approved_sha` = `HEAD`, `gate_1_plan_approved` true, `gate_2_release_approved` false.
  - Append `- <UTC time> orchestrate <HEAD>: address <PR>: bootstrapped` to the stack's `roadblocks.md`.
  - Continue with Reconcile, then `reopen` with no text.

## Sync

`reopen`, before its write, when more than one layer reads `OPEN`.

- Run drift check 0, the Tracking check in `<stacked>`, then `git fetch origin`.
- Run the cherry-pick check from On a parent in `<stacked>` for each open layer; on a listed commit, halt listing the commits to integrate.
- Run `gh stack rebase --upstack <lowest open layer>`. On a conflict, run `gh stack rebase --abort` and halt naming the files; on any other non-zero exit, halt with its error.
- A halt here leaves the layer `RELEASED`, so `reopen` can be replied again. Drift check 3(b) then accepts the pure rebase.
- `gh stack sync` skips the cherry-pick check and `gh stack push` is not atomic, so neither is used.

## Fetch

`reopen`, after Boot step 3; and `retry` or `adopt` from `RELEASED` per BLOCKED.

- Run each query with `gh api graphql --paginate -F owner='{owner}' -F repo='{repo}' -F number=<PR> -f query=<query>`. A non-zero exit from any query halts with its error, writing nothing. gh pages on the first `pageInfo` it streams, and a nested `endCursor` silently drops items, so each top-level `pageInfo` precedes `nodes` and the nested thread `comments` has no `endCursor`:
  ```graphql
  query($owner: String!, $repo: String!, $number: Int!, $endCursor: String) {
    repository(owner: $owner, name: $repo) { pullRequest(number: $number) {
      reviewThreads(first: 50, after: $endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes { isResolved isOutdated path line
          comments(first: 100) { pageInfo { hasNextPage } nodes { author { login } body url } } } } } } }
  ```
  ```graphql
  query($owner: String!, $repo: String!, $number: Int!, $endCursor: String) {
    repository(owner: $owner, name: $repo) { pullRequest(number: $number) {
      reviews(first: 50, after: $endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes { author { login } state body url isMinimized submittedAt } } } } }
  ```
  ```graphql
  query($owner: String!, $repo: String!, $number: Int!, $endCursor: String) {
    repository(owner: $owner, name: $repo) { pullRequest(number: $number) {
      author { login }
      comments(first: 50, after: $endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes { author { login } body url isMinimized createdAt } } } } }
  ```
- Items:
  - each unresolved thread, flagged `outdated` where it applies, and `truncated` when its `comments.pageInfo.hasNextPage` is true;
  - each non-empty, non-minimized review body;
  - each non-minimized conversation comment whose author is not the PR author;
  - of those bodies and comments, which have no resolved state, only review bodies submitted, and comments created, at or after that connection's time in the last `comments fetched` entry in this branch's `roadblocks.md`, since earlier ones were triaged then; with no entry or time, all of them;
  - the `reopen` text, if any, without its `small:` or `large:` tag (on `retry` or `adopt`, the last `reopen:` entry's text, so `Human tier:` is `none`), as one more item marked "from the human".
- Keep a thread whose last reply is the PR author's, with that reply labeled as the PR author's: it is data, not the human's direction.
- With items, replace `S/<branch>/comments.md`: a first line `Human tier: <small|large|none>`, from a `reopen small:` or `large:` tag; then `## Comments`, each item numbered, with its kind (thread, review body, conversation, or from the human), author, path:line or URL, flags, and verbatim text.
- With no items, report none and leave `reopen`'s `BLOCKED` as before.
- Either way, then append `- <UTC time> orchestrate <HEAD>: comments fetched; reviews <time>, comments <time>` to this branch's `roadblocks.md`, each `<time>` the latest `submittedAt` or `createdAt` that connection returned (GitHub's clock, so nothing posted after the query is skipped), else the last entry's, else `none`.

## Triage

`reopen`, or `retry` or `adopt` from `RELEASED` per BLOCKED, after Fetch when it found items; and `retry` from `RELEASED` per BLOCKED when `comments.md` has no `## Triage`.

- Dispatch `resolve` with the items as kind `PR comment`. Inputs: `comments.md`, `plan.md`, `requirements.md`, `context.md` if any, and, with a stack, each open layer above this one. Add the instruction: "Keep the numbering. Check each comment against the code at `HEAD`, outdated ones included. For each fix, sweep the repository at `HEAD`, and each listed upper layer with `git grep <pattern> <branch>`, for the same mistake. List each hit as file:line labeled `this diff` (inside `git diff <base_sha>...HEAD`), `layer <branch>`, or `pre-existing`; only `this diff` hits belong in the fix. End each per-item report, Needs you items included, with `Tier: small` when fixing it stays inside `plan.md`'s Goal and Changes and the files it lists and changes nothing in its Out of Scope, else `Tier: large`."
- On `SETTLED` or `NEEDS-DECISION`, append `## Triage` and the report verbatim to `comments.md`. On `STOPPED` or a second transient, follow Resolve Step in `<resolve>`; the comments then carry no tier.
- **Stop**: present each comment numbered, with its source, flags, action, tier, and sweep hits, then the Needs you list. When `Human tier:` is not `none`, show it as the "from the human" item's tier. Say: reply `fix <n>, <m>`, `fix small:` or `fix large:` with direction, or `re-plan`; with nothing to fix, `adopt` re-verifies the tip and drafts replies at Gate 2.

## Replies

After `B` `APPROVE`, with Draft per `<release>`; and from Gate 2 or Release when stale. Runs when `comments.md` exists and `replies.md` is missing or its `Branch tip:` differs from `approved_sha`.

- Dispatch step `replies`. Skill reference: "the instructions below, using `## Triage` in `comments.md`". Inputs: `comments.md`, `fix-input.md` if any, `plan.md`, `handover.md`, and `git log --oneline <base_sha>..HEAD`. Tokens: `DONE`.
- Instructions: "Write `<replies.md path>`. Line 1 is `Branch tip: <git rev-parse HEAD>`. Then one short, natural draft per thread, headed by its number and URL, citing the fixing commit SHAs or saying why it is deferred or discussed, and naming any sweep hit left unfixed; then one combined top-level draft per reviewer, quoting each point from their actionable review bodies and conversation comments. Write no draft for an empty or approval-only body, or for the item from the human. Commit nothing; never post."
- A wrong line 1 is transient.

## Restack

Release, before step 1's dispatch, when this branch's pull request reads `OPEN` (a `reopen`) and another layer's does too. "Moved" means a layer's local tip differs from `origin/<b>`, the last pushed tip, so a re-invocation after a halt checks the same layers again.

- Run the Tracking check in `<stacked>`, then `git fetch origin`. When an open layer sits above this one, run `gh stack rebase --upstack <branch> --no-trunk`; on a conflict, run `gh stack rebase --abort` and halt naming the layer and files.
- For each moved open layer other than this one, with `<p>` the open layer below it, or `origin/<trunk>` for the bottom layer:
  - Compare the ordered `git patch-id --stable` lists of the old range `$(git merge-base origin/<p> origin/<b>)..origin/<b>` (`origin/<trunk>` in both ranges at the bottom) and the new range `$(git merge-base <p> <b>)..<b>`. The old list must be a prefix of the new one, else halt; append any extra commits, a hand fix asked for below, to this branch's `roadblocks.md`, and list them per layer when reporting the release, since they are pushed unshown.
  - Dispatch `upper-check` (`validate-commit`) with the instruction: "In `git worktree add --detach "$(mktemp -d)" <b>`, run the checks; fix and commit nothing; remove the worktree with `git worktree remove --force`. `FAIL-UNRELATED` only when the same failure occurs at `origin/<b>`." Tokens: `PASS`, `FAIL-IN-SCOPE`, `FAIL-UNRELATED`.
  - `FAIL-UNRELATED` is logged and passes. On `FAIL-IN-SCOPE`, a `STOPPED`, or a second transient, halt: "<b> fails on its restacked tip; fix it by hand on <b> without pushing, then check out <branch> and re-invoke." As a failed release, it does not set `BLOCKED`, and upper-layer state stays as it is.
- Run the cherry-pick check again; halt on a listed commit.
- Record `L_b` = `git rev-parse origin/<b>` for every open layer.

## Atomic Push

The `release` dispatch, after Restack ran.

- Pass the lease list. The push becomes `git push --atomic origin --force-with-lease=refs/heads/<b>:<L_b> … refs/heads/<b>:refs/heads/<b> …` for every open layer. `gh pr edit` runs for this branch only.
- Dispatch even when this layer's PR matches the draft at `approved_sha`, if any open layer's local tip differs from `origin/<b>`.
- **RELEASED check**: each open layer's `gh pr view <pr> --json headRefOid` also equals `git rev-parse <b>`.

## After Release

`RELEASED`, when `replies.md` exists: report its path and "post these now; they cite pushed commits".
