# Orchestrate: Release Text

It extends the orchestrate `SKILL.md`, the core, whose terms, paths, Halt, and BLOCKED rules apply here; each section names where the skill points to it.

## Draft

Run when `AUDITING` leaves for Gate 2 (`B` `APPROVE`, or per `<review-fix>`), and from Gate 2 or Release when `S/<branch>/pr-draft.md` is missing or its `Branch tip:` differs from `approved_sha`.

- Dispatch `draft`.
- The result is transient per Result in `<dispatch>` when `pr-draft.md` fails any of: first line `Branch tip: <approved_sha>`, second line `Missing links: …`, third line `Title: …`, a blank line, then a non-empty body.
- It is also transient when the body fails the What bound. The body must have a `## What` heading; without one it fails, unless `git ls-files` lists a path whose name contains `pull_request_template` (any case), where create-pr's step 4 and Gate 2 cover the shape. From that heading up to the next heading, leaving out a trailing link block (create-pr's link block: the body's last blank-line-separated block when none of its lines starts with `- ` or `* ` and each names a `#<number>` or a URL):
  - every non-blank line starts with `- ` or `* `, so wrapped paragraphs, numbered lists, and nested bullets fail;
  - there are at most 6 such lines;
  - no line is over 160 characters, counted after stripping a trailing CR.
- Then write `WAITING_RELEASE_APPROVAL`; `retry` after a `draft` BLOCKED re-runs `draft`.

## Gate 2

- **Presentation**: also present `pr-draft.md`'s title and body verbatim, and its `Missing links` line when it is not "none". Also list `incidental.md`'s entries as `N<n>`, each with its mark if any, with the hint "reply `file`, `defer` or `drop N<n>`". When `comments.md` exists, also present `git log --oneline --cherry-pick --right-only origin/<branch>...HEAD --not <base_sha>`, this round's commits (rebased ones left out), then run Replies per `<comments>` and present `replies.md` verbatim too. There, `fix <n>` selects review findings, not comments; change a comment's reply with `fix small:` or `fix large:` and direction.
- **`redraft <feedback>`**, when `HEAD` equals `approved_sha` (otherwise handle it as Gate 2 handles a moved `HEAD`):
  - Set `gate_2_release_approved` false.
  - Dispatch `draft` with the feedback verbatim and the current `pr-draft.md`.
  - Present Gate 2 again.
  - Not counted, no fix pass, and the feedback is recorded per Decisions in `<boot>`.

## Release

With `gate_2_release_approved` true and `HEAD` equal to `approved_sha` (else enter `IMPLEMENTING`, not counted, which clears the flag), and the Precondition below:

1. Restack per `<comments>`. Read `gh pr view <branch> --json number,state,baseRefName,headRefOid`. One reading `MERGED` at `approved_sha` goes to step 4. An open one with a base other than `<target>` halts when `<target>` is `<trunk>`. Unless an open one is at `approved_sha` with text matching `pr-draft.md` (per Step 1 below), dispatch `release` with `R` = the SHA `git ls-remote origin refs/heads/<branch>` prints, if any. When `R` is set, first `git fetch origin <branch>` and halt if `git cherry approved_sha R` prints a `+` line: "origin/<branch> holds commits not in the approved tip; integrate them, unless they are a merged lower layer's original commits, then force-push with `git push --force-with-lease=refs/heads/<branch>:<R> origin <approved_sha>:refs/heads/<branch>` yourself; then re-invoke." `PUSHED` logs it with `approved_sha` and reports the approved title and body for the human to open the pull request against `<target>`; the next invocation resumes here.
2. **Link**, when `<target>` is a layer: per `<stacked>`.
3. **RELEASED check**: a fresh `gh pr view` shows `OPEN` with `baseRefName` equal to `<target>` and `headRefOid` equal to `approved_sha`. After a link, also run Stack membership in `<stacked>`. Exit codes are not evidence.
4. Write `state.json` `RELEASED`, then in `stack.json` the layer's `pr` and `RELEASED`, moving `active_layer_index` to the next `PENDING` layer if one remains. If it moved, re-run Reconcile and continue at that layer's Branch creation.

A failed `create-pr`, link, or check, including a `release` step returning `STOPPED` or a second transient, does not set `BLOCKED`: append the cause to `roadblocks.md`, leave the phase unchanged, and report; re-run once it is resolved. The flag stays true, and the next invocation resumes at Release.

- **Precondition**: `pr-draft.md`'s `Branch tip:` equals `approved_sha`. Otherwise set `gate_2_release_approved` false, run Draft, and present Gate 2. An unapproved draft is never published.
- **Step 1, an open pull request at `approved_sha`**: read its text with `gh pr view <branch> --json title,body`. Dispatch `release` anyway when its title or body differs from `pr-draft.md`'s, ignoring line endings (CRLF or LF) and trailing whitespace on each line. The push is then a no-op, and `gh pr edit` applies the approved text. This covers a text-only fix after `reopen` and a crash between push and edit. Skip this comparison when `roadblocks.md` logs a `PUSHED` at `approved_sha` and no `reopen:` entry after it: the human opened that pull request by hand, so its text stands, and Release continues at the RELEASED check.
- **Trivial release**, while the pass is trivial per `<review-fix>`:
  - Skip the Precondition and Step 1's text comparison. Run Replies per `<comments>` when `replies.md` is missing or stale.
  - Dispatch `release` with no `pr-draft.md`, adding the instruction: "No `pr-draft.md` is given: ignore the instructions that use its title and body, and skip `gh pr edit`. Push only and open no pull request; with one open, end `DONE`." Restack, the lease list, and Atomic Push are unchanged.
  - Skip the dispatch only when an open pull request is already at `approved_sha` and Atomic Push does not require it.
