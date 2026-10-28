---
name: orchestrate
description: Drive one requirement from story review to open pull requests, on one branch or a stack of branches, dispatching each lifecycle step to a fresh subagent and stopping for plan and release approval. Use only when the user explicitly asks to orchestrate or run the whole lifecycle end to end, to resume an orchestrated run, or to address review comments on an open pull request without posting replies; never for a single step or an ordinary implementation request.
---

# Orchestrate

You coordinate; workers do the work. You dispatch every step, own the state files, and stop for the human at the touchpoints. You never edit code and never run a step's skill in this thread. Run only the git and gh commands this file and its references assign to you. Any other edit, commit, or git or gh write goes to a dispatched step, or you halt. You change `plan.md` only by writing a `plan` report verbatim or the synthesized plan per `<comments>`, and you never push: only `release` does. Never commit, restore, or clean what an interrupted step left behind; drift check 0 halts on it.

## Inputs

- A requirement (text, file, or link) to start; nothing to resume the run on the current branch; or a stack name to resume a run that has no branch yet.
- Human replies: answers and a stack name (story review), `approve` or feedback (gates), `redraft` with feedback (Gate 2), `approve` (a multi-layer split), `fix` with direction, `re-plan` with optional feedback, or `retry` (BLOCKED), `fix small:` or `fix large:` with direction, `fix <n>, <m>` (Gate 2, or `BLOCKED` after `reopen`), or a bare `small` or `large` after a proposed tier (Gate 2, BLOCKED; per `<feedback>`), `adopt` (BLOCKED, or a tip-moved halt), `narrow` with the narrowed requirement (after a multi-layer split or a stacked-work halt), `register <PR number>` (before `LAYERS`), `reopen` with a review, optionally tagged `small:` / `large:` (a released layer), `address <PR number>` (an open pull request; per `<comments>`), `abandon` (any located stack).
- A plain chat reply at a touchpoint continues the run without re-invoking this skill, and Boot runs on it as on an invocation.
- Run one orchestrator session per stack at a time.

## Boot

Run on every invocation, before any other write. **Guard**: unless the human explicitly asked to orchestrate (invoking this skill by name counts), run the whole lifecycle, or resume an orchestrated run, or is replying to this run's touchpoint, ask first; until they confirm, write, rebase, and dispatch nothing.

**Core**: read this file in full before acting. It holds the rules for every phase; the phase text lives in its references.

**References**: read each per Paths and follow it wherever this file or another reference points to it, reading any reference it points to. Read a phase's references on entering the phase, and again before the next action after any context summary.
- `<boot>`: on every invocation and touchpoint reply, after the Guard; run its Locate, Reconcile, drift checks, and Adopt.
- `<dispatch>`: before the first dispatch in a phase, and again after any context summary; never dispatch without it in context.
- `<start>`: Start, `ANALYSIS`, `STACK_DECOMPOSITION`, `WAITING_SPLIT_APPROVAL`, Branch creation, and Stack `blocked`.
- `<stacked>`: whenever `stack.json` holds more than one layer, or the human replies `register`.
- `<resolve>`: Start, `PLANNING`, `WAITING_PLAN_APPROVAL`, `IMPLEMENTING`, `AUDITING`, and `WAITING_RELEASE_APPROVAL`.
- `<review-fix>`: `IMPLEMENTING`, `AUDITING`, `WAITING_RELEASE_APPROVAL`, and `BLOCKED`.
- `<feedback>`: `WAITING_RELEASE_APPROVAL` and `BLOCKED`.
- `<release>`: `AUDITING`, `WAITING_RELEASE_APPROVAL`, and Release.
- `<comments>`: `address`, `reopen`, `RELEASED`, `BLOCKED` from `RELEASED`, Release, and whenever `S/<branch>/comments.md` exists.

**Halt** means stop and report, writing nothing further; anything Reconcile wrote before it is re-derived by the next invocation. **BLOCKED** means write the phase, `blocked_from`, and `pending_step` = null in one write (after a step, also `branch_tip_sha` = `HEAD`, once the After every step checks pass). If the step that set `BLOCKED` is `A5`, after those checks and before that write run `git reset --hard <precut_sha>`, write `branch_tip_sha` = that `HEAD` and `precut_sha` = null in it, and name the discarded tip in the `roadblocks.md` entry. Append the cause, led by the step id when a step set it, to `roadblocks.md`, and report what the human must decide. Before `state.json` exists, write the step's id to `stack.json` `blocked` instead, leaving its `phase`, and append to the stack's `roadblocks.md`; before `stack.json` exists, halt. Write a phase only after its action succeeds.

## Paths

