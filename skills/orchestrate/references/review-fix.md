# Orchestrate: Review Fix

Read this on every run. It extends the orchestrate `SKILL.md`, whose terms, paths, halt, and BLOCKED rules apply here; each section names where that file points to it. Findings and `S/<branch>/review.md` are per `<resolve>`; tiers are per `<feedback>`.

## Request Changes

`AUDITING`, after `B` `REQUEST CHANGES` and Findings per `<resolve>`.

- **Blocking**: Critical or Important.
- **Auto-fixable**, a finding that is all of:
  - blocking;
  - new: every finding of a full review is new; on the fix diff, `B` must mark it `New` (a finding carried from `review.md` is never `New`);
  - recommended fix by resolve's per-item report, which ends `Tier: small`;
  - not under Needs you.
- **Continue** when every blocking finding is auto-fixable and, on the fix diff, `New blocking:` equals the number of blocking findings: run a counted failure per Retries as a round-starting short fix pass.
- **Fix input**: for each auto-fixable finding, in `B`'s numbering, `B`'s finding n, then resolve's per-item report n, all verbatim, the shape of `fix <n>, <m>` per `<feedback>`. Suggestions and Nitpicks are never auto-fixed; they go to Gate 2.
- **Otherwise**, go to Leave for Gate 2.

## Short Fix Pass

- **Applies to**: the pass above; Small per `<feedback>` from Gate 2; Small from `BLOCKED` when `blocked_from` is `WAITING_RELEASE_APPROVAL` or `RELEASED` and `HEAD` equals `approved_sha`, or is `AUDITING` and the last `roadblocks.md` entry is led `B: counted failure at cap:`, so `B` returned a verdict since the last `Scope Reductions:` entry; and the inner passes of the Short Path.
- **Full Stage A from `A2` stays** for `BLOCKED` from `IMPLEMENTING`, `BLOCKED` from `AUDITING` on a `B` `STOPPED` or second transient, `adopt` (except Adopt per `<comments>`), re-entry after a rebase (drift check 4), maintenance (drift check 3(b)), a moved `HEAD` at Gate 2, `GAPS` and A3 CONFLICT passes inside full Stage A, and a fix base that fails the Ancestor guard.
- **Round-starting pass**: a Retries fix pass, except that it logs `- <UTC time> <skill, or human> <tip SHA>: short fix: <its input's root cause>` in place of `fix:`, and `pending_step` is `{ "A1f", "implement", branch_tip_sha }`. That entry's `<tip SHA>` is the **fix base**.
- **Inner pass** (`A2f` `FAIL-IN-SCOPE`, `A3f` `GAPS`, a settled `A3f` conflict): a Retries fix pass logged `fix:`, with `pending_step` `A1f`. Its input is the current `fix-input.md` verbatim, then a `## <step id>` heading, then that step's usual fix input verbatim, so the round's findings stay first and the fix base is unchanged.
- **Ancestor guard**: the Short Path and `B` on the fix diff require `git merge-base --is-ancestor <fix base> HEAD` to succeed. When it fails (for example, maintenance rebased the branch in `BLOCKED`, then `retry`), take full Stage A at `A2`.

## Short Path

1. **`A1f`**: `A1` on a fix pass (its table row).
2. **`A2f`**: `A2` (its table row). `FAIL-IN-SCOPE` is a counted failure, run as an inner pass; `FAIL-UNRELATED` is logged and passes.
3. **`A3f`**: step `A3f`. Skill: `check-alignment`. Inputs: `fix-input.md` as the plan, the `A2f` report verbatim, and as context `plan.md` and `S/<branch>/resolve.md` if any. Tokens: `ALIGNED`, `GAPS`, `CONFLICT`.
   - Instructions: "Plan: `fix-input.md`. Phase start commit: `<fix base>`; scope: `git diff <fix base>...HEAD`. Check that the diff addresses each item in the plan and changes nothing else; `plan.md` and `resolve.md` are context, not scope. Take verification results from that report rather than re-running them. `CONFLICT` when any plan-versus-standard conflict exists. Do not re-raise a conflict that `resolve.md` settles."
   - Handle it as `A3`: `ALIGNED` sets `gaps_fix_used` false, `GAPS` follows `gaps_fix_used`, and `CONFLICT` follows A3 CONFLICT per `<resolve>`; each resulting fix pass is an inner pass.
