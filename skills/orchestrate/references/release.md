# Orchestrate: Release Text

Read this on every run. It extends the orchestrate `SKILL.md`, whose terms, paths, halt, and BLOCKED rules apply here; each section names where that file points to it.

## Draft

Run after `B` `APPROVE`, and from Gate 2 or Release when `S/<branch>/pr-draft.md` is missing or its `Branch tip:` differs from `approved_sha`.

- Dispatch `draft`.
- The result is transient per Result when `pr-draft.md` fails any of: first line `Branch tip: <approved_sha>`, second line `Missing links: …`, third line `Title: …`, a blank line, then a non-empty body.
- It is also transient when the body fails the What bound. The body must have a `## What` heading; without one it fails, unless `git ls-files` lists a path whose name contains `pull_request_template` (any case), where create-pr's step 4 and Gate 2 cover the shape. From that heading up to the next heading, leaving out a trailing link block (create-pr's link block: the body's last blank-line-separated block when none of its lines starts with `- ` or `* ` and each names a `#<number>` or a URL):
  - every non-blank line starts with `- ` or `* `, so wrapped paragraphs, numbered lists, and nested bullets fail;
  - there are at most 6 such lines;
  - no line is over 160 characters, counted after stripping a trailing CR.
- Then, when `comments.md` exists, run Replies per `<comments>`.
- Then write `WAITING_RELEASE_APPROVAL`; `retry` after a `draft` BLOCKED re-runs `draft`.

## Gate 2

- **Presentation**: also present `pr-draft.md`'s title and body verbatim, and its `Missing links` line when it is not "none". When `comments.md` exists, first run Replies per `<comments>`, then present `replies.md` verbatim too.
- **`redraft <feedback>`**, when `HEAD` equals `approved_sha` (otherwise handle it as Gate 2 handles a moved `HEAD`):
  - Set `gate_2_release_approved` false.
  - Dispatch `draft` with the feedback verbatim and the current `pr-draft.md`.
  - Present Gate 2 again.
  - Not counted, no fix pass, and the feedback is not persisted.

## Release

- **Precondition**: `pr-draft.md`'s `Branch tip:` equals `approved_sha`. Otherwise set `gate_2_release_approved` false, run Draft, and present Gate 2. When `comments.md` exists, `replies.md`'s `Branch tip:` must also equal `approved_sha`; otherwise set `gate_2_release_approved` false, run Replies per `<comments>`, and present Gate 2. An unapproved draft is never published.
- **Step 1, an open pull request at `approved_sha`**: read its text with `gh pr view <branch> --json title,body`. Dispatch `release` anyway when its title or body differs from `pr-draft.md`'s, ignoring line endings (CRLF or LF) and trailing whitespace on each line. The push is then a no-op, and `gh pr edit` applies the approved text. This covers a text-only fix after `reopen` and a crash between push and edit. Skip this comparison when `roadblocks.md` logs a `PUSHED` at `approved_sha` and no `reopen:` entry after it: the human opened that pull request by hand, so its text stands, and Release continues at the RELEASED check.