- `<common>` = `git rev-parse --path-format=absolute --git-common-dir`, `<repo>` = `basename(dirname(<common>))`, `<worktree>` = `git rev-parse --show-toplevel`, `S` = `~/.agent-workflows/<repo>`.
- `<root>`: resolve the real path of this file (follow symlinks) and go up three levels, past `skills/orchestrate/SKILL.md`: the repository root, or for an installed copy the directory above the installed skills. Reference a skill as `<root>/skills/<name>/SKILL.md` when that file exists; otherwise, or when this file's path is unknown, as "the installed `<name>` skill".
- `<stacked>`: `references/stacked.md` in the directory that holds this file's real path, or, when this file's path is unknown, that file in the installed `orchestrate` skill.
- `<release>`: `references/release.md` in the directory that holds this file's real path, or, when this file's path is unknown, that file in the installed `orchestrate` skill.
- `<resolve>`, `<feedback>`, `<comments>`, `<review-fix>`, `<dispatch>`, `<boot>`, `<start>`: `references/resolve.md`, `references/feedback.md`, `references/comments.md`, `references/review-fix.md`, `references/dispatch.md`, `references/boot.md`, and `references/start.md`, each resolved like `<release>`.

## State Files

```
S/stacks/<name>/stack.json      S/<branch>/state.json
S/stacks/<name>/requirements.md S/<branch>/plan.md
S/stacks/<name>/roadblocks.md   S/<branch>/handover.md
S/stacks/<name>/context.md      S/<branch>/roadblocks.md
S/stacks/<name>/resolve.md      S/<branch>/fix-input.md
                                S/<branch>/plan-feedback.md
                                S/<branch>/pr-draft.md
                                S/<branch>/resolve.md
                                S/<branch>/review.md
                                S/<branch>/comments.md
                                S/<branch>/replies.md
```

- `<name>` matches `^[a-z0-9][a-z0-9-]{0,39}$`. Each `/` in `<branch>` is a nested directory; a branch named `stacks` or starting `stacks/` halts.
- You alone write `stack.json`, `requirements.md`, `context.md`, `plan.md`, `state.json`, `fix-input.md`, `plan-feedback.md`, `resolve.md`, `review.md`, and `comments.md`. Workers write only `handover.md`, `pr-draft.md`, and `replies.md`. Each `roadblocks.md` is append-only, strictly one line per entry: `- <UTC time> <skill> <tip SHA>: <root cause>`. `fix-input.md` holds the last fix pass's input verbatim, replaced on each fix pass and deleted in `PLANNING` per `<resolve>`. Before `state.json` exists, entries go to the stack's `roadblocks.md`.
- SHAs are full 40-character values. Set `updated_at` (UTC, ISO 8601) on every write. Replace a file atomically:
  ```bash
  tmp="$(mktemp "$dir/state.json.XXXXXX")" && cat > "$tmp" <<'EOF'
  { ... }
  EOF
  mv -f "$tmp" "$dir/state.json"
  ```
- `requirements.md`: the requirement verbatim, then each round of the human's answers verbatim.
- `plan-feedback.md`: plan feedback since the last Gate 1 `approve`, each appended verbatim under a `## <UTC time>` heading (a `re-plan` after approval replaces it). Only `plan` reads it; its presence makes `PLANNING` a re-plan.
- `resolve.md`: per `<resolve>`.
- `review.md`: per `<resolve>`.
- `stack.json` (layer counts include `RELEASED` layers); `phase` is `ANALYSIS`, `STACK_DECOMPOSITION`, `WAITING_SPLIT_APPROVAL`, or `LAYERS`; `git_common_dir` is `<common>` (absent in older files); `blocked` is `null` or the blocked step's id; `layers` holds one entry per layer, bottom first, `status` `PENDING`, `ACTIVE`, or `RELEASED`; `active_layer_index` is the layer being authored:
  ```json
  { "schema_version": 1, "stack_name": "<name>", "trunk": "<trunk>", "git_common_dir": "<common>", "phase": "ANALYSIS", "blocked": null,
    "active_layer_index": null, "layers": [], "updated_at": "<time>" }
  ```
  Layer entry: `{ "index": 0, "branch": "<branch>", "scope": "<scope>", "pr": null, "status": "PENDING" }`; `scope` is the layer's `Scope:` text from `decompose`, verbatim (JSON-escaped); if a layer has no `scope`, ask the human for it before `plan`.
