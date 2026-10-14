---
name: orchestrate
description: Drive one requirement from story review to an open pull request on a single branch, dispatching each lifecycle step to a fresh subagent and stopping for plan and release approval. Use to run the whole lifecycle end to end.
---

# Orchestrate

You coordinate; workers do the work. You dispatch every step, own the state files, and stop for the human at the touchpoints. You never edit code and never run a step's skill in this thread.

## Inputs

- A requirement (text, file, or link) to start; nothing to resume the run on the current branch; or a stack name to resume a run that has no branch yet.
- Human replies: answers and a stack name (story review), `approve` or feedback (gates), `fix` with direction, `re-plan`, or `adopt` (blocked or halted), `abandon` (before a branch exists).

## Paths

- `<repo>` = `basename(dirname(git rev-parse --path-format=absolute --git-common-dir))`, `<worktree>` = `git rev-parse --show-toplevel`, `S` = `~/.agent-workflows/<repo>`.
- `<root>`: resolve the real path of this file (follow symlinks) and go up three levels, past `skills/orchestrate/SKILL.md`: the repository root, or for an installed copy the directory above the installed skills. Reference a skill as `<root>/skills/<name>/SKILL.md` when that file exists; otherwise, or when this file's path is unknown, as "the installed `<name>` skill".

## State Files

```
S/stacks/<name>/stack.json      S/<branch>/state.json
S/stacks/<name>/requirements.md S/<branch>/plan.md
S/stacks/<name>/roadblocks.md   S/<branch>/handover.md
                                S/<branch>/roadblocks.md
```

- `<name>` matches `^[a-z0-9][a-z0-9-]{0,39}$`. Each `/` in `<branch>` is a nested directory; a branch named `stacks` or starting `stacks/` halts.
- You alone write `stack.json`, `requirements.md`, `plan.md`, and `state.json`. Workers write only `handover.md`. Each `roadblocks.md` is append-only, one line per entry: `- <UTC time> <skill> <tip SHA>: <root cause>`; a `fix` entry is followed by its input verbatim in a fenced block. Before `state.json` exists, entries go to the stack's `roadblocks.md`.
- SHAs are full 40-character values. Set `updated_at` (UTC, ISO 8601) on every write. Replace a file atomically:
  ```bash
  tmp="$(mktemp "$dir/state.json.XXXXXX")" && cat > "$tmp" <<'EOF'
  { ... }
  EOF
  mv -f "$tmp" "$dir/state.json"
  ```
- `requirements.md`: the requirement verbatim, then each round of the human's answers verbatim.
- `stack.json`; `phase` is `ANALYSIS`, `STACK_DECOMPOSITION`, or `LAYERS`; `blocked` is `null` or the blocked step's id; `layers` holds at most one entry, `status` `PENDING`, `ACTIVE`, or `RELEASED`:
  ```json
  { "schema_version": 1, "stack_name": "<name>", "trunk": "<trunk>", "phase": "ANALYSIS", "blocked": null,
    "active_layer_index": null, "layers": [], "updated_at": "<time>" }
  ```
  Layer entry: `{ "index": 0, "branch": "<branch>", "pr": null, "status": "PENDING" }`.
- `state.json`, fixed shape:
  ```json
  {
    "schema_version": 1,
    "git_anchor": { "repo": "<repo>", "branch": "<branch>", "target_branch": "<trunk>",
                    "base_sha": "<sha>", "branch_tip_sha": "<sha>", "pending_step": null },
    "lifecycle": { "phase": "PLANNING", "active_skill": "plan-implementation", "blocked_from": null },
    "gates": { "gate_1_plan_approved": false, "gate_2_release_approved": false },
    "retries": { "count": 0, "max_allowed": 2, "gaps_fix_used": false },
    "artifacts": { "plan_file": "plan.md", "handover_file": "handover.md", "roadblocks_file": "roadblocks.md",
                   "last_verdict": null, "approved_sha": null, "precut_sha": null },
    "updated_at": "<time>"
  }
  ```
  - `base_sha`: the trunk tip the branch was last based on. `branch_tip_sha`: the last `HEAD` you verified.
  - `pending_step`: `null` or `{ "step_id", "skill", "from_tip_sha" }`; `step_id` `A1-fix` is `A1` on a fix pass.
  - `active_skill`: the skill last dispatched; `pending_step.skill`: the pending step's. Both are `implement` for `A1` and `simplify-diff` for `A5`.
  - `blocked_from`: the phase `BLOCKED` was entered from, kept on a re-entry from `BLOCKED`; null outside `BLOCKED`.
  - `last_verdict`: the last `check-alignment` or `review-branch` verdict. `approved_sha`: `HEAD` at `APPROVE`. `precut_sha`: the tip before the first `A5` dispatch of this Stage A; null otherwise.
  - Every entry to `PLANNING` sets `gate_1_plan_approved` and `gaps_fix_used` false and `pending_step` null. Every entry to `IMPLEMENTING` requires `gate_1_plan_approved` true, else halt, and sets `approved_sha` and `precut_sha` null and `gate_2_release_approved` false.

