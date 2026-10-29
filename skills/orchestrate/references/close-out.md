# Orchestrate: Close-out

Read this on `CLOSE_OUT`, `WAITING_CLOSE_OUT_APPROVAL`, and a `close-out` reply. It extends the orchestrate `SKILL.md`, the core, whose terms, paths, Halt, and BLOCKED rules apply here; each section names where the skill points to it.

## Trigger

- Entered from Reconcile in `<boot>`.
- A `close-out` reply is handled right after Reconcile:
  - in `CLOSE_OUT` or `WAITING_CLOSE_OUT_APPROVAL`, it continues that phase;
  - otherwise halt, listing each layer that is `PENDING` or `ACTIVE` and each pull request that reads `OPEN` (with its URL from `gh pr view <pr> --json url`), with "merge or close them, or reply `abandon`". There is no partial close-out.
- In both phases, BLOCKED writes `stack.json` `blocked` and appends to the stack's `roadblocks.md`, as before `state.json` exists; Stack `blocked` (`fix`, `retry`, `abandon`) then applies unchanged.

## Close-out steps

These rules apply to `inventory`, `tickets`, and `resolve` with purpose `close-out`:
- Omit the branch clause from the template.
- Reports go to `S/stacks/<name>/reports/`.
- In place of the After every step check in `<dispatch>`: `git branch --show-current` and `git rev-parse HEAD` equal their values before the dispatch, and the tree is clean.

## `CLOSE_OUT`

1. Dispatch `inventory`. Before any re-dispatch (on feedback, or in step 5), when `reports/inventory.md` exists, `mv -f` it to `reports/inventory-previous.md` and pass it.
2. A missing or non-numeric `Open items:` line is transient.
3. At 0 items, report "nothing to close out" and run Cleanup.
4. Otherwise dispatch `resolve` on the items as kind `question`. Inputs: the `inventory` report, `requirements.md`, `context.md` if any, and the stack's `resolve.md`. Add the instruction: "Each item is a proposed follow-up: verify its premise against the sources, and say whether the proposed action is the smallest that settles it, or what is. Keep the inventory's numbering, so Item <n> is C<n>. Second-to-last line: `Inventory changes: <n>`, the number of items whose premise fails or whose action should change."
5. If `Inventory changes:` is above 0, re-dispatch `inventory` once with `reports/inventory-previous.md` and `reports/resolve-close-out.md` as inputs, adding: "Adopt each change and rewrite your report. Keep every `C<n>` number from `inventory-previous.md`. An item whose premise fails becomes `leave` with the reason. Number any new item after the last." The once-per-entry count is held in this thread, as in PLANNING in `<resolve>`.
6. A `resolve` that returns `STOPPED` or hits a second transient follows Resolve Step in `<resolve>`: log it, and mark every item "premise unverified" at the gate.
7. Then write `WAITING_CLOSE_OUT_APPROVAL`.

