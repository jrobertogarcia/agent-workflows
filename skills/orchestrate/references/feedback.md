# Orchestrate: Feedback Tiers

Read this on every run. It extends the orchestrate `SKILL.md`, whose terms, paths, halt, and BLOCKED rules apply here; each section names where that file points to it. `S/<branch>/review.md` is written by Findings in `<resolve>`.

## Tiered Replies

- Tiered: Gate 2 feedback; BLOCKED `fix` with `gate_1_plan_approved` true; `reopen` text.
- Not tiered, and unchanged: Gate 1 feedback, BLOCKED `re-plan`, BLOCKED `fix` with the flag false, `redraft`, and the automatic counted passes (`FAIL-IN-SCOPE`, `GAPS`, a settled A3 conflict, `REQUEST CHANGES`).

## Tier

- **Tagged**: `fix small: <text>` or `fix large: <text>`, or `reopen small: <text>` or `reopen large: <text>`, names the tier; the feedback is the text, and a `reopen` logs it without the tag.
- **`fix <n>, <m>`** (Gate 2 only):
  - If `review.md` is missing, or any number matches no finding in it, stop naming the numbers that matched nothing. Propose no tier and change no state.
  - Otherwise the feedback is, for each selected number, `B`'s finding n from `## Review`, then resolve's per-item report n from `## Recommendations`, all verbatim.
  - Each entry's tier is the `Tier:` line in its per-item report. The reply is large if any entry is large, else small.
  - When any entry has no `Tier:` line (no `## Recommendations`, or none in that report), the reply is untagged.
- **Untagged**:
  - Propose a tier by comparing the feedback with `plan.md`'s Goal, Changes, listed files, and Out of Scope.
  - Present the proposal and stop, leaving the phase unchanged.
  - A bare `small` or `large` (or `fix small` / `fix large` without text) applies the tier to the feedback held in this thread. In `BLOCKED` from `reopen` with nothing held, it applies to the last `reopen:` entry in `roadblocks.md`. Otherwise, ask for the feedback again.

## Small

- Dispatch `plan-delta` with the feedback. A missing or unclosed `<plan>` tag, a missing or invalid `Tier:` line, or `Tier: large` without a `Reason:` line is transient.
- On `Tier: large`, append `- <UTC time> plan-delta <tip SHA>: tier escalated from small: <reason>` to `roadblocks.md` and take Large with the reason. No extra stop: Gate 1 shows the escalation per `<resolve>`.
- On `Tier: small`, the fix-pass input is the feedback verbatim, then a `## Fix plan` heading, then the delta plan verbatim. Append that input to `S/<branch>/resolve.md` under a `## Small fix <UTC time>` heading, so `A3` and `A6a` keep it in the plan on this and later fix passes. Run a fix pass with it per Retries: not counted from Gate 2, after `BLOCKED`'s reset, with `gate_2_release_approved` false, leaving `plan.md` and `gate_1_plan_approved` untouched.
- `B` and Gate 2 always run again.

## Large

- Append the feedback verbatim to `plan-feedback.md` under a `## <UTC time>` heading. After an escalation, follow it with the line `Tier escalated from small: <reason>`.
- Set `gate_2_release_approved` false and enter `PLANNING`, with resolve and Gate 1 per `<resolve>`.