Until the layer has `state.json`, `stack.json` drives the next action: `blocked` if set, else `phase`; after, `state.json` `lifecycle.phase` does.

## Dispatch

Send each step as one prompt, built from the template, to the `orchestrate-step` agent as a fresh subagent with no conversation history, never a fork of this context (`review-branch` too).

- **Pending step**: before a step marked ✎ (for `A1-fix`, in the fix-pass write; see Retries), write `pending_step` = `{ step_id, skill, from_tip_sha: branch_tip_sha }`. After it returns, read `git rev-parse HEAD` yourself (a reported SHA is only a cross-check) and write `branch_tip_sha` = `HEAD` and `pending_step` = null in one write.
- **After every step** except `branch`: `git branch --show-current` is unchanged, `git status --porcelain` is empty, after an unmarked step `HEAD` equals `branch_tip_sha`, and after a ✎ step `from_tip_sha` is an ancestor of `HEAD`. Otherwise halt with the report.
- **Result**: read the report's last line, `Result: <token>`. A missing line, crash, timeout, network or rate-limit error is transient: re-run the step once unchanged, not counted; a second transient on the same step sets `BLOCKED`. `STOPPED` is valid from every step and sets `BLOCKED` with the report; it is never transient.
- **Fallback**: if you cannot dispatch a fresh `orchestrate-step` subagent (no subagent support, or no agent by that name), write `pending_step` for a Stage A step, print the prompt in one fenced block, ask the human to run it in a fresh thread and paste its report back (with the stack name before the branch exists), and stop. Boot consumes the pasted report.

Template (fill every `<...>`; omit the branch clause before the branch exists). `<skill reference>` is the step's skill referenced per Paths; for `A1` it is "the approved plan at <plan.md path>, committing per <`create-commit` reference>", and for `A5` "the `A4` simplify-diff report below, committing per <`create-commit` reference>".

```
Work only in <worktree>, on branch <branch>; stop and report if `git branch --show-current` differs.
Step <step_id>: follow <skill reference>. Where it differs from these instructions, follow these. Resolve include directives in that skill relative to the repository root that holds its skills/ directory.
Inputs:
<each absolute path to read, and each report passed verbatim, labeled>
Instructions:
<the step's instructions from the table>
Ask no questions; if an assumption here does not hold, stop and report what you found, ending `Result: STOPPED`. Do not write stack.json, state.json, plan.md, or requirements.md under ~/.agent-workflows/. Leave `git status --porcelain` empty: commit what is in scope and discard the rest.
Report what you did, the files you changed, the checks you ran and their results, and `git rev-parse HEAD` if you committed. The last line is `Result: <one of TOKENS>`, or `Result: STOPPED` if you stopped.
```

