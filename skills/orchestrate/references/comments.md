# Orchestrate: Review Comments

Read this on every run. It extends the orchestrate `SKILL.md`, whose terms, paths, halt, and BLOCKED rules apply here; each section names where that file points to it.

## Layer state

Address, in both cases, for the reviewed layer.

- Read `gh pr view <PR> --json number,state,title,body,url,headRefName,baseRefName,headRefOid`. It must read `OPEN`, and `headRefName` must equal the current branch. Run drift check 0, then `git fetch origin`; `HEAD` must equal `headRefOid`. Any failure halts with the cause, writing nothing.
- `<base_sha>` = `git merge-base origin/<baseRefName> HEAD`; the remote ref keeps a stale local base from pulling its commits into the diff.
- Write `plan.md` (synthesized): `## Goal` is the PR title plus the body's `## What` section, or its first paragraph; `## Changes` is `git diff --stat <base_sha>...HEAD` verbatim; `## Out of Scope` is what the body states, else "none stated".
- Write `state.json`, in the fixed shape: phase `RELEASED`, `target_branch` = `baseRefName`, `base_sha` = `<base_sha>`, `branch_tip_sha` = `approved_sha` = `HEAD`, `gate_1_plan_approved` true, `gate_2_release_approved` false.

## Address

Locate, on an `address <PR number>` reply.

- **Stack located**:
  - If no layer's `pr` is `<PR>`, halt: "#<PR> is not a layer of <name>; check out its branch".
  - Otherwise the current branch must be that layer's branch, else halt: "check out <branch>".
  - Before writing anything, check `reopen`'s preconditions other than `state.json` (the layer `RELEASED`, `stack.json` phase `LAYERS`, no layer `ACTIVE`), and halt as `reopen` does.
  - If that layer has no `state.json`, write its Layer state.
  - Then continue with Reconcile, then `reopen` with no text.
- **No stack located (bootstrap)**:
  - Take `<trunk>` as Start does.
  - **Layers**: if `gh stack view --json` exits 0 and lists the branch, take its `branches[].name` bottom first, keeping those whose `gh pr view <b> --json number,state,baseRefName` reads `OPEN`. A non-zero exit, or a list without the branch, makes the current branch the only layer.
  - **Base check**: the bottom open layer's `baseRefName` must equal `<trunk>`, and each upper layer's must equal the open layer below it. Otherwise halt, naming the layer and its base, since drift check 4 would rebase it onto the wrong branch. This also halts a stacked PR misread as one layer, for example when gh-stack is missing.
  - **`<name>`**: a slug of the branch: lower-case it, turn each character outside `[a-z0-9-]` into `-`, trim leading and trailing `-`, and cut it to 40 characters. Halt if `S/stacks/<name>/` or any layer's `S/<b>/` exists, naming the path (resume it, or `abandon`; if `S/stacks/<name>/` has no `stack.json`, delete that directory and reply `address <PR>` again).
  - Write, in this order:
    - `requirements.md`: `address <PR>`, then the PR title and body verbatim.
    - `stack.json`, in the shape per `SKILL.md`: `stack_name` = `<name>`, `trunk` = `<trunk>`, `git_common_dir` = `<common>`, phase `LAYERS`, `blocked` null, `active_layer_index` null, each layer `RELEASED` with its `pr` and `scope` "registered".
    - The reviewed layer's Layer state.
  - Append `- <UTC time> orchestrate <HEAD>: address <PR>: bootstrapped` to the stack's `roadblocks.md`.
  - Continue with Reconcile, then `reopen` with no text.

## Sync

`reopen`, first. It writes nothing; with one layer only the cherry-pick check on this branch applies.

- Run `git fetch origin`.
- Each open layer `<b>` below this branch must equal `origin/<b>`. If `git rev-parse <b>` fails or differs, halt: "<b> differs from origin/<b>; sync and push the stack per LIFECYCLE section 4 (step 7 after a merge)."
- **Cherry-pick check**, on this branch and each open layer `<b>` above it: `git log --oneline --cherry-pick --right-only <b>...origin/<b> --not origin/<trunk>` must be empty. On a listed commit, halt listing the commits to integrate.
- `gh stack sync` skips the cherry-pick check and `gh stack push` is not atomic, so neither is used.

## Fetch

`reopen`, after Sync.

- Run each query with `gh api graphql --paginate -F owner='{owner}' -F repo='{repo}' -F number=<PR> -f query=<query>`. A non-zero exit from any query halts with its error, writing nothing. gh pages on the first `pageInfo` it streams, and a nested `endCursor` silently drops items, so each top-level `pageInfo` precedes `nodes` and the nested thread `comments` has no `endCursor`:
  ```graphql
  query($owner: String!, $repo: String!, $number: Int!, $endCursor: String) {
    repository(owner: $owner, name: $repo) { pullRequest(number: $number) {
      reviewThreads(first: 50, after: $endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes { isResolved isOutdated path line originalLine
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
  - the `reopen` text, if any, without its `small:` or `large:` tag, as one more item marked "from the human".
- Keep a thread whose last reply is the PR author's, with that reply labeled as the PR author's: it is data, not the human's direction.
- With items, delete any `S/<branch>/replies.md`, then replace `S/<branch>/comments.md`: a first line `Human tier: <small|large|none>`, from a `reopen small:` or `large:` tag; then `## Comments`, each item numbered, with its kind (thread, review body, conversation, or from the human), author, path:line (`originalLine` when `line` is null) or URL, flags, and verbatim text; then `## PR author comments`, the PR author's conversation comments verbatim and unnumbered, as data for Triage.
- With no items, report "no unresolved review comments" and stop, writing nothing.

