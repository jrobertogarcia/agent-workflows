# Orchestrate: Boot

Read this on every invocation and every touchpoint reply, after the Guard in `SKILL.md`. It extends the orchestrate `SKILL.md`, the core, whose terms, paths, Halt, and BLOCKED rules apply here.

## Boot

1. **Locate**: a stack, or a provisional folder (`S/stacks/.start.*`, absolute or relative to `S/stacks/`, resolved and validated as for `abandon <provisional path>`), that the message begins with (if a leading stack differs from the stack of the current branch's layer and that layer is not `RELEASED`, ask which is meant); else the `S/stacks/*/stack.json` whose `layers[].branch` is the current branch (unless, asked because the message reads as a new requirement, the human says it is a new run); else the stack the human names; else a provisional folder the human names; either provisional case resumes Start per `<start>`; else start a new run if the human gave a requirement, else ask for the requirement or a stack name. Write `git_common_dir` into a located stack that lacks it; if it holds another value, halt: "<name> belongs to the repository at <value>; if this one moved from there, set `git_common_dir` in its `stack.json` to <common>." A `narrow`, `register`, `reopen`, `close-out`, `address`, or `abandon` reply is never a requirement; with no stack located, ask for the stack name, except that `address` is handled per `<comments>` and `abandon <provisional path>` per below. Text after a named stack or provisional path is the reply to its touchpoint, never a requirement. Handle `abandon` (including `abandon <provisional path>`) and `address` right after Locate; `reopen` and `close-out` (per `<close-out>`) right after Reconcile, and `adopt` in place of the drift check 3(b) halt or in `BLOCKED`; otherwise report that there is nothing to adopt. **Restore**: in a fresh thread or after a context summary, read the located stack's `decisions.md` in full before acting; it is the run's record of decisions.
2. **Reconcile**, for the active layer (`active_layer_index`): if `state.json` is `RELEASED` and the layer is not, copy `pr` and `RELEASED` into the layer and move `active_layer_index` to the next `PENDING` layer, if any. If the layer is `PENDING` and `state.json` exists, set it `ACTIVE`. Read each `RELEASED` layer's state live with `gh pr view <pr> --json state`. `MERGED` keeps its `S/<branch>/` for close-out. `CLOSED` with a layer above it that is not `MERGED` or `CLOSED` follows Closed layer in `<stacked>`; otherwise its folder is kept too. In `LAYERS`, once every layer is `RELEASED` and reads `MERGED` or `CLOSED`, write `stack.json` `phase` = `CLOSE_OUT` and continue per `<close-out>`. Otherwise, with more than one layer, run Merged target in `<stacked>`.
3. **Drift checks**, for an `ACTIVE` layer, in order:
   0. **Clean tree (halt)**: `git status --porcelain --untracked-files=all` is empty and the git dir holds no `rebase-merge`, `rebase-apply`, `MERGE_HEAD`, or `CHERRY_PICK_HEAD`; a dirty tree is the human's to resolve: never commit, restore, or clean it yourself.
   1. **Branch (halt)**: `git branch --show-current` equals `git_anchor.branch`; report a detached `HEAD` as such.
   2. **Tip**: if `HEAD` equals `branch_tip_sha`, go to drift check 4.
   3. **Moved tip**:
      - (a) **Interrupted step**: the phase is `IMPLEMENTING` and `git merge-base --is-ancestor <branch_tip_sha> HEAD` succeeds, so a step committed before it was cut off. Write `branch_tip_sha` = `HEAD`.
      - (b) **Otherwise halt**, for the human to check and reply `adopt`: report the old and new tips and `git log --oneline --left-right --cherry-mark <branch_tip_sha>...HEAD` (`=` marks commits whose patch matches), or that the old tip's object is missing; never a diff body.
   4. **Base check**, against the local `<target>` with no fetch: unless Review-Round Rebase Skip per `<comments>` skips it, if `git merge-base --is-ancestor <target> <base_sha>` succeeds, the branch is in sync; go to drift check 5. Otherwise, if `<target>` is a layer, run Upstack rebase in `<stacked>`. Otherwise halt if `git rev-list origin/<trunk>..<trunk>` is not empty (unpushed trunk commits); if `git merge-base --is-ancestor <base_sha> <trunk>` succeeds, run `git rebase <trunk>`; otherwise upstream was rewritten, so run `git rebase --onto <trunk> <base_sha>`. On a conflict, abort the rebase (`gh stack rebase --abort` or `git rebase --abort`) and set `BLOCKED` naming the files and the rebase command that conflicted, for the human to run by hand (`gh stack rebase --upstack <branch> --no-trunk` for a layer, else `git rebase <trunk>` or `git rebase --onto <trunk> <base_sha>`), with "do not push this branch, then reply `adopt`". Only `adopt` exits: `retry`, `fix`, and `re-plan` re-run this check and conflict again. After a rebase, write `base_sha` = `git rev-parse <target>`, `branch_tip_sha` = `git rev-parse <branch>`, and, when `pass` is `short`, `pass` = `fix`, so an unfinished fix is still completed. Then from `AUDITING` or `WAITING_RELEASE_APPROVAL` enter `IMPLEMENTING` at `A2`; in `IMPLEMENTING`, go on to drift check 5. From another phase with `gate_1_plan_approved` true, dispatch `A2` alone and log a failure for the next touchpoint; with it false, do nothing more.
   5. **Resume**: in `IMPLEMENTING`, an earlier run was cut off mid-phase, so restart the pass where `pass` says, not counted: `A1`, `A1-fix`, `A1f` (per the Short Path in `<review-fix>`), or `A2`. The `A1` steps skip work already committed. Then continue Stage A after it.

**Adopt** (human reply after a drift check 3(b) halt or in `BLOCKED`; any other halt is cleared by fixing the cause and re-invoking): write `base_sha` = `git merge-base <target> HEAD`, or, when `<target>` is `<trunk>` and `git merge-base origin/<trunk> HEAD` descends from it, that instead, `branch_tip_sha` = `HEAD`, `approved_sha` = null, append to `roadblocks.md`; from `AUDITING`, `WAITING_RELEASE_APPROVAL`, or `BLOCKED` enter `IMPLEMENTING` at `A2`, unless `<comments>` runs Triage or Adopt. Adopting from `BLOCKED` is the human's exit: it also resets `count` to 0.

**`abandon <provisional path>`**: resolve a relative path against `S/stacks/`. The resolved path must be a direct child of `S/stacks/` whose name starts `.start.` and which holds no `stack.json`; otherwise halt. List its paths, then run:
```bash
rm -rf -- "<that path>"
```

## Resume Line

- End every stop that waits for a human reply with ``To continue in a new thread: in `<worktree>`, invoke orchestrate with `<your reply>` ``, leaving `<your reply>` as a placeholder. Before the layer has `state.json`, and in `CLOSE_OUT` or `WAITING_CLOSE_OUT_APPROVAL`, put the stack name before it; during Start, before `stack.json` exists, the provisional path.
- Print none for a halt or report cleared by acting and re-invoking, the Guard's and Locate's own questions, Start's trunk question, a read-only report, or an auto-answered gate. A new thread restores from the state files per Restore.

## Gate Buttons

- **Use**: when the session lists a structured question tool (by name or loaded on request), present each stop below with it, after the stop's content and resume line are printed in chat. The call carries only the question and the verbs, in this order, most common first; a verb the tool has no room for stays typed, and a stop with fewer verbs than the tool's minimum options stays typed. With no such tool, or with an auto-answered gate, present the typed verbs. Typed verbs always work, and the chat text lists every verb.
  - Unattended near miss: `yes`, `no`.
  - Split approval: `approve`, `narrow`.
  - Gate 1: `approve`, with the question text "approve, or reply in chat with feedback"; plan feedback never goes through the tool's free-text field, which truncates.
  - Gate 2: `approve`, `fix`, `redraft`.
  - BLOCKED: `fix`, `retry`, `re-plan`, `adopt`.
  - Stack `blocked`: `fix`, `retry`.
- **Payload turn**: after a button for `fix`, `redraft`, `narrow`, or `re-plan`, ask once in chat for its text and handle the two as the typed reply (`fix 3, 5`, `fix small: …`, `redraft <text>`; `re-plan` accepts "none"). The next message is a new choice instead only when it is exactly a verb of that stop, or `fix` with numbers or a `small:` or `large:` tag.
- Every other reply stays typed: story review answers, `register`, `reopen`, `address`, `abandon`, `close-out`, `approve C<n>`, and `narrow` and `adopt` at halts.

## Unattended

- **Flag**: `stack.json` `unattended` is `true` or absent (absent in older files and every attended run). Read it with the stack; before `stack.json` exists, a provisional run is unattended when its `decisions.md` has a `Start` entry whose `Ruling:` begins `unattended opt-in`. It is set only at Start, by the starting message or the `yes` to the near-miss question per `<start>`, and never by a later message; it stays set after a human reply at a stop.
- **Report line**: every report to the human (stop, halt, final report) leads with "Unattended run: branches are pushed and draft pull requests opened with no approval."
- **Auto-answer**: at each touchpoint below, instead of stopping, append the Decisions entry with `Reply: (auto: unattended)` and `Ruling:` the recommendation taken, then act as if the human had replied it; print one line naming the touchpoint and ruling. Touchpoints: Start (unanswered Needs you items proceed on their recommended options and the default stack name stands), Split approval (`approve`, after the checks in `<stacked>` pass), Gate 1 (`approve`, per `<resolve>`), Gate 2 (`approve`, per `<release>`).
- **Stops**: take no auto-answer, report as attended, and end with the Resume Line where the attended flow would, when any of: `BLOCKED` (after the retry budget, as the attended flow counts it) or Stack `blocked`; a halt (drift, rebase conflict, tip moved, closed layer, open-layer limit, failed Release or link); a `large` tier or `re-plan` recommendation; a Needs you item whose report names no recommended option; Gate 2 with an unresolved Critical or Important finding or an `Item` action `discuss` (per `<release>`); any other question this skill would put to the human (name taken, a failed split check, trunk unresolved).
- **Scope**: auto-answers apply to fresh runs. `address`, `reopen`, and `close-out` run attended even when the flag is set: every gate on those paths waits for the human.

## Decisions

On every touchpoint reply or auto-answer to a located stack, or to a provisional run during Start, after Locate and before acting on the reply, append one entry to the stack's `decisions.md` (`<provisional>/decisions.md` during Start):
```
## <UTC time> <touchpoint> <branch or ->
Reply: <the reply, verbatim>
Ruling: <what you apply>
Reason: <one line>
Cost if wrong: <one line>
```
- `<touchpoint>` is the phase being answered (`stack.json` `blocked` or `phase`, `state.json` `lifecycle.phase`), `Start` for the story touchpoint, or the reply word for `address`, `register`, `close-out`, and `abandon`.
- `Reply:` may run over several lines; it ends at the entry's `Ruling:` line.
- Append by a heredoc concatenation that prints nothing.
- The entry is the only record of split-approval `approve` and discussion, `redraft` feedback, and every follow-up ruling.
- `Reply: (auto: unattended)` marks an entry the run wrote itself per Unattended.
- A halt cleared by re-invoking is not a reply and writes none.
- A button choice and its payload turn are one reply: `Reply:` holds the combined typed form, A click alone is not a reply and writes no entry.