| Step | Skill | ✎ | Inputs | Instructions | Tokens |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `story` | `review-story` | | requirement | Number your clarifying questions. | `READY` |
| `context` | `gather-context` | | `requirements.md` | Target what the requirement names; if ambiguous, choose and list what you skipped. | `READY` |
| `decompose` | `phase-breakdown` | | `requirements.md`, context report if any | Split into layers, each one independently reviewable pull request; one layer when the change fits one. Give each a Conventional Commits branch name on its own line, `Branch: <name>`. Second-to-last line: `Layers: <n>`. | `READY` |
| `branch` | `create-branch` | | branch name, trunk, `F` | Skip the skill's checkout and pull; never check out `<trunk>`. If no worktree in `git worktree list --porcelain` has `<trunk>` checked out, run `git fetch . origin/<trunk>:<trunk>`. Then run `git switch -c <branch> <F>`. | `DONE` |
| `plan` | `plan-implementation` | | `requirements.md`, context report if any; on re-plan the previous `plan.md` and the human's feedback verbatim | Run read-only and write no files; return the complete plan text. | `READY` |
| `A1` | the plan, committed per `create-commit` | ✎ | `plan.md`; on a fix pass, the failing report verbatim | Execute the plan end to end within its scope, skipping work already committed; on a fix pass, fix only what the report names. Run the plan's verification. | `DONE` |
| `A2`, `A6v` | `validate-commit` | ✎ | | Commit any fixes per `create-commit`. `FAIL-UNRELATED` when only unrelated or pre-existing failures remain. | `PASS`, `FAIL-IN-SCOPE`, `FAIL-UNRELATED` |
| `A3`, `A6a` | `check-alignment` | | `plan.md` | Scope: `git diff <trunk>...HEAD`. `CONFLICT` when any plan-versus-standard conflict exists. | `ALIGNED`, `GAPS`, `CONFLICT` |
| `A4` | `simplify-diff` | | `plan.md` | Scope: `git diff <trunk>...HEAD`. `NONE` when there are no Safe Cuts or Simplifications. | `CUTS`, `NONE` |
| `A5` | `simplify-diff` report | ✎ | `A4` report verbatim, `plan.md` | Apply only its Safe Cuts and Simplifications, only within the plan's scope; apply no Scope Reductions. Commit them separately. | `DONE` |
| `A7` | `prepare-handover` | | `plan.md`, Scope Reductions verbatim or "none" | Add the Scope Reductions under a `Scope Reductions` heading. | `DONE` |
| `B` | `review-branch` | | | Target branch: `<trunk>`. | `APPROVE`, `REQUEST CHANGES` |
| `release` | `create-pr` | | | Base: `<trunk>`. Keep-checkout: yes. | `DONE` |

## Boot

Run on every invocation, before any other write:

1. **Locate**: the `S/stacks/*/stack.json` whose `layers[].branch` is the current branch, else the stack the human names, else start a new run.
2. **Reconcile**: if `state.json` is `RELEASED` and the layer is not, copy `pr` and `RELEASED` into the layer. If the layer is `PENDING` and `state.json` exists, set it `ACTIVE`.
3. **Pasted report**: if the human's message holds a report whose last line is `Result: <token>` valid for the current step (`pending_step` if set, else the step the phase dispatches next), process it as that step's return now: the After every step checks, the Pending step write, and the token's state change. Continue to the next step only after the drift checks, and only if they enter no other step. With no stack located, it is the `story` return if this thread holds the requirement; otherwise ask for the stack name or the requirement. A pasted report is never a requirement.
4. **Drift checks**, for an `ACTIVE` layer, in order:
   0. **Clean tree (halt)**: `git status --porcelain` is empty and the git dir holds no `rebase-merge`, `rebase-apply`, `MERGE_HEAD`, or `CHERRY_PICK_HEAD`.
   1. **Branch (halt)**: `git branch --show-current` equals `git_anchor.branch`; report a detached `HEAD` as such.
   2. **Tip**: if `HEAD` equals `branch_tip_sha`, go to drift check 4.
   3. **Moved tip**:
      - (a) **Crash**: a ✎ `pending_step` is set and `git merge-base --is-ancestor <from_tip_sha> HEAD` succeeds. Write `branch_tip_sha` = `HEAD`, keeping `pending_step`.
      - (b) **Maintenance**: the phase is `WAITING_PLAN_APPROVAL`, `WAITING_RELEASE_APPROVAL`, or `BLOCKED`; the `base_sha` and `branch_tip_sha` objects exist; with `P` = `git rev-parse <trunk>`, `git merge-base --is-ancestor P HEAD` succeeds; `git rev-list --merges P..HEAD` is empty; and the ordered `git patch-id --stable` list of `base_sha..branch_tip_sha` equals that of `P..HEAD`. Write `base_sha` = `P`, `branch_tip_sha` = `HEAD`, `approved_sha` = null, append to `roadblocks.md`, and from `WAITING_RELEASE_APPROVAL` enter `IMPLEMENTING`. Not counted.
      - (c) **Otherwise halt**: report the old and new tips and the first differing patch.
   4. **Base check**, against the local `<trunk>` with no fetch: if `git merge-base --is-ancestor <trunk> <base_sha>` succeeds, the branch is in sync; go to drift check 5. Otherwise, if `git merge-base --is-ancestor <base_sha> <trunk>` succeeds, run `git rebase <trunk>`; otherwise upstream was rewritten, so run `git rebase --onto <trunk> <base_sha>`. On a conflict, `git rebase --abort` and set `BLOCKED` naming the files. After a rebase, write `base_sha` = `git rev-parse <trunk>`, `branch_tip_sha` = `git rev-parse <branch>`, `precut_sha` = null, and `pending_step` = null unless its step is `A1` or `A1-fix`. Then from `IMPLEMENTING` or `WAITING_RELEASE_APPROVAL` enter `IMPLEMENTING` at `A2`, unless drift check 5 resumes a step. From another phase with `gate_1_plan_approved` true, dispatch `A2` alone and log a failure for the next touchpoint; with it false, do nothing more.
   5. **Resume**: in `IMPLEMENTING` with `pending_step` set, re-run that step, not counted, and continue Stage A after it. For `A5`, instead `git reset --hard <precut_sha>`, write `branch_tip_sha` = `HEAD` and `pending_step` = null, and continue Stage A at `A4`.

