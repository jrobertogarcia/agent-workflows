# Orchestrate: Feedback Tiers

It extends the orchestrate `SKILL.md`, the core, whose terms, paths, Halt, and BLOCKED rules apply here; each section names where the skill points to it. `S/<branch>/review.md` is written by Findings in `<resolve>`.

## Tiered Replies

- Tiered: Gate 2 feedback; BLOCKED `fix` with `gate_1_plan_approved` true, including `fix <n>, <m>` after `reopen`.
- Not tiered: Gate 1 feedback, BLOCKED `re-plan`, BLOCKED `fix` with the flag false, `redraft`, `file`, `defer` and `drop` replies, and the automatic counted passes (`FAIL-IN-SCOPE`, `GAPS`, a settled A3 conflict). `REQUEST CHANGES` is tiered per `<review-fix>`.

## Tier

- **Tagged**: `fix small: <text>` or `fix large: <text>` names the tier; the feedback is the text.
- **`fix <n>, <m>`** (Gate 2, or `BLOCKED` from `RELEASED` with `S/<branch>/comments.md`):
  - Look each number up per Item lookups in `<dispatch>`, never reading the file: at Gate 2 the `Finding` and `Item` patterns in `review.md`; from `BLOCKED` `grep -m1 -E '^Comment <n>: '` and the `Item` pattern in `comments.md`, with `Human tier:` from `head -1`. If the file is missing, or any number has no `Finding` or comment line, stop naming the numbers that matched nothing. Propose no tier and change no state.
  - The feedback is the selection block per Fix Input in `<dispatch>`. Each entry's tier is the `Tier:` of its `Item` line, except that from `BLOCKED` the item from the human takes `Human tier:` when that is not `none`.
  - The reply is large if any entry is large, trivial if every entry is trivial, else small. Only Triage's reports carry `Tier: trivial`; `Human tier:` stays small or large, and no tag or untagged proposal is trivial.
  - When any entry has no `Item` line, the reply is untagged.
- **Untagged**:
  - Propose a tier by comparing the feedback with `plan.md`'s Goal, Changes, listed files, and Out of Scope.
  - Present the proposal and stop, leaving the phase unchanged, and record `Ruling: proposed tier <small|large>, awaiting reply` per Decisions in `<boot>`.
  - A bare `small` or `large` (or `fix small` / `fix large` without text) applies the tier to the feedback of the latest proposal entry for this branch in `decisions.md` (its `Reply:` lines up to `Ruling:`, found by `grep`), when no entry for this branch other than `file`, `defer` or `drop` follows it. Otherwise, ask for the feedback again.

## Small

- **No plan-delta**: when the reply is `fix <n>, <m>` and every selected `Item` line's action is `fix`, the fix-pass input is the selection block, with no `## Fix plan`; append and run it as for `Tier: small` below.
- Otherwise (free-text `fix small:`, a bare `small`, or a selected `Item` line whose action is defer, discuss, or `already answered`), dispatch `plan-delta` with the human's text, or the selected numbers and the source path. A missing or invalid `Tier:` line, or `Tier: large` without a `Reason:` line is transient.
- On `Tier: large`, append `- <UTC time> plan-delta <tip SHA>: tier escalated from small: <reason>` to `roadblocks.md` and take Large with the reason. No extra stop: Gate 1 shows the escalation per `<resolve>`.
- On `Tier: small`, build the fix-pass input per Fix Input in `<dispatch>`, and append `## Small fix <UTC time>` and that input to `S/<branch>/resolve.md` by concatenation, so `A3` and `A6a` keep it in the plan on this and later fix passes. Run a fix pass with it per Retries, as a short fix pass where `<review-fix>` allows: not counted from Gate 2, after `BLOCKED`'s reset, with `gate_2_release_approved` false, leaving `plan.md` and `gate_1_plan_approved` untouched.
- `B` and Gate 2 always run again, except on the Trivial Path per `<review-fix>`.

## Trivial

Handled as Small; when Small skips plan-delta and it is a short fix pass per `<review-fix>`, it takes the Trivial Path, otherwise it is small.

## Large

- Append the human's text, or the selection block, to `plan-feedback.md` under a `## <UTC time>` heading. After an escalation, follow it with the line `Tier escalated from small: <reason>`.
- Set `gate_2_release_approved` false and enter `PLANNING`, with resolve and Gate 1 per `<resolve>`.
