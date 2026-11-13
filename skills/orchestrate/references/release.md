# Orchestrate: Release Text

It extends the orchestrate `SKILL.md`, the core, whose terms, paths, Halt, and BLOCKED rules apply here; each section names where the skill points to it.

## Draft

Run when `AUDITING` leaves for Gate 2 (`B` `APPROVE`, or per `<review-fix>`), and from Gate 2 or Release when `S/<branch>/pr-draft.md` is missing or its `Branch tip:` differs from `approved_sha`.

- Dispatch `draft`.
- The result is transient per Result in `<dispatch>` when `pr-draft.md` fails any of: first line `Branch tip: <approved_sha>`, second line `Missing links: …`, third line `Title: …`, a blank line, then a non-empty body.
- The body's shape is `create-pr`'s to enforce: the `draft` worker checks it against that skill's body bounds and the chosen template, so do not re-check it here.
- Then write `WAITING_RELEASE_APPROVAL`; `retry` after a `draft` BLOCKED re-runs `draft`.

## Gate 2

- Unattended per `<boot>`: when the stop conditions in `<resolve>` do not apply, record the auto-answer, set `gate_2_release_approved`, and go to Release without presenting; otherwise present as attended.
- **Presentation**: also present `pr-draft.md`'s title and body verbatim, and its `Missing links` line when it is not "none". When `comments.md` exists, also present `git log --oneline --cherry-pick --right-only origin/<branch>...HEAD --not <base_sha>`, this round's commits (rebased ones left out), then run Replies per `<comments>` and present `replies.md` verbatim too. There, `fix <n>` selects review findings, not comments; change a comment's reply with `fix small:` or `fix large:` and direction.
- **Re-presentation**: the first presentation in a thread is complete, and so is the first after a context summary. A later one always shows `pr-draft.md`'s title and body verbatim, and `Missing links` when not "none"; otherwise only what changed since the last presentation in this thread: `git log --oneline <last presented HEAD>..HEAD` instead of the diff stat when `HEAD` moved, findings per Findings in `<resolve>`, `handover.md` only when `A2` rewrote it, and `replies.md` only when Replies rewrote it. Name each unchanged part with its path, such as "findings unchanged: <review.md path>".
- **`redraft <feedback>`**, when `HEAD` equals `approved_sha` (otherwise handle it as Gate 2 handles a moved `HEAD`):
  - Set `gate_2_release_approved` false.
  - Dispatch `draft` with the feedback verbatim and the current `pr-draft.md`.
  - Present Gate 2 again.
  - Not counted, no fix pass, and the feedback is recorded per Decisions in `<boot>`.

## Release

With `gate_2_release_approved` true and `HEAD` equal to `approved_sha` (else enter `IMPLEMENTING`, not counted, which clears the flag), and the Precondition below:

1. Restack per `<comments>`. Read `gh pr view <branch> --json number,state,baseRefName,headRefOid`. One reading `MERGED` at `approved_sha` goes to step 4. An open one with a base other than `<target>` halts when `<target>` is `<trunk>`. Unless an open one is at `approved_sha` with text matching `pr-draft.md` (per Step 1 below), dispatch `release` with `R` = the SHA `git ls-remote origin refs/heads/<branch>` prints, if any. When `R` is set, first `git fetch origin <branch>` and halt if `git cherry approved_sha R` prints a `+` line: "origin/<branch> holds commits not in the approved tip; integrate them, unless they are a merged lower layer's original commits, then force-push with `git push --force-with-lease=refs/heads/<branch>:<R> origin <approved_sha>:refs/heads/<branch>` yourself; then re-invoke." `PUSHED` logs it with `approved_sha` and reports the approved title and body for the human to open the pull request against `<target>`; the next invocation resumes here.
2. **Link**, when `<target>` is a layer: per `<stacked>`.
3. **RELEASED check**: a fresh `gh pr view` shows `OPEN` with `baseRefName` equal to `<target>` and `headRefOid` equal to `approved_sha`. When `unattended` is set, also read `isDraft`; `false` fails the check, reported without BLOCKED like other Release check failures: the pull request was not opened as a draft, so reviewers may already be notified; the human runs `gh pr ready --undo <number>` and re-invokes. After a link, also run Stack membership in `<stacked>`. Exit codes are not evidence.
4. Write `state.json` `RELEASED`, then in `stack.json` the layer's `pr` and `RELEASED`, moving `active_layer_index` to the next `PENDING` layer if one remains. If it moved, re-run Reconcile and continue at that layer's Branch creation.

A failed `create-pr`, link, or check, including a `release` step returning `STOPPED` or a second transient, does not set `BLOCKED`: append the cause to `roadblocks.md`, leave the phase unchanged, and report; re-run once it is resolved. The flag stays true, and the next invocation resumes at Release.

- **Precondition**: `pr-draft.md`'s `Branch tip:` equals `approved_sha`. Otherwise set `gate_2_release_approved` false, run Draft, and present Gate 2. An unapproved draft is never published.
- **Step 1, an open pull request at `approved_sha`**: read its text with `gh pr view <branch> --json title,body`. Dispatch `release` anyway when its title or body differs from `pr-draft.md`'s, ignoring line endings (CRLF or LF) and trailing whitespace on each line. The push is then a no-op, and `gh pr edit` applies the approved text. This covers a text-only fix after `reopen` and a crash between push and edit. Skip this comparison when `roadblocks.md` logs a `PUSHED` at `approved_sha` and no `reopen:` entry after it: the human opened that pull request by hand, so its text stands, and Release continues at the RELEASED check.
- **Unattended release**, when `unattended` is set: dispatch `release` adding the instruction: "Open the pull request as a draft: pass `--draft` to `gh pr create`. Do not mark it ready." The edit path (`gh pr edit`) and the `PUSHED` end are unchanged; `PUSHED` is a stop, since the worker could not open the pull request.