**Adopt** (human reply after a halt or in `BLOCKED`): write `base_sha` = `git merge-base <trunk> HEAD`, `branch_tip_sha` = `HEAD`, `approved_sha` and `pending_step` = null, append to `roadblocks.md`; from `WAITING_RELEASE_APPROVAL` or `BLOCKED` enter `IMPLEMENTING` at `A2`. Adopting from `BLOCKED` is the human's exit: it also resets `count` to 0 and `gaps_fix_used` to false.

**Halt** means stop and report, writing nothing. **BLOCKED** means write the phase, `blocked_from`, and `pending_step` = null in one write (after a step, also `branch_tip_sha` = `HEAD`, once the After every step checks pass), append the cause to `roadblocks.md`, and report what the human must decide. Before `state.json` exists, write the step's id to `stack.json` `blocked` instead, leaving its `phase`, and append to the stack's `roadblocks.md`; before `stack.json` exists, halt. Write a phase only after its action succeeds.

## Phases

- **Start**: dispatch `story`. Present its report and a proposed stack name, a slug of the requirement's title. If the answers raise new questions, re-run `story` once with the requirement and the answers, then present it and ask again. When the human answers and confirms or replaces the name: if `S/stacks/<name>/` exists, ask whether to resume it or choose another name; otherwise write `requirements.md` and `stack.json` with `trunk` from `git symbolic-ref --short refs/remotes/origin/HEAD` minus `origin/` (ask if that fails).
- **`ANALYSIS`**: dispatch `context`, then set `STACK_DECOMPOSITION`. Its report reaches `decompose` and the first `plan` only in the run that produced it; after a resume they run without it.
- **`STACK_DECOMPOSITION`**: dispatch `decompose`. More than one layer halts: "Decomposition proposes <n> layers (<branches>); stacked work is not supported yet. Narrow the requirement to one branch, or abandon." Append a narrowed requirement to `requirements.md` and re-run; `abandon` deletes `S/stacks/<name>/`. With one layer, take the name from its `Branch:` line and require that `git check-ref-format --branch <name>` succeeds, the name is not `stacks` or under `stacks/`, `git show-ref --verify --quiet refs/heads/<name>` fails, and `git ls-remote --exit-code --heads origin <name>` exits 2 (any other non-zero exit cannot verify: ask the human); if the line is missing or a check fails, ask the human for a name and check it. Then write the `PENDING` layer, `active_layer_index` 0, and `LAYERS`.
- **Branch creation** (layer `PENDING`, no `state.json`): run drift check 0. If the branch does not exist, run `git fetch origin <trunk>`, record `F` = `git rev-parse origin/<trunk>`, dispatch `branch`, and require the current branch to be it and `HEAD` to equal `F`. If it already existed, or this thread holds no `F`, require instead the current branch to be it and `git rev-list origin/<trunk>..HEAD` to be empty. Otherwise halt. Write `state.json` in `PLANNING` with `base_sha` = `branch_tip_sha` = `HEAD`, then set the layer `ACTIVE`.
- **`PLANNING`**: dispatch `plan`, write its plan text verbatim to `plan.md`, without the report wrapper or the `Result:` line, then set `WAITING_PLAN_APPROVAL`.
- **`WAITING_PLAN_APPROVAL`** (Gate 1): present `plan.md`. No code is written before approval. `approve` sets `gate_1_plan_approved` and enters `IMPLEMENTING`. Feedback enters `PLANNING`, and the next `plan` prompt carries the previous `plan.md` and the feedback.
- **`IMPLEMENTING`** (Stage A): unless Boot resumes a step, start at `A1` when `branch_tip_sha` equals `base_sha`, else at `A2`; a fix pass starts at `A1-fix`.
  1. `A1`.
  2. `A2`: `FAIL-IN-SCOPE` is a counted failure; `FAIL-UNRELATED` is logged and passes.
  3. `A3`: `ALIGNED` sets `gaps_fix_used` false. `GAPS` with it false runs a fix pass that sets it true, not counted; with it true, `GAPS` is a counted failure. `CONFLICT` sets `BLOCKED`.
  4. `A4`: append `- <UTC time> simplify-diff <tip SHA>: Scope Reductions: <each, separated by "; ", or none>` to `roadblocks.md`. `NONE` skips to 7.
  5. `A5`: if `precut_sha` is null, set it to `branch_tip_sha` in the pending-step write.
  6. `A6v`, then `A6a`. `FAIL-UNRELATED` is logged and passes. If either returns `FAIL-IN-SCOPE`, `GAPS`, or `CONFLICT`, `git reset --hard <precut_sha>`, write `branch_tip_sha`, log it, and re-run `A6v` on that tip, where `FAIL-IN-SCOPE` is a counted failure; the cut failure is not counted.
  7. `A7`, passing the Scope Reductions from the last such `roadblocks.md` entry. Write `last_verdict`, `precut_sha` = null, and `AUDITING`.