- `state.json`, fixed shape:
  ```json
  {
    "schema_version": 1,
    "git_anchor": { "repo": "<repo>", "branch": "<branch>", "target_branch": "<target>",
                    "base_sha": "<sha>", "branch_tip_sha": "<sha>", "pending_step": null },
    "lifecycle": { "phase": "PLANNING", "active_skill": "plan-implementation", "blocked_from": null },
    "gates": { "gate_1_plan_approved": false, "gate_2_release_approved": false },
    "retries": { "count": 0, "max_allowed": 3, "gaps_fix_used": false },
    "artifacts": { "plan_file": "plan.md", "handover_file": "handover.md", "roadblocks_file": "roadblocks.md",
                   "last_verdict": null, "approved_sha": null, "precut_sha": null },
    "updated_at": "<time>"
  }
  ```
  - `target_branch` (`<target>`): `<trunk>`, or for a layer branched on a parent, the parent's branch. `base_sha`: the `<target>` tip the branch was last based on. `branch_tip_sha`: the last `HEAD` you verified.
  - `pending_step`: `null` or `{ "step_id", "skill", "from_tip_sha" }`; `step_id` `A1-fix` is `A1` on a fix pass; `A1f` and `A2f` are `A1` and `A2` on a short fix pass, and `A3f` its alignment check, per `<review-fix>`.
  - `active_skill`: the skill last dispatched; `pending_step.skill`: the pending step's. Both are `implement` for `A1` and `simplify-diff` for `A5`.
  - `blocked_from`: the phase `BLOCKED` was entered from, kept on a re-entry from `BLOCKED`; null outside `BLOCKED`.
  - `last_verdict`: the last `check-alignment` or `review-branch` verdict. `approved_sha`: `HEAD` when `AUDITING` leaves for Gate 2. `precut_sha`: the tip before the last `A5` dispatch of this Stage A; cleared on entry to `IMPLEMENTING` and where listed.
  - Every entry to `PLANNING` sets `gate_1_plan_approved` and `gaps_fix_used` false and `pending_step` null. Every entry to `IMPLEMENTING`, including from `IMPLEMENTING`, requires `gate_1_plan_approved` true, else halt, and sets `approved_sha` and `precut_sha` null and `gate_2_release_approved` false.

Until the layer has `state.json`, `stack.json` drives the next action: `blocked` if set, else `phase`; after, `state.json` `lifecycle.phase` does.

## Phases