4. **`A7`**: as Stage A step 7, with the Scope Reductions from the last such entry. Write `last_verdict` (from `A3f`), `precut_sha` = null, and `AUDITING`.
5. **`B`** on the fix diff.

- There is no `A4` to `A6`, and `A4` always logs a `Scope Reductions:` entry, so `B` is on the fix diff exactly when the last `short fix:` entry in `roadblocks.md` is later than the last `Scope Reductions:` entry and the Ancestor guard passes.
- **Resume and retry**, each continuation subject to the Ancestor guard:
  - drift check 5 after `A1f` or `A2f` continues the Short Path;
  - an interrupted `A3f` or `A7` leaves no pending step, so the next run takes full Stage A at `A2`, and `B` reviews the full diff;
  - `BLOCKED` `retry` at `A1f`, `A2f`, `A3f`, or `A7` continues the Short Path (`A7` without its held report from `A2f`).

## Trivial Path

A short fix pass whose reply is trivial per `<feedback>`.

- **Marker**: the round-starting entry is logged `short fix: trivial: <root cause>`. The pass is trivial while the last `short fix:` entry is led `trivial:`, is later than the last `Scope Reductions:` and `reopen:` entries, and no `trivial escalated:` entry follows it. Resume, `retry`, and Release re-derive it from `roadblocks.md`.
- **`A1f`**: add the instruction: "Make only the change each selected report recommends. If any needs more than a change to code comments, docs no tool or agent loads as instructions, human-facing wording no test asserts, or identifiers local to one file, or needs any change to the pull request's title or body, commit nothing and stop." Its `STOPPED` sets `BLOCKED` as usual.
- **`A2f`**: on `FAIL-IN-SCOPE`, log `- <UTC time> orchestrate <tip SHA>: trivial escalated: A2f FAIL-IN-SCOPE` and continue per Short Path step 2. `FAIL-UNRELATED` is logged and passes.
- **Threshold**, after `A2f` passes: `git diff --numstat <fix base>...HEAD` trips when added plus deleted lines exceed 20, any entry is binary (`-`), or a changed path is named neither as a selected comment's path nor in its Triage report. On a trip, log `- <UTC time> orchestrate <tip SHA>: trivial escalated: <reason>` and continue the Short Path at `A3f`.
- **Release**: otherwise, in one write set `approved_sha` = `HEAD`, `gate_2_release_approved` true, `pending_step` null, and `WAITING_RELEASE_APPROVAL`, then go to Release in `SKILL.md`. The Triage reply was the approval; no `A3f`, `A7`, `B`, `draft`, or handover runs.
- **Resume and retry**: as Short Path; drift check 5 or `retry` after `A1f` or `A2f` stays on this path while the pass is trivial. After the release write, Gate 2's flag-true rule resumes at Release.

## B on the Fix Diff

- Diff scope: `git diff <fix base>...HEAD`.
- Add the instruction: "Review only this diff, against the findings in `fix-input.md`. Mark each finding `New` unless it restates a finding in `fix-input.md` that the fix did not resolve; a regression the fix introduced is `New`. After your own findings, carry forward verbatim each finding of any severity in `review.md`'s `## Review` that `fix-input.md` does not list and this diff did not address, numbering on in sequence, marked carried and not `New`. On the line before `Open items:`, write `New blocking: <n>`, the number of Critical or Important findings marked `New`."
- A missing or non-numeric `New blocking:` line is transient.

## Leave for Gate 2

- Write `approved_sha` = `HEAD`; `review.md` stays as Findings wrote it. Run Draft per `<release>`, which sets `WAITING_RELEASE_APPROVAL`. Not counted.
- Gate 2 leads with the verdict `REQUEST CHANGES` and, for each blocking finding, why the loop stopped: large, discuss, defer, untiered (a resolve `STOPPED` leaves every finding untiered), under Needs you, carried from the previous review, addressed but unresolved, no new blocking, or auto-fixable but held by another finding.
- `approve` releases with those findings open; `fix <n>, <m>` and the tiers go per `<feedback>`.
