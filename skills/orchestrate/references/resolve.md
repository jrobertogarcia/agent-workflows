# Orchestrate: Open Items

It extends the orchestrate `SKILL.md`, the core, whose terms, paths, Halt, and BLOCKED rules apply here; each section names where the skill points to it.

## Resolve Step

- After `story` or `plan`, or after `B` per Findings, dispatch `resolve` only when that step reports an `Open items:` count above 0; at 0, skip it. At A3 CONFLICT, always dispatch it.
- A missing or non-numeric `Open items:` line from `story`, `plan`, or `B`, or `Plan changes:` line from the `PLANNING` `resolve`, is transient.
- A `resolve` that returns `STOPPED` or hits a second transient does not set `BLOCKED`. Instead:
  - append `- <UTC time> resolve-open-items <tip SHA, or none>: <cause>` to the applicable `roadblocks.md`;
  - present the items unresearched;
  - at A3, `CONFLICT` still sets `BLOCKED` with the `A3` report.
- Before the stack exists, append the log line to `<provisional>/roadblocks.md`, which moves with the folder per Start in `<start>`.

## Start

- After `story`, dispatch `resolve` with the story report's numbered questions as kind `question`; inputs: `requirements.md` and the `story` report file.
- Present the story report, the Settled and Needs you lists, and the proposed stack name.
- When the name is confirmed, after the folder moves, `mv` `reports/resolve-story.md` to `S/stacks/<name>/resolve.md`.
- A Needs you item the human leaves unanswered proceeds on its recommended option.
- Add this sentence to the instructions of every step that gets both `requirements.md` and `resolve.md`: "The human's answers in `requirements.md` override `resolve.md`; an unanswered Needs you item takes its recommended option."
- On Start's single `story` re-run (in `<start>`):
  - resolve its questions again, with the first round's Settled list as an input and the instruction: "Carry each Settled item forward unless `requirements.md` overrides it.";
  - on `SETTLED` or `NEEDS-DECISION`, append `## Story re-run` and `reports/resolve-story-rerun.md` to `resolve.md` by concatenation, keeping the first round's report;
  - present the lists again.
- This adds no stop.

## PLANNING

- After this entry's first `plan.md` is written, delete any `S/<branch>/resolve.md` and `S/<branch>/fix-input.md`, so neither carries an earlier plan's lists or settlements into this one. Dispatch `resolve` on the plan's numbered Open Questions & Assumptions, with `plan.md` as an input, and on `SETTLED` or `NEEDS-DECISION` `mv -f reports/resolve-plan.md` to `S/<branch>/resolve.md`.
- If the report's `Plan changes:` is above 0, dispatch `plan` once more with `S/<branch>/resolve.md` as an input; it writes `plan.md` itself. This happens at most once per entry to `PLANNING`: the count is held in this thread, and a crash re-runs `PLANNING` from the start.
- Do not resolve the second plan's open items.
- Then set `WAITING_PLAN_APPROVAL`.

## Gate 1

- Present `plan.md`, plus the Settled and Needs you lists from `S/<branch>/resolve.md` when it exists.
- When `plan-feedback.md` holds a `Tier escalated from small:` line (per `<feedback>`), also present "tier escalated from small: <reason>", so that `approve` confirms the large tier.
- A bare `approve` while Needs you items are open accepts each item's recommended option, which the presentation shows. The re-dispatched plan already assumes those options; when no re-dispatch ran, they did not differ from the plan.

## Findings

`AUDITING`, after `B` `APPROVE`, and after `REQUEST CHANGES` before `<review-fix>` decides; `<feedback>` and `<review-fix>` read the `review.md` this writes.

- **At 0 findings**: delete `S/<branch>/review.md` and go to Draft per `<release>`.
- **Otherwise**, dispatch `resolve` with `B`'s numbered findings as kind `finding`. Inputs: `plan.md`, `requirements.md`, `context.md` if any, and the `B` report file. Add the instruction: "Keep `B`'s numbering. For each finding, recommend fix, defer, or discuss. End each per-item report, Needs you items included, with `Tier: small` when fixing it stays inside `plan.md`'s Goal and Changes and the files it lists and changes nothing in its Out of Scope, else `Tier: large`. End with the `Item <n>:` lines."
- On `SETTLED` or `NEEDS-DECISION`, replace `S/<branch>/review.md` with `{ echo '## Review'; cat reports/B.md; echo '## Recommendations'; cat reports/resolve-findings.md; }` via a temp file and `mv -f`, printing nothing.
- On a `resolve` `STOPPED` or second transient, follow Resolve Step, and write `review.md` the same way with `## Review` and `reports/B.md` only, so the findings have no tier.
- **Gate 2 presentation**: read `review.md` and present every finding in it, numbered as `B` numbered it, most severe first, Suggestions and Nitpicks included. Each shows its action (resolve's recommendation, else the reviewer's `Recommended action`) and its tier, if any. Resolve's Needs you list follows, if any. Label the column "action", so resolve's `deferred` marker is not read as the `defer` action.

## A3 CONFLICT

Stage A step 3, and `A3f` per `<review-fix>`.

- Dispatch `resolve` with each conflict in the `A3` report as kind `conflict`. Inputs: `plan.md`, `requirements.md`, `context.md` if any, and the `A3` or `A3f` report file. Add the instruction: "Any resolution that would change `plan.md` is NEEDS-DECISION."
- `SETTLED` is handled exactly like `GAPS`, using `gaps_fix_used`, with `reports/resolve-conflict.md` as the fix pass's input. First append `## A3 conflict <UTC time>` and that file to `S/<branch>/resolve.md` by concatenation, so later fix passes keep it settled.
- `NEEDS-DECISION` sets `BLOCKED` with the resolve report's Needs you list.