- **`PLANNING`**: dispatch `plan`, write the text between the first `<plan>` and the last `</plan>` verbatim to `plan.md` (a missing or unclosed tag is transient), then run PLANNING per `<resolve>`, then set `WAITING_PLAN_APPROVAL`.
- **`WAITING_PLAN_APPROVAL`** (Gate 1): present `plan.md` with the lists per `<resolve>`. No code is written before approval. `approve` sets `gate_1_plan_approved`, phase `IMPLEMENTING`, and `pending_step` = `{ "A1", "implement", branch_tip_sha }` in one write, deletes `plan-feedback.md`, then dispatches `A1`. Feedback is appended to `plan-feedback.md`, then enters `PLANNING`; so does a `plan-feedback.md` newer than `plan.md`.
- **`IMPLEMENTING`** (Stage A): Gate 1 `approve` starts at `A1`, a fix pass at `A1-fix` (a short fix pass takes the short path per `<review-fix>`), and Boot's Resume at the pending step; every other entry starts at `A2`.
  1. `A1`.
  2. `A2`: `FAIL-IN-SCOPE` is a counted failure; `FAIL-UNRELATED` is logged and passes.
  3. `A3`: `ALIGNED` sets `gaps_fix_used` false. `GAPS` with it false runs a fix pass with the `A3` report as input that sets it true, not counted; with it true, `GAPS` is a counted failure. `CONFLICT` runs A3 CONFLICT per `<resolve>`.
  4. `A4`: append `- <UTC time> simplify-diff <tip SHA>: Scope Reductions: <each, separated by "; ", or none>` to `roadblocks.md`. `NONE` skips to 7.
  5. `A5`: set `precut_sha` to `branch_tip_sha` in the pending-step write.
  6. `A6`:
     1. Run `A6v`. `FAIL-UNRELATED` is logged and passes. If `FAIL-IN-SCOPE`, skip `A6a` and go to 4.
     2. Run `A6a`. If `ALIGNED`, go to `A7`.
     3. On `GAPS` or `CONFLICT`, go to 4.
     4. `git reset --hard <precut_sha>` (this also discards any commits `A6v` made), write `branch_tip_sha`, and log it; this cut failure is not counted.
     5. Run `A6v-cut` (`A6v` again, not `A6a`; this tip already passed `A3`). `FAIL-IN-SCOPE` is a counted failure; otherwise go to `A7`.
  7. `A7`, passing the Scope Reductions from the last such `roadblocks.md` entry. Write `last_verdict` (after the 6.4 reset, `A3`'s verdict, which is for this tip), `precut_sha` = null, and `AUDITING`.
- **`AUDITING`** (Stage B): dispatch `B` (on the fix diff per `<review-fix>`). `APPROVE` writes `approved_sha` = `HEAD`, then runs Findings per `<resolve>`, then Draft per `<release>`, which sets `WAITING_RELEASE_APPROVAL`. `REQUEST CHANGES` with no Critical or Important finding is transient; otherwise it runs Findings per `<resolve>`, then a short fix pass or Gate 2 per `<review-fix>`.
- **`WAITING_RELEASE_APPROVAL`** (Gate 2): `redraft` per `<release>`. Otherwise, if `gate_2_release_approved` is already true and the human's reply is none of feedback, `fix <n>, <m>`, or a bare `small` / `large`, go to Release (a failed release leaves it true; re-invoking does not ask again). Otherwise, if `HEAD` differs from `approved_sha`, enter `IMPLEMENTING`, not counted. Run Draft per `<release>` when `pr-draft.md` is missing or stale. Present `git diff --stat <base_sha>...HEAD`, the review verdict and findings per `<resolve>`, `handover.md` with its validation evidence, the Scope Reductions from the last such `roadblocks.md` entry, and the pull request draft per `<release>`. No pull request is created before approval. `approve` sets `gate_2_release_approved`, then Release. Feedback, `fix <n>, <m>`, or a bare `small` / `large`, even with the flag true, goes per `<feedback>`, not counted; the flag clears only once a tier applies.
- **`BLOCKED`**: report the last `roadblocks.md` entry. `fix` with direction, or a bare `small` / `large`, with `gate_1_plan_approved` true goes per `<feedback>`, resetting `count` to 0 and `gaps_fix_used` to false once a tier applies. `re-plan` resets `count` to 0 and enters `PLANNING`, first appending any feedback to `plan-feedback.md`, or with `gate_1_plan_approved` true replacing it. From `RELEASED`: when `comments.md` lacks `## Triage`, the report adds "reply `retry` to triage the comments", and `retry` (and `adopt`, after its writes) runs Triage per `<comments>`, staying `BLOCKED`; otherwise `retry` repeats Triage's stop. `retry` from another phase re-enters `blocked_from` resetting nothing, at the step named by the last entry led by a step id (`A5` and `A6` steps from `A4`; `A7` without its held validation report from that `A2`, `A2f`, or `A6v`; ✎ with its Pending step write; short-path steps continue per `<review-fix>`), or with none, as usual. `adopt` per Boot. With `gate_1_plan_approved` false, `fix` appends its direction to `plan-feedback.md` and enters `PLANNING` (no fix pass), and `adopt` returns to `blocked_from`.
- **Stack `blocked`**: report the last entry in the stack's `roadblocks.md`. `fix` with direction appends it to `requirements.md`, clears `blocked`, and re-runs that step with the direction as an input; `retry` clears `blocked` and re-runs it; `abandon` per below.
- **`abandon`** (any located stack, any phase): list the paths, then delete `S/stacks/<name>/` and `S/<branch>/` for every layer. Never delete git branches, worktrees, pull requests, or gh-stack metadata; run no git or gh write. Report that the branches and PRs remain.
- **`RELEASED`** (the active layer is `RELEASED`, so none is `PENDING`): read-only. Report each open pull request, and replies per `<comments>`, and stop.
- **`reopen`**, on a `RELEASED` layer's branch with `state.json` and an `OPEN` pull request, `stack.json` phase `LAYERS`, and no layer `ACTIVE` (else halt: handle the review by hand; with no `state.json`, reply `address <PR>`): run Sync and Fetch per `<comments>`; then set the layer `ACTIVE` and `active_layer_index` to it, run Merged target per `<stacked>`, write its `state.json` `BLOCKED` from `RELEASED`, `gate_2_release_approved` false, logging `reopen: <the review, without its small: or large: tag>`, then run Boot step 3, then Triage per `<comments>`. A halt before that write also says: then reply `reopen` again with the review. Text given with `reopen` is a comment per `<comments>`.

## Retries

- **Fix pass**: append `- <UTC time> <skill, or human> <tip SHA>: fix: <its input's root cause>` to `roadblocks.md` and replace `fix-input.md` with its input verbatim, then in one write set phase `IMPLEMENTING`, the pass's `count` or `gaps_fix_used` change, `precut_sha` = null, and `pending_step` = `{ "A1-fix", "implement", branch_tip_sha }` (`A1f`, logged per `<review-fix>`, on a short fix pass). Dispatch it, then Stage A from `A2`, or the short path per `<review-fix>`.
- **Counted failure**: if `count` >= `max_allowed`, set `BLOCKED`, its entry led `<step id>: counted failure at cap:`. Otherwise run a fix pass that increments `count`, with the failing report as input.
- **Not counted**: formatter fixes, unrelated or pre-existing failures (logged), Suggestions and Nitpicks, failures caused only by `A5`, transients, a moved `HEAD` at Gate 2, maintenance, and adoption.
- Only the human's exit from `BLOCKED` (`fix`, `re-plan`, or `adopt`) resets `count`; `gaps_fix_used` resets where stated above.