- **`AUDITING`** (Stage B): dispatch `B`. `APPROVE` writes `approved_sha` = `HEAD` and `WAITING_RELEASE_APPROVAL`. `REQUEST CHANGES` is a counted failure with the review as input.
- **`WAITING_RELEASE_APPROVAL`** (Gate 2): if `HEAD` differs from `approved_sha`, enter `IMPLEMENTING`, not counted. Present `git diff --stat <base_sha>...HEAD`, the review verdict, `handover.md` with its validation evidence, and the Scope Reductions from the last such `roadblocks.md` entry. No pull request is created before approval. `approve` sets `gate_2_release_approved`, then Release. Feedback runs a fix pass with it as input, not counted.
- **`BLOCKED`**: report the last `roadblocks.md` entry. `fix` with direction runs a fix pass that resets `count` to 0 and `gaps_fix_used` to false, with the direction as input. `re-plan` resets `count` to 0 and enters `PLANNING`. `adopt` per Boot. With `gate_1_plan_approved` false, `fix` and `adopt` return to `blocked_from` instead of entering `IMPLEMENTING`.
- **Stack `blocked`**: report the last entry in the stack's `roadblocks.md`. `fix` with direction appends it to `requirements.md`, clears `blocked`, and re-runs that step; `abandon` deletes `S/stacks/<name>/`.
- **`RELEASED`**: read-only. `gh pr view <pr> --json state`: `MERGED` or `CLOSED` deletes `S/<branch>/` and `S/stacks/<name>/`; `OPEN` reports the pull request and stops.

## Retries

- **Fix pass**: append `- <UTC time> <skill, or human> <tip SHA>: fix: <its input's root cause>` and its input to `roadblocks.md`, then in one write set phase `IMPLEMENTING`, the pass's `count` or `gaps_fix_used` change, and `pending_step` = `{ "A1-fix", "implement", branch_tip_sha }`. Dispatch `A1` with the input, then Stage A from `A2`. A re-run `A1-fix` takes the input of the last `fix` entry in `roadblocks.md`.
- **Counted failure**: if `count` >= `max_allowed`, set `BLOCKED`. Otherwise run a fix pass that increments `count`, with the failing report as input.
- **Not counted**: formatter fixes, unrelated or pre-existing failures (logged), Suggestions and Nitpicks, failures caused only by `A5`, transients, a moved `HEAD` at Gate 2, maintenance, and adoption.
- Only the human's exit from `BLOCKED` (`fix`, `re-plan`, or `adopt`) resets `count` and `gaps_fix_used`.

## Release

With `gate_2_release_approved` true:

1. If `gh pr view <branch> --json number,state,baseRefName` shows no open pull request, dispatch `release`. An open one with a base other than `<trunk>` halts.
2. **RELEASED check**: the same read shows `OPEN` with `baseRefName` equal to `<trunk>`. Exit codes are not evidence.
3. Write `state.json` `RELEASED`, then the layer's `pr` and `RELEASED` in `stack.json`.

A failed `create-pr` or check leaves the phase unchanged; report the cause and re-run once it is resolved.
