# Orchestrate: Release Text

Read this on every run. It extends the orchestrate `SKILL.md`, whose terms, paths, halt, and BLOCKED rules apply here; each section names where that file points to it.

## Draft

Run after `B` `APPROVE`, and from Gate 2 or Release when `S/<branch>/pr-draft.md` is missing or its `Branch tip:` differs from `approved_sha`.

- Dispatch `draft`.
- The result is transient (re-run once, then BLOCKED, per Result) when `pr-draft.md` fails any of: first line `Branch tip: <approved_sha>`, second line `Missing links: …`, third line `Title: …`, a blank line, then a non-empty body.
- Then write `WAITING_RELEASE_APPROVAL`. A `draft` that returns `STOPPED` sets `BLOCKED`, and `retry` re-runs `draft`.

## Gate 2

- **Presentation**: also present `pr-draft.md`'s title and body verbatim, and its `Missing links` line when it is not "none".
- **`redraft <feedback>`**, with `gate_2_release_approved` true or false, handled before Gate 2's "flag true and not feedback" check:
  - Set `gate_2_release_approved` false.
  - Dispatch `draft` with the feedback verbatim and the current `pr-draft.md`.
  - Present Gate 2 again.
  - Not counted, no fix pass, and the feedback is not persisted.

## Release

- **Precondition**: `pr-draft.md`'s `Branch tip:` equals `approved_sha`. Otherwise set `gate_2_release_approved` false, run Draft, and present Gate 2. An unapproved draft is never published.
- **Step 1, an open pull request at `approved_sha`**: read its text with `gh pr view <branch> --json title,body`. Dispatch `release` anyway when its title or body differs from `pr-draft.md`'s, ignoring trailing whitespace. The push is then a no-op, and `gh pr edit` applies the approved text. This covers a text-only fix after `reopen` and a crash between push and edit.
