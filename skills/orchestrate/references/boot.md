# Orchestrate: Boot

Read this on every invocation and every touchpoint reply, after the Guard in `SKILL.md`. It extends the orchestrate `SKILL.md`, the core, whose terms, paths, Halt, and BLOCKED rules apply here.

## Boot

1. **Locate**: a stack, or a provisional folder (`S/stacks/.start.*`, absolute or relative to `S/stacks/`, resolved and validated as for `abandon <provisional path>`), that the message begins with (if a leading stack differs from the stack of the current branch's layer and that layer is not `RELEASED`, ask which is meant); else the `S/stacks/*/stack.json` whose `layers[].branch` is the current branch (unless, asked because the message reads as a new requirement, the human says it is a new run); else the stack the human names; else a provisional folder the human names; either provisional case resumes Start per `<start>`; else start a new run if the human gave a requirement, else ask for the requirement or a stack name. Write `git_common_dir` into a located stack that lacks it; if it holds another value, halt: "<name> belongs to the repository at <value>; if this one moved from there, set `git_common_dir` in its `stack.json` to <common>." A `narrow`, `register`, `reopen`, `close-out`, `address`, `abandon`, `file`, `defer`, or `drop` reply is never a requirement; with no stack located, ask for the stack name, except that `address` is handled per `<comments>` and `abandon <provisional path>` per below. Text after a named stack or provisional path is the reply to its touchpoint, never a requirement. Handle `abandon` (including `abandon <provisional path>`), `address`, and `file|defer|drop N<n>` right after Locate, so a `file|defer|drop` reply is never read as Gate 2 feedback or as a release trigger when `gate_2_release_approved` is true; `reopen` and `close-out` (per `<close-out>`) right after Reconcile, and `adopt` in place of the drift check 3(c) halt or in `BLOCKED`; otherwise report that there is nothing to adopt. **Restore**: in a fresh thread or after a context summary, read the located stack's `decisions.md` and `incidental.md` in full before acting; they are the run's record of decisions and findings.
2. **Reconcile**, for the active layer (`active_layer_index`): if `state.json` is `RELEASED` and the layer is not, copy `pr` and `RELEASED` into the layer and move `active_layer_index` to the next `PENDING` layer, if any. If the layer is `PENDING` and `state.json` exists, set it `ACTIVE`. Read each `RELEASED` layer's state live with `gh pr view <pr> --json state`. `MERGED` keeps its `S/<branch>/` for close-out. `CLOSED` with a layer above it that is not `MERGED` or `CLOSED` follows Closed layer in `<stacked>`; otherwise its folder is kept too. In `LAYERS`, once every layer is `RELEASED` and reads `MERGED` or `CLOSED`, write `stack.json` `phase` = `CLOSE_OUT` and continue per `<close-out>`. Otherwise, with more than one layer, run Merged target in `<stacked>`.
3. **Drift checks**, for an `ACTIVE` layer, in order:
   0. **Clean tree (halt)**: `git status --porcelain --untracked-files=all` is empty and the git dir holds no `rebase-merge`, `rebase-apply`, `MERGE_HEAD`, or `CHERRY_PICK_HEAD`; a dirty tree is the human's to resolve: never commit, restore, or clean it yourself.
   1. **Branch (halt)**: `git branch --show-current` equals `git_anchor.branch`; report a detached `HEAD` as such.
   2. **Tip**: if `HEAD` equals `branch_tip_sha`, go to drift check 4.
   3. **Moved tip**:
      - (a) **Crash**: a ✎ `pending_step` is set and `git merge-base --is-ancestor <from_tip_sha> HEAD` succeeds. Write `branch_tip_sha` = `HEAD`, keeping `pending_step`.
      - (b) **Maintenance**: the phase is `WAITING_PLAN_APPROVAL`, `WAITING_RELEASE_APPROVAL`, or `BLOCKED`; the `base_sha` and `branch_tip_sha` objects exist; with `P` = `git rev-parse <target>`, or, when `<target>` is `<trunk>` and `git rev-list origin/<trunk>..<trunk>` is not empty or the ancestor, merges, and patch-id checks below fail for it, `git rev-parse origin/<trunk>`, `git merge-base --is-ancestor P HEAD` succeeds; `git rev-list --merges P..HEAD` is empty; and the ordered `git patch-id --stable` list of `base_sha..branch_tip_sha` equals that of `P..HEAD`. Write `base_sha` = `P`, `branch_tip_sha` = `HEAD`, `approved_sha` = null, append to `roadblocks.md`, and from `WAITING_RELEASE_APPROVAL` enter `IMPLEMENTING`. Not counted.
      - (c) **Otherwise halt**: report the old and new tips and `git log --oneline --left-right --cherry-mark <branch_tip_sha>...HEAD` (`=` marks commits whose patch matches), or that the old tip's object is missing; never a diff body.
   4. **Base check**, against the local `<target>` with no fetch: unless Review-Round Rebase Skip per `<comments>` skips it, if `git merge-base --is-ancestor <target> <base_sha>` succeeds, the branch is in sync; go to drift check 5. Otherwise, if `pending_step` is `A5`, first run its Resume reset, `git reset --hard <precut_sha>`, and write `branch_tip_sha` = `HEAD`. Then, if `<target>` is a layer, run Upstack rebase in `<stacked>`. Otherwise halt if `git rev-list origin/<trunk>..<trunk>` is not empty (unpushed trunk commits); if `git merge-base --is-ancestor <base_sha> <trunk>` succeeds, run `git rebase <trunk>`; otherwise upstream was rewritten, so run `git rebase --onto <trunk> <base_sha>`. On a conflict, abort the rebase (`gh stack rebase --abort` or `git rebase --abort`) and set `BLOCKED` naming the files and the rebase command that conflicted, for the human to run by hand (`gh stack rebase --upstack <branch> --no-trunk` for a layer, else `git rebase <trunk>` or `git rebase --onto <trunk> <base_sha>`), with "do not push this branch, then reply `adopt`". Only `adopt` exits: `retry`, `fix`, and `re-plan` re-run this check and conflict again. After a rebase, write `base_sha` = `git rev-parse <target>`, `branch_tip_sha` = `git rev-parse <branch>`, `precut_sha` = null, and `pending_step` = null unless its step is `A1`, `A1-fix`, or `A1f` (kept as `A1-fix`), which keeps it with `from_tip_sha` = the new `branch_tip_sha`. Then from `IMPLEMENTING`, `AUDITING`, or `WAITING_RELEASE_APPROVAL` enter `IMPLEMENTING` at `A2`, unless drift check 5 resumes a step. From another phase with `gate_1_plan_approved` true, dispatch `A2` alone and log a failure for the next touchpoint; with it false, do nothing more.
   5. **Resume**: in `IMPLEMENTING` with `pending_step` set, re-run that step, not counted, and continue Stage A after it (after `A6v-cut`, go to `A7`; after `A1f` or `A2f`, continue the short path per `<review-fix>`). For `A5`, instead `git reset --hard <precut_sha>`, write `branch_tip_sha` = `HEAD` and `pending_step` = null, and continue Stage A at `A4`.

**Adopt** (human reply after a drift check 3(c) halt or in `BLOCKED`; any other halt is cleared by fixing the cause and re-invoking): write `base_sha` = `git merge-base <target> HEAD`, or, when `<target>` is `<trunk>` and `git merge-base origin/<trunk> HEAD` descends from it, that instead, `branch_tip_sha` = `HEAD`, `approved_sha`, `precut_sha`, and `pending_step` = null, append to `roadblocks.md`; from `AUDITING`, `WAITING_RELEASE_APPROVAL`, or `BLOCKED` enter `IMPLEMENTING` at `A2`, unless `<comments>` runs Triage or Adopt. Adopting from `BLOCKED` is the human's exit: it also resets `count` to 0 and `gaps_fix_used` to false.

**`abandon <provisional path>`**: resolve a relative path against `S/stacks/`. The resolved path must be a direct child of `S/stacks/` whose name starts `.start.` and which holds no `stack.json`; otherwise halt. List its paths and its `incidental.md` entries, then run:
```bash
rm -rf -- "<that path>"
```

## Resume Line

- End every stop that waits for a human reply with this line, values filled in: ``To continue in a new thread: in `<worktree>`, invoke orchestrate with `<your reply>` ``. `<your reply>` stays a placeholder; the stop already lists the replies.
- Before the layer has `state.json`, and while `stack.json` `phase` is `CLOSE_OUT` or `WAITING_CLOSE_OUT_APPROVAL`, precede `<your reply>` with the stack name; during Start, before `stack.json` exists, with the provisional path. On a layer with `state.json`, Locate finds the run by the current branch.
- None for a halt or a report cleared by acting and re-invoking (`PUSHED`, a failed Release step), the Guard's and Locate's own questions (they settle which run the message belongs to, and a new thread's message is asked afresh), Start's trunk question (no `stack.json` yet, folder already moved), or a read-only report (`RELEASED`, no review comments). An auto-answered gate is not a stop and prints none.
- The new thread restores from the state files per Restore; nothing extra is written.

## Gate Buttons

- **Use**: when a structured question tool is listed among the session's tools, including one listed only by name that the host loads on request, present each stop below with it, after the gate's content and its resume line have been printed in chat, never inside the call. No tool name is hard-coded. The call carries only the question and the verb options; no summary, findings, diff stat, or PR text goes in it. With no such tool, present the typed verbs as usual. A button choice is an ordinary reply, so switching hosts mid-run is fine. With `unattended` set, an auto-answered gate shows no buttons; see Unattended.
- **Verbs per stop** (each option is the existing verb, label and meaning unchanged):
  - Split approval: `approve`, `narrow`.
  - Gate 1: `approve`, with the question text "approve, or reply in chat with feedback". Plan feedback is never collected through the tool's free-text field, which truncates at about 300 characters.
  - Gate 2: `approve`, `fix`, `redraft`.
  - Untagged tier proposal: `small`, `large`.
  - BLOCKED: `fix`, `retry`, `re-plan`, `adopt`.
  - Stack `blocked`: `fix`, `retry`.
- **Payload turn**: after a button for a verb that takes text or numbers (`fix`, `redraft`, `narrow`, `re-plan`), ask once in plain chat for the payload and read the next message as it. Combine them into the equivalent typed reply and handle it exactly as if typed: `fix <payload as typed>` (numbers such as `fix 3, 5`, `small:` or `large:` text, or untagged text), `redraft <text>`, `narrow <text>`, `re-plan <text>`. A `re-plan` with no feedback is allowed: accept "none". The next message replaces the button choice only when it is exactly one verb word of that stop, or a verb followed by the number list or tag form Inputs accepts (`fix 3, 5`, `small:`); anything else, including text that merely starts with a verb word, is the payload.
- **Option limits**: if the tool states an upper limit below the stop's verb count, show the verbs in the order listed above (most common first) and leave the rest typed. If the tool needs more options than the stop has verbs, that stop stays typed. Typed verbs always work, and the stop's plain-chat text still lists every verb.
- **Not covered**: story review answers and the stack name, `register`, `reopen`, `address`, `abandon` (everywhere, including `abandon <path>`, which deletes state and stays typed), `narrow` and `adopt` at the stacked-work and tip-moved halts, `close-out`, `approve C<n>`, close-out `approve`, and `file|defer|drop N<n>` stay typed.

## Unattended

- **Flag**: `stack.json` `unattended` is `true` or absent (absent in older files and every attended run). Read it with the stack; before `stack.json` exists, a provisional run is unattended when its `requirements.md`, above the first `## Answers` heading, has the opt-in per `<start>`. It is set only at Start and never by a later message; it stays set after a human reply at a stop.
- **Report line**: every report to the human (stop, halt, final report) leads with "Unattended run: branches are pushed and draft pull requests opened with no approval."
- **Auto-answer**: at each touchpoint below, instead of stopping, append the Decisions entry with `Reply: (auto: unattended)` and `Ruling:` the recommendation taken, then act as if the human had replied it; print one line naming the touchpoint and ruling. Touchpoints: Start (unanswered Needs you items proceed on their recommended options and the default stack name stands), Split approval (`approve`, after the checks in `<stacked>` pass), Gate 1 (`approve`, per `<resolve>`), Gate 2 (`approve`, per `<release>`).
- **Stops**: take no auto-answer, report as attended, and end with the Resume Line where the attended flow would, when any of: `BLOCKED` (after the retry budget, as the attended flow counts it) or Stack `blocked`; a halt (drift, rebase conflict, tip moved, closed layer, open-layer limit, failed Release or link); a `large` tier or `re-plan` recommendation (including a Gate 1 whose `plan-feedback.md` holds `Tier escalated from small:`); a Needs you item whose report names no recommended option; Gate 2 with an unresolved Critical or Important finding or an `Item` action `discuss` (per `<release>`); any other question this skill would put to the human (name taken, a failed split check, trunk unresolved).
- **Scope**: auto-answers apply to fresh runs. `address`, `reopen`, and `close-out` run attended even when the flag is set: every gate on those paths waits for the human.
- **Known gap**: no new spend, turn, or time cap; the run is bounded by the retry `count`, review rounds that stop on new blocking findings, and BLOCKED.

## Decisions

On every touchpoint reply or auto-answer to a located stack, or to a provisional run during Start, after Locate and before acting on the reply, append one entry to the stack's `decisions.md` (`<provisional>/decisions.md` during Start):
```
## <UTC time> <touchpoint> <branch or ->
Reply: <the reply, verbatim>
Ruling: <what you apply>
Reason: <one line>
Cost if wrong: <one line>
```
- `<touchpoint>` is the phase being answered (`stack.json` `blocked` or `phase`, `state.json` `lifecycle.phase`), `Start` for the story touchpoint, or the reply word for `address`, `register`, `close-out`, `abandon`, `file`, `defer`, and `drop`.
- `Reply:` may run over several lines; it ends at the entry's `Ruling:` line.
- Append by a heredoc concatenation that prints nothing.
- The entry is the only record of split-approval `approve` and discussion, the untagged tier proposal (`Ruling: proposed tier <small|large>, awaiting reply`), `redraft` feedback, `file|defer|drop`, and every follow-up ruling.
- `Reply: (auto: unattended)` marks an entry the run wrote itself per Unattended.
- A halt cleared by re-invoking is not a reply and writes none.
- A button choice and its payload turn are one reply: `Reply:` holds the combined typed form, so lookups (for example `grep` of the latest proposal entry in `<feedback>`) are unchanged. A click alone is not a reply and writes no entry.

## History

- Before replacing or deleting `S/<branch>/fix-input.md` or `S/<branch>/plan-feedback.md`, if it exists, append `## <UTC time> <file>: <replaced|deleted> (<cause>)` and then the file's contents to `S/<branch>/history.md`, by concatenation that prints nothing; the success check is empty output.
- `<cause>` is the triggering step or reply: `fix pass`, `Gate 1 approve`, `re-plan`, `PLANNING`, or `inner pass <step id>`.
- The live files keep their meaning. Appends to `plan-feedback.md` lose nothing and are not history events.

## Incidental

- `N<n>` is line `n` of the stack's `incidental.md` (`<provisional>/incidental.md` during Start), written per Out of scope in `<dispatch>`. Every line is an entry: the file has no heading and no blank lines, and lines are never removed, so the numbers stay stable.
- **`file|defer|drop N<n>[, N<m>]`**:
  - Check each number exists (`sed -n '<n>p'` is non-empty); otherwise stop, naming the numbers that matched nothing, and leave `incidental.md` unchanged; this read-only check runs before the Decisions entry, which records `Ruling: rejected, no such N<n>`.
  - Otherwise replace the file atomically (`awk` to a temp file, then `mv -f`): on each named line, strip any trailing ` [file]`, ` [defer]`, or ` [drop]` mark and append ` [<word>]`.
  - Change no phase, and re-present the pending touchpoint's question in one line.
  - `file` marks an entry for the human to file; you file no issue, since that is a GitHub write.
