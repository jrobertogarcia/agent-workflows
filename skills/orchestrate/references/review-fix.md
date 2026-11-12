# Orchestrate: Review Fix

It extends the orchestrate `SKILL.md`, the core, whose terms, paths, Halt, and BLOCKED rules apply here; each section names where the skill points to it. Findings and `S/<branch>/review.md` are per `<resolve>`; tiers are per `<feedback>`.

## Request Changes

`AUDITING`, after `B` `REQUEST CHANGES` and Findings per `<resolve>`; when unattended, also after `B` `APPROVE` and Findings.

- **Blocking**: Critical or Important.
- **Eligible**, a finding that is all of:
  - new: every finding of a full review is new; on the fix diff, `B` must mark it `New` (a finding carried from `review.md` is never `New`);
  - its `Item` line reads `fix Tier: small`.
- **Auto-fixable**: an eligible blocking finding.
- **Non-blocking selection**: when `stack.json` `unattended` is true and `roadblocks.md` has no entry led `short fix: non-blocking:` and no `reopen:` entry, every eligible Suggestion or Nitpick; otherwise none.
- Take severity and `New` or `carried` from `B`'s `Finding <n>:` lines, and action and tier from `B`'s `Item <n>:` lines, each per Item lookups in `<dispatch>`. Severities are the words `Critical`, `Important`, `Suggestion`, and `Nitpick`.
- **Continue** when every blocking finding is auto-fixable and, on the fix diff, `New blocking:` equals the number of blocking findings: run a counted failure per Retries as a round-starting short fix pass.
- **Fix input**: the selection block of the auto-fixable findings plus the non-blocking selection, in `B`'s numbering, per Fix Input in `<dispatch>`. When the non-blocking selection is non-empty, the round-starting entry is logged `short fix: non-blocking: <root cause>`. Attended, Suggestions and Nitpicks are never auto-fixed; they go to Gate 2.
- **Otherwise**, go to Leave for Gate 2, selecting nothing (non-blocking included).
- **On `APPROVE`** (unattended): when `review.md` has no blocking finding and the non-blocking selection is non-empty, run a round-starting short fix pass with that selection block as input, logged `short fix: non-blocking: <root cause>`, changing no `count`. Otherwise Draft per `<release>`.

## Short Fix Pass

- **Applies to**: the pass above; Small per `<feedback>` from Gate 2; Small from `BLOCKED` when `blocked_from` is `WAITING_RELEASE_APPROVAL` or `RELEASED` and `HEAD` equals `approved_sha`, or is `AUDITING` and the last `roadblocks.md` entry is led `B: counted failure at cap:`; and the inner passes of the Short Path.
- **Full Stage A from `A2` stays** for `BLOCKED` from `IMPLEMENTING`, `BLOCKED` from `AUDITING` on a `B` `STOPPED` or second transient, `adopt` (except Adopt per `<comments>`), re-entry after a rebase (drift check 4 in `<boot>`), a moved `HEAD` at Gate 2, and a fix base that fails the Ancestor guard.
- **Round-starting pass**: a Retries fix pass, except that it logs `- <UTC time> <skill, or human> <tip SHA>: short fix: <its input's root cause>` in place of `fix:`, and writes `pass` = `short`. That entry's `<tip SHA>` is the **fix base**.
- **Inner pass** (`A2f` `FAIL-IN-SCOPE`): a Retries fix pass logged `fix:`, keeping `pass` = `short`. Its input is built per Fix Input in `<dispatch>`, so the round's findings stay first and the fix base is unchanged.
- **Ancestor guard**: the Short Path and `B` on the fix diff require `git merge-base --is-ancestor <fix base> HEAD` to succeed. When it fails (for example, the branch was rebased in `BLOCKED`, then `retry`), write `pass` = `validate` and take full Stage A at `A2`.

## Short Path

1. **`A1f`**: `A1` on a fix pass (its table row).
2. **`A2f`**: `A2` (its table row). `FAIL-IN-SCOPE` is a counted failure, run as an inner pass; `FAIL-UNRELATED` is logged and passes. Then write `AUDITING`.
3. **`B`** on the fix diff.

- `B` is on the fix diff exactly when `pass` is `short` and the Ancestor guard passes.
- **Resume and retry**: drift check 5 in `<boot>`, and `BLOCKED` `retry` at `A1f` or `A2f`, continue the Short Path, subject to the Ancestor guard.

## B on the Fix Diff

- Diff scope: `git diff <fix base>...HEAD`.
- Add the instruction: "Review only this diff, against the findings `fix-input.md` selects: check that it addresses each selected item and changes nothing else; `plan.md` is context, not scope. Mark each finding `New` unless it restates a selected finding that the fix did not resolve; a regression the fix introduced is `New`. After your own findings, carry forward verbatim each finding of any severity in `review.md`'s `## Review` that `fix-input.md` does not select and this diff did not address, numbering on in sequence, marked carried and not `New`, each with its `Item` line renumbered to match. On the line before `Open items:`, write `New blocking: <n>`, the number of Critical or Important findings marked `New`."
- A missing or non-numeric `New blocking:` line is transient.

## Leave for Gate 2

- Write `approved_sha` = `HEAD`; `review.md` stays as Findings wrote it. Run Draft per `<release>`, which sets `WAITING_RELEASE_APPROVAL`. Not counted.
- Gate 2 leads with the verdict `REQUEST CHANGES` and, for each blocking finding, why the loop stopped: large, discuss, defer, untiered (no `Item` line), carried from the previous review, addressed but unresolved, no new blocking, or auto-fixable but held by another finding.
- `approve` releases with those findings open; `fix <n>, <m>` and the tiers go per `<feedback>`.
