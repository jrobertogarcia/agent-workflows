---
name: orchestrate
description: Drive one requirement from story review to an open pull request on a single branch, dispatching each lifecycle step to a fresh subagent and stopping for plan and release approval. Use to run the whole lifecycle end to end.
---

# Orchestrate

You coordinate; workers do the work. You dispatch every step, own the state files, read every SHA from git yourself, and stop for the human at the touchpoints. You never edit code and never run a step's skill in this thread. This version drives one branch; a requirement that needs more than one halts at decomposition.

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
                                S/<branch>/handover.md
                                S/<branch>/roadblocks.md
```

- `<name>` matches `^[a-z0-9][a-z0-9-]{0,39}$`. Each `/` in `<branch>` is a nested directory; a branch named `stacks` or starting `stacks/` halts.
- You alone write `stack.json`, `requirements.md`, `plan.md`, and `state.json`. Workers write only `handover.md`. `roadblocks.md` is append-only, one line per entry: `- <UTC time> <skill> <tip SHA>: <root cause>`.
- SHAs are full 40-character values. Set `updated_at` (UTC, ISO 8601) on every write. Replace a file atomically:
  ```bash
  tmp="$(mktemp "$dir/state.json.XXXXXX")" && cat > "$tmp" <<'EOF'
  { ... }
  EOF
  mv -f "$tmp" "$dir/state.json"
  ```
- `requirements.md`: the requirement verbatim, then each round of the human's answers verbatim.
- `stack.json`; `phase` is `ANALYSIS`, `STACK_DECOMPOSITION`, or `LAYERS`; `layers` holds at most one entry, `status` `PENDING`, `ACTIVE`, or `RELEASED`:
  ```json
  { "schema_version": 1, "stack_name": "<name>", "trunk": "<trunk>", "phase": "ANALYSIS",
    "active_layer_index": null, "layers": [], "updated_at": "<time>" }
  ```
  Layer entry: `{ "index": 0, "branch": "<branch>", "pr": null, "status": "PENDING" }`.
- `state.json`, fixed shape:
  ```json
  {
    "schema_version": 1,
    "git_anchor": { "repo": "<repo>", "branch": "<branch>", "target_branch": "<trunk>",
                    "base_sha": "<sha>", "branch_tip_sha": "<sha>", "pending_step": null },
    "lifecycle": { "phase": "PLANNING", "active_skill": "plan-implementation" },
    "gates": { "gate_1_plan_approved": false, "gate_2_release_approved": false },
    "retries": { "count": 0, "max_allowed": 2 },
    "artifacts": { "plan_file": "plan.md", "handover_file": "handover.md", "roadblocks_file": "roadblocks.md",
                   "last_verdict": null, "approved_sha": null },
    "updated_at": "<time>"
  }
  ```
  - `base_sha`: the trunk tip the branch was last based on. `branch_tip_sha`: the last `HEAD` you verified.
  - `pending_step`: `null` or `{ "step_id", "skill", "from_tip_sha" }`.
  - `active_skill`: the skill last dispatched. `last_verdict`: the last `check-alignment` or `review-branch` verdict. `approved_sha`: `HEAD` at `APPROVE`.
  - Every entry to `PLANNING` sets `gate_1_plan_approved` false. Every entry to `IMPLEMENTING` sets `approved_sha` null and `gate_2_release_approved` false.

## Dispatch

Send each step as one prompt, built from the template, to the `orchestrate-step` agent as a fresh subagent with no conversation history, never a fork or copy of this context. `review-branch` is no exception.

- **Pending step**: before a step marked ✎, write `pending_step` = `{ step_id, skill, from_tip_sha: branch_tip_sha }`. After it returns, read `git rev-parse HEAD` yourself (a reported SHA is only a cross-check) and write `branch_tip_sha` = `HEAD` and `pending_step` = null in one write.
- **After every step**: `git branch --show-current` is unchanged, `git status --porcelain` is empty, and after an unmarked step `HEAD` equals `branch_tip_sha`. Otherwise halt with the report.
- **Result**: read the report's last line, `Result: <token>`. A missing line, crash, timeout, network or rate-limit error is transient: re-run the step once unchanged, not counted; a second transient on the same step sets `BLOCKED`. `STOPPED` sets `BLOCKED` with the report.
- **Fallback**: if you cannot dispatch a fresh `orchestrate-step` subagent (no subagent support, or no agent by that name), write `pending_step` if the step is ✎, print the prompt in one fenced block, ask the human to run it in a fresh thread and bring back its report, and stop.

Template (fill every `<...>`; omit the branch clause before the branch exists):

```
Work only in <worktree>, on branch <branch>; stop and report if `git branch --show-current` differs.
Treat this as a fresh session with no prior conversation.
Step <step_id>: follow <skill reference>. Where it differs from these instructions, follow these. Resolve include directives in that skill relative to the repository root that holds its skills/ directory.
Inputs:
<each absolute path to read, and each report passed verbatim, labeled>
Instructions:
<the step's instructions from the table>
Ask no questions; if an assumption here does not hold, stop and report what you found. Do not write stack.json, state.json, plan.md, or requirements.md under ~/.agent-workflows/.
Report what you did, the files you changed, the checks you ran and their results, and `git rev-parse HEAD` if you committed. The last line is `Result: <one of TOKENS>`.
```

| Step | Skill | ✎ | Inputs | Instructions | Tokens |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `story` | `review-story` | | requirement | Number your clarifying questions. | `READY` |
| `context` | `gather-context` | | `requirements.md` | Target what the requirement names; if ambiguous, choose and list what you skipped. | `READY` |
| `decompose` | `phase-breakdown` | | `requirements.md`, context report | Split into layers, each one independently reviewable pull request; one layer when the change fits one. Give each a Conventional Commits branch name. Second-to-last line: `Layers: <n>`. | `READY` |
| `branch` | `create-branch` | | branch name, trunk | Create exactly `<branch>` from the latest `<trunk>`. | `DONE` |
| `plan` | `plan-implementation` | | `requirements.md`, context report if any; on re-plan the previous `plan.md` and the human's feedback verbatim | Run read-only and write no files; return the complete plan text. | `READY` |
| `A1` | the plan, committed per `create-commit` | ✎ | `plan.md`; on a fix pass, the failing report verbatim | Execute the plan end to end within its scope, skipping work already committed; on a fix pass, fix only what the report names. Run the plan's verification. Commit per `create-commit`. | `DONE` |
| `A2`, `A6v` | `validate-commit` | ✎ | | Commit any fixes per `create-commit`. `FAIL-UNRELATED` when only unrelated or pre-existing failures remain. | `PASS`, `FAIL-IN-SCOPE`, `FAIL-UNRELATED` |
| `A3`, `A6a` | `check-alignment` | | `plan.md` | Scope: the branch diff against `<trunk>`. `CONFLICT` when any plan-versus-standard conflict exists. | `ALIGNED`, `GAPS`, `CONFLICT` |
| `A4` | `simplify-diff` | | `plan.md` | Scope: the branch diff against `<trunk>`. `NONE` when there are no Safe Cuts or Simplifications. | `CUTS`, `NONE` |
| `A5` | `simplify-diff` report | ✎ | `A4` report verbatim, `plan.md` | Apply only its Safe Cuts and Simplifications, only within the plan's scope; apply no Scope Reductions. Commit them separately per `create-commit`. | `DONE` |
| `A7` | `prepare-handover` | | `plan.md`, Scope Reductions verbatim or "none" | Add the Scope Reductions under a `Scope Reductions` heading. | `DONE` |
| `B` | `review-branch` | | | Target branch: `<trunk>`. | `APPROVE`, `REQUEST CHANGES` |
| `release` | `create-pr` | | | Base: `<trunk>`. Keep-checkout: yes. | `DONE` |

## Boot

Run on every invocation, before any write:

1. **Locate**: the `S/stacks/*/stack.json` whose `layers[].branch` is the current branch, else the stack the human names, else start a new run (a requirement is required).
2. **Reconcile**: if `state.json` is `RELEASED` and the layer is not, copy `pr` and `RELEASED` into the layer. If the layer is `PENDING` and `state.json` exists, set it `ACTIVE`.
3. **Drift checks**, for an `ACTIVE` layer, in order:
   0. **Clean tree (halt)**: `git status --porcelain` is empty and the git dir holds no `rebase-merge`, `rebase-apply`, `MERGE_HEAD`, or `CHERRY_PICK_HEAD`.
   1. **Branch (halt)**: `git branch --show-current` equals `git_anchor.branch`; report a detached `HEAD` as such.
   2. **Tip**: if `HEAD` equals `branch_tip_sha` and `pending_step` is set, the step never committed: clear it, run check 4, then re-run the step, not counted.
   3. **Moved tip**:
      - (a) **Crash**: `pending_step` is set and `git merge-base --is-ancestor <from_tip_sha> HEAD` succeeds. Write `branch_tip_sha` = `HEAD` and clear `pending_step`, keeping `from_tip_sha` as the step's starting tip. After check 4, if the human brought the step's report, process it as the step's return; otherwise re-run the step as a transient, not counted.
      - (b) **Maintenance**: the phase is `WAITING_PLAN_APPROVAL`, `WAITING_RELEASE_APPROVAL`, or `BLOCKED`; the `base_sha` and `branch_tip_sha` objects exist; with `P` = `git rev-parse <trunk>`, `git merge-base --is-ancestor P HEAD` succeeds; `git rev-list --merges P..HEAD` is empty; and the ordered `git patch-id --stable` list of `base_sha..branch_tip_sha` equals that of `P..HEAD`. Write `base_sha` = `P`, `branch_tip_sha` = `HEAD`, `approved_sha` = null, append to `roadblocks.md`, and from `WAITING_RELEASE_APPROVAL` enter `IMPLEMENTING`. Not counted.
      - (c) **Otherwise halt**: report the old and new tips and the first differing patch.
   4. **Base check**, against the local `<trunk>` with no fetch: `git rev-parse <trunk>` equals `base_sha` is in sync. If `git merge-base --is-ancestor <base_sha> <trunk>` succeeds, run `git rebase <trunk>`; otherwise upstream was rewritten, so run `git rebase --onto <trunk> <base_sha>`. On a conflict, `git rebase --abort` and set `BLOCKED` naming the files. After a rebase, write `base_sha` = `git rev-parse <trunk>` and `branch_tip_sha` = `git rev-parse <branch>`; from `IMPLEMENTING` or `WAITING_RELEASE_APPROVAL` enter `IMPLEMENTING` at `A2`, otherwise dispatch `A2` alone and log a failure for the next touchpoint.
4. **Adopt** (human reply after a halt or in `BLOCKED`): write `base_sha` = `git merge-base <trunk> HEAD`, `branch_tip_sha` = `HEAD`, `approved_sha` and `pending_step` = null, append to `roadblocks.md`; from `WAITING_RELEASE_APPROVAL` or `BLOCKED` enter `IMPLEMENTING` at `A2`.

**Halt** means stop and report, writing nothing. **BLOCKED** means write the phase, append the cause to `roadblocks.md`, and report what the human must decide. Write a phase only after its action succeeds.

## Phases

- **Start**: dispatch `story`. Present its report and a proposed stack name, a slug of the requirement's title. When the human answers and confirms or replaces the name: if `S/stacks/<name>/` exists, ask whether to resume it or choose another name; otherwise write `requirements.md` and `stack.json` with `trunk` from `git symbolic-ref --short refs/remotes/origin/HEAD` minus `origin/` (ask if that fails).
- **`ANALYSIS`**: dispatch `context`, then set `STACK_DECOMPOSITION`.
- **`STACK_DECOMPOSITION`**: dispatch `decompose`. More than one layer halts: "Decomposition proposes <n> layers (<branches>); stacked work is not supported yet. Narrow the requirement to one branch, or abandon." Append a narrowed requirement to `requirements.md` and re-run; `abandon` deletes `S/stacks/<name>/`. With one layer, check the branch name, then write the `PENDING` layer, `active_layer_index` 0, and `LAYERS`.
- **Branch creation** (layer `PENDING`, no `state.json`): run drift check 0. If the branch does not exist, dispatch `branch`. Then require the current branch to be it and `HEAD` to equal `git rev-parse <trunk>`, else halt. Write `state.json` in `PLANNING` with `base_sha` = `branch_tip_sha` = `HEAD`, then set the layer `ACTIVE`.
- **`PLANNING`**: dispatch `plan`, write its text verbatim to `plan.md`, set `WAITING_PLAN_APPROVAL`.
- **`WAITING_PLAN_APPROVAL`** (Gate 1): present `plan.md`. No code is written before approval. `approve` sets `gate_1_plan_approved` and enters `IMPLEMENTING`. Feedback enters `PLANNING`, and the next `plan` prompt carries the previous `plan.md` and the feedback.
- **`IMPLEMENTING`** (Stage A): start at `A1` when `branch_tip_sha` equals `base_sha` or a fix pass is due, else at `A2`.
  1. `A1`.
  2. `A2`: `FAIL-IN-SCOPE` is a counted failure; `FAIL-UNRELATED` is logged and passes.
  3. `A3`: `GAPS` gets one fix pass (`A1` with the report), then `A2` and `A3` again; `GAPS` again is a counted failure. `CONFLICT` sets `BLOCKED`.
  4. `A4`: `NONE` skips to 7.
  5. `A5`; its starting tip is the pre-cut tip.
  6. `A6v`, then `A6a`. If either fails, `git reset --hard <pre-cut tip>`, write `branch_tip_sha`, log it, and continue. Not counted.
  7. `A7`, passing `A4`'s Scope Reductions. Write `last_verdict` and set `AUDITING`.
- **`AUDITING`** (Stage B): dispatch `B`. `APPROVE` writes `approved_sha` = `HEAD` and `WAITING_RELEASE_APPROVAL`. `REQUEST CHANGES` is a counted failure with the review as the fix input.
- **`WAITING_RELEASE_APPROVAL`** (Gate 2): if `HEAD` differs from `approved_sha`, enter `IMPLEMENTING`, not counted. Present `git diff --stat <base_sha>..HEAD`, the review verdict, and `handover.md` with its validation evidence and Scope Reductions. No pull request is created before approval. `approve` sets `gate_2_release_approved`, then Release. Feedback enters `IMPLEMENTING` with it as the fix input, not counted.
- **`BLOCKED`**: report the last `roadblocks.md` entry. `fix` with direction resets `count` to 0 and enters `IMPLEMENTING` with the direction as the fix input. `re-plan` resets `count` to 0 and enters `PLANNING`. `adopt` per Boot.
- **`RELEASED`**: read-only. `gh pr view <pr> --json state`: `MERGED` or `CLOSED` deletes `S/<branch>/` and `S/stacks/<name>/`; `OPEN` reports the pull request and stops.

## Retries

- **Counted failure**: if `count` >= `max_allowed`, set `BLOCKED`. Otherwise increment `count`, append to `roadblocks.md`, enter `IMPLEMENTING`, and run a fix pass (`A1` with the failing report), then Stage A from `A2`.
- **Not counted**: formatter fixes, unrelated or pre-existing failures (logged), Suggestions and Nitpicks, failures caused only by `A5`, transients, a moved `HEAD` at Gate 2, maintenance, and adoption.
- Only the human's exit from `BLOCKED` resets `count`.

## Release

With `gate_2_release_approved` true:

1. If `gh pr view <branch> --json number,state,baseRefName` shows no open pull request, dispatch `release`. An open one with a base other than `<trunk>` halts.
2. **RELEASED check**: the same read shows `OPEN` with `baseRefName` equal to `<trunk>`. Exit codes are not evidence.
3. Write `state.json` `RELEASED`, then the layer's `pr` and `RELEASED` in `stack.json`.

A failed `create-pr` or check leaves the phase unchanged; report the cause and re-run once it is resolved.