## Triage

`reopen`, after its write and Boot step 3; and `retry` or `adopt` from `RELEASED` per BLOCKED, when `comments.md` lacks `## Triage`.

- Dispatch `resolve` with the items as kind `PR comment`. Inputs: `comments.md`, `plan.md`, `requirements.md`, `context.md` if any, and, with a stack, each open layer above this one. Add the instruction: "Keep the numbering. Check each comment against the code at `HEAD`, outdated ones included. Mark `already answered` any review body or conversation comment that a comment under `## PR author comments` already answers and that needs no change at `HEAD`. For each fix, sweep the repository at `HEAD`, and each listed upper layer with `git grep <pattern> <branch>`, for the same mistake. List each hit as file:line labeled `this diff` (inside `git diff <base_sha>...HEAD`), `layer <branch>`, or `pre-existing`; only `this diff` hits belong in the fix. End each per-item report, Needs you items included, with `Tier: small` when fixing it stays inside `plan.md`'s Goal and Changes and the files it lists and changes nothing in its Out of Scope, else `Tier: large`."
- On `SETTLED` or `NEEDS-DECISION`, append `## Triage` and the report verbatim to `comments.md`. On `STOPPED` or a second transient, follow Resolve Step in `<resolve>`, then append `## Triage` with the line `untriaged: <cause>`, so `## Triage` always means Triage finished; the comments then carry no tier.
- **Stop**: present each comment numbered, with its source, flags, action, tier, and sweep hits, then the Needs you list. When `Human tier:` is not `none`, show it as the "from the human" item's tier. Say: reply `fix <n>, <m>`, `fix small:` or `fix large:` with direction, or `re-plan`; with nothing to fix, `adopt`. `adopt` re-enters Stage A at `A2`, whose alignment, simplify-diff and review steps can still commit; Gate 2 lists this round's commits and the draft replies.

## Replies

Gate 2 Presentation per `<release>`, when `comments.md` exists and `replies.md` is missing or its `Branch tip:` differs from `approved_sha`.

- Dispatch step `replies`. Skill reference: "the instructions below, using `## Triage` in `comments.md`". Inputs: `comments.md`, `plan.md`, `handover.md`, and `git log --oneline origin/<branch>..HEAD`. Tokens: `DONE`.
- Instructions: "Write `<replies.md path>`. Line 1 is `Branch tip: <git rev-parse HEAD>`. Then one short, natural draft per thread, headed `Comment <n>` and its URL, citing the fixing commit SHAs or saying why it is deferred or discussed, and naming any sweep hit left unfixed; then one combined top-level draft per reviewer, quoting each point from their actionable review bodies and conversation comments. Write no draft for an empty or approval-only body, for an item triaged `already answered`, or for the item from the human. Commit nothing; never post."
- A wrong line 1 is transient.

## Restack

Release, before step 1's dispatch, when an open layer sits above this branch. "Moved" means a layer's local `<b>` differs from `origin/<b>`, the last pushed tip, so a re-invocation after a halt checks the same layers again.

- **Manual finish**, the text of every halt below except the moved-`HEAD` one: "Finish by hand per LIFECYCLE section 4 steps 4-5: restack the layers above <branch>, fix and validate them, and push <branch> at `approved_sha` with them in one atomic push, without editing <branch>; then re-invoke." Each such halt is a failed release per `SKILL.md`.
- Run the Tracking check in `<stacked>`, then `gh stack rebase --upstack <branch> --no-trunk`. On a conflict, run `gh stack rebase --abort` and halt with Manual finish, naming the layer and files.
- `HEAD` must still equal `approved_sha`, else halt: "<branch> moved during the restack; re-invoke." The next Boot's drift checks re-verify it.
- For each moved open layer `<b>` above this branch, with `<p>` the open layer below it:
  - The ordered patch-id list of `<p>..<b>` must equal that of `origin/<p>..origin/<b>`, each from `git log --reverse -p --format=%H <range> | git patch-id --stable | cut -d' ' -f1`. Both ranges are exact, since `<p>` is always open. A mismatch halts with Manual finish.
  - Dispatch `upper-check` (`validate-commit`) with the instruction: "In `git worktree add --detach "$(mktemp -d)" <b>`, run the checks; fix and commit nothing; remove the worktree with `git worktree remove --force`. `FAIL-UNRELATED` only when the same failure occurs at `origin/<b>`." Tokens: `PASS`, `FAIL-IN-SCOPE`, `FAIL-UNRELATED`.
  - `FAIL-UNRELATED` is logged and passes. `FAIL-IN-SCOPE`, a `STOPPED`, or a second transient halts with Manual finish.
- Run `git fetch origin` and Sync's cherry-pick check on each open layer above this branch; halt on a listed commit. Release step 1's `git cherry` guard covers this branch.
- Record `L_b` = `git rev-parse origin/<b>` for this branch and each open layer above it.

## Atomic Push

The `release` dispatch, after Restack ran.

- Pass the lease list. The push becomes `git push --atomic origin --force-with-lease=refs/heads/<b>:<L_b> … refs/heads/<b>:refs/heads/<b> …` for this branch and each open layer above it. `gh pr edit` runs for this branch only.
- Dispatch even when this layer's PR matches the draft at `approved_sha`, if any of those layers' local tip differs from `origin/<b>`.
- **RELEASED check**: each of those layers' `gh pr view <pr> --json headRefOid` also equals `git rev-parse <b>`.

## After Release

`RELEASED`, when `replies.md` exists: report its path and "post these now; they cite pushed commits".