**`inventory`** (defined here, as `replies` is in `<comments>`). Skill reference: "the instructions below". Agent: `orchestrate-step`. Tokens: `READY`.
- Inputs: `stack.json`; each layer's `S/<branch>/` path with its PR number; the stack's `requirements.md`, `context.md`, `resolve.md`, `decisions.md` (as context), `incidental.md`, and `roadblocks.md`; on a re-dispatch, also `inventory-previous.md` and/or `resolve-close-out.md`.
- Instructions:
  - "Run read-only. Read ticket state only through `gh issue view` / `gh pr view` or the ticket MCP's read tools.
  - Inventory the follow-ups this change created, from:
    - each layer's handover `Follow-ups` (for a handover without one, its deviation and "not yet verified" lines) and `Scope Reductions`;
    - each `roadblocks.md`'s `Scope Reductions:`, `PUSHED`, fix, and pending lines;
    - `review.md` `Item <n>: defer` lines;
    - deferred and Settled RECOMMEND items in both `resolve.md` files;
    - `incidental.md` entries not marked `[drop]`: `[file]` proposes `ticket-new`, the others `leave`;
    - docs in the checkout that name a file or symbol a PR touched (`gh pr view <pr> --json files`, then `rg`);
    - the state of each linked ticket.
  - Mark a `CLOSED` layer's items "not shipped". Add one `branch` item per `MERGED` layer whose local branch exists, and none for a `CLOSED` layer.
  - Give each item the smallest action, of one kind:
    - `repo-edit`;
    - `ticket-edit`, only on a ticket the human reports or is assigned: compare `gh api user --jq .login` with `gh issue view <url> --json author,assignees` (or the Jira MCP's user-info and issue read tools); otherwise a `draft` comment;
    - `ticket-new`, in the linked ticket's project, or in the PRs' repository when no ticket is linked;
    - `draft`, a comment or chat message, with its destination;
    - `branch`;
    - `leave`, no action; who owns leftovers is the human's call.
  - Match ticket text to the team's format: read the 2–3 most recent tickets in the linked ticket's project or repository (repo line, spec link, done-when, points), with `gh issue list --repo <r> --state all --limit 3` for GitHub, or the matching JQL through the MCP for Jira. With no reachable system, the item becomes a `draft`.
  - Report shape:
    - `## Links`: every link from the layers' handover `Links` plus each layer's PR URL, then `Missing links: <kinds of ticket, PRs, spec, epic, or none>`.
    - One `## C<n>` section per item: line 1 `C<n>: <kind> — <source> — <action>`; then `Destination: <ticket URL, project or repository, channel, or file>`; `Read: <ticket updatedAt, or ->`; `Links:` and `Missing links:` lines; and a `Text:` block holding the exact ticket, draft, or repo-edit text.
    - Second-to-last line: `Open items: <n>`."

## `WAITING_CLOSE_OUT_APPROVAL`

- Present the `## Links` block and every `C<n>` section: kind, source, action, premise verdict, destination, missing links, and text. The premise verdict for `C<n>` is Item `<n>` in `reports/resolve-close-out.md`; an item with no such Item (numbered after a re-inventory, or after a `resolve` failure) shows "premise unverified".
- Replies:
  - `approve` runs every item except `ticket-edit`, `ticket-new`, and `branch`; the gate says so.
  - `approve C<n>[, C<m>]` runs exactly the named items. First check each with `grep -m1 -E '^C<n>: (repo-edit|ticket-edit|ticket-new|draft|branch|leave) — '` on the report; if any matches nothing, stop and name it, and the Decisions entry records `Ruling: rejected, no such C<n>`.
  - Any other text, except `abandon` and `file|defer|drop`, is feedback: append it to `requirements.md` under `## Close-out feedback <UTC time>`, write `CLOSE_OUT`, and re-run.
- The Decisions entry, touchpoint `WAITING_CLOSE_OUT_APPROVAL`, records the approved list in `Ruling:`.
- The stop ends with the Resume Line, with the stack name.

## Execute

For the approved items, in order:
1. `tickets`, when any ticket item is approved.
2. Brief, when any `repo-edit` item is approved.
3. Branch deletion, for each approved `branch` item.
4. A final report that prints every approved `draft` verbatim with its destination and links, and likewise the `Text:`, destination and links of each approved ticket item that `tickets` returned as `draft`, or as `skipped` for any reason but the write already being present; the ticket results, the brief invocation, the branches deleted or skipped with reasons, and "who owns the leftovers is yours".
5. Cleanup.

**`tickets`**. Skill reference: "the instructions below". Agent: `orchestrate-step`. Tokens: `DONE`.
- Inputs: the `inventory` report, the approved C numbers, and `tickets-previous.md` if any. Before a re-dispatch, when `reports/tickets.md` exists, `mv -f` it to `reports/tickets-previous.md`; a missing report leaves any earlier `tickets-previous.md` in place.
- Instructions:
  - "Write only the named items, in order, and run no other gh or MCP write.
  - Skip an item that `tickets-previous.md` records as written, and report it again as `C<n>: written <URL>`.
  - Re-read each ticket before writing. For an edit, compare its updated time with `Read:`; for a new ticket, search for one with the same title created since the inventory. If it changed, or the write is already present, skip it and say why.
  - Write `Text:` verbatim: `gh issue edit <url> --body-file <tmp>` / `gh issue create --repo <r> --title <t> --body-file <tmp>`, or the matching Atlassian MCP tool. Read it back and report the URL and whether it matches.
  - With no reachable system, report the item as a draft.
  - Closing lines: one `C<n>: <written|skipped|draft> <URL or ->` per item."

**Brief**:
- Skip it when a `S/stacks/.start.*/requirements.md` already begins with `# Close-out follow-ups: <name>` (`grep -l`), and report that path.
- Otherwise `mktemp -d S/stacks/.start.XXXXXX` and write `<provisional>/requirements.md` atomically from: the line `# Close-out follow-ups: <name>`; one line naming the merged PR URLs; the inventory's `## Links` block; and each approved `repo-edit` `## C<n>` section, extracted from the report with `awk`, printing nothing.
- Report "To start it: in `<worktree>`, invoke orchestrate with `<provisional path>`", for a fresh thread. Do not start it here.

**Branch deletion**, for each approved `branch` item `<b>` with PR `<pr>`. Skip and report the item when any of these holds:
- `git show-ref --verify --quiet refs/heads/<b>` fails;
- `gh pr view <pr> --json state,headRefOid` does not read `MERGED`;
- its `headRefOid` differs from `git rev-parse <b>`;
- `git worktree list --porcelain` shows `<b>` checked out in a worktree other than `<worktree>`.

When `<b>` is the current branch, run `git fetch origin <trunk>`, then `git switch --detach origin/<trunk>`. Then run `git branch -D <b>`; a squash merge makes `git branch -d` refuse, so the `headRefOid` check guards `-D`. Never touch remote branches, worktrees, PRs, or gh-stack metadata.

**Cleanup**: delete each layer's `S/<branch>/`, then `S/stacks/<name>/`, and report the stack done. The brief's `.start.*` folder survives, and the final report already holds the drafts.
