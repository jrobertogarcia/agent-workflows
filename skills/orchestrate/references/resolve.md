# Orchestrate: Open Items

Read this on every run. It extends the orchestrate `SKILL.md`, whose terms, paths, halt, and BLOCKED rules apply here; each section names where that file points to it.

## Resolve Step

- After `story` or `plan`, or after `B` per Findings, dispatch `resolve` only when that step reports an `Open items:` count above 0; at 0, skip it. At A3 CONFLICT, always dispatch it.
- A missing or non-numeric `Open items:` line from `story`, `plan`, or `B`, or `Plan changes:` line from the `PLANNING` `resolve`, is transient.
- A `resolve` that returns `STOPPED` or hits a second transient does not set `BLOCKED`. Instead:
  - append `- <UTC time> resolve-open-items <tip SHA, or none>: <cause>` to the applicable `roadblocks.md`;
  - present the items unresearched;
  - at A3, `CONFLICT` still sets `BLOCKED` with the `A3` report.
- Before the stack exists, hold the log line in this thread and append it to the stack's `roadblocks.md` when Start writes the stack.

## Start

- After `story`, dispatch `resolve` with the story report's numbered questions as kind `question`; inputs: the requirement verbatim and the `story` report verbatim.
- Present the story report, the Settled and Needs you lists, and the proposed stack name.
- Hold the resolve report in this thread. When the name is confirmed, write it verbatim to `S/stacks/<name>/resolve.md` together with `requirements.md`.
- A Needs you item the human leaves unanswered proceeds on its recommended option.
- Add this sentence to the instructions of every step that gets both `requirements.md` and `resolve.md`: "The human's answers in `requirements.md` override `resolve.md`; an unanswered Needs you item takes its recommended option."
- On Start's single `story` re-run:
  - resolve its questions again, with the first round's Settled list as an input and the instruction: "Carry each Settled item forward unless `requirements.md` overrides it.";
  - on `SETTLED` or `NEEDS-DECISION`, append its report to `resolve.md` under the heading `## Story re-run`, keeping the first round's report;
  - present the lists again.
- This adds no stop.

## PLANNING

- After writing this entry's first `plan.md`, delete any `S/<branch>/resolve.md` and `S/<branch>/fix-input.md`, so neither carries an earlier plan's lists or settlements into this one. Dispatch `resolve` on the plan's numbered Open Questions & Assumptions, with `plan.md` as an input, and on `SETTLED` or `NEEDS-DECISION` write its report verbatim to `S/<branch>/resolve.md`.
- If the report's `Plan changes:` is above 0, dispatch `plan` once more with that report as an input, and write its `plan.md`. This happens at most once per entry to `PLANNING`: the count is held in this thread, and a crash re-runs `PLANNING` from the start.
- Do not resolve the second plan's open items.
- Then set `WAITING_PLAN_APPROVAL`.

## Gate 1

- Present `plan.md`, plus the Settled and Needs you lists from `S/<branch>/resolve.md` when it exists.
- When `plan-feedback.md` holds a `Tier escalated from small:` line (per `<feedback>`), also present "tier escalated from small: <reason>", so that `approve` confirms the large tier.
- A bare `approve` while Needs you items are open accepts each item's recommended option, which the presentation shows. The re-dispatched plan already assumes those options; when no re-dispatch ran, they did not differ from the plan.

## Findings

`AUDITING`, after `B` `APPROVE`, and after `REQUEST CHANGES` before `<review-fix>` decides; `<feedback>` and `<review-fix>` read the `review.md` this writes.

- **At 0 findings**: delete `S/<branch>/review.md` and go to Draft per `<release>`.
- **Otherwise**, dispatch `resolve` with `B`'s numbered findings as kind `finding`. Inputs: `plan.md`, `requirements.md`, `context.md` if any, and the `B` report verbatim. Add the instruction: "Keep `B`'s numbering. For each finding, recommend fix, defer, or discuss. End each per-item report, Needs you items included, with `Tier: small` when fixing it stays inside `plan.md`'s Goal and Changes and the files it lists and changes nothing in its Out of Scope, else `Tier: large`."
- On `SETTLED` or `NEEDS-DECISION`, replace `S/<branch>/review.md` with `## Review` and the `B` report verbatim, then `## Recommendations` and the resolve report verbatim.
- On a `resolve` `STOPPED` or second transient, follow Resolve Step, and write `review.md` with `## Review` only, so the findings have no tier.
- **Gate 2 presentation**: every finding in `review.md`, numbered as `B` numbered it, most severe first, Suggestions and Nitpicks included. Each shows its action (resolve's recommendation, else the reviewer's `Recommended action`) and its tier, if any. Resolve's Needs you list follows, if any. Label the column "action", so resolve's `deferred` marker is not read as the `defer` action.

## A3 CONFLICT

Stage A step 3, and `A3f` per `<review-fix>`.

- Dispatch `resolve` with each conflict in the `A3` report as kind `conflict`. Inputs: `plan.md`, `requirements.md`, `context.md` if any, and the `A3` report verbatim. Add the instruction: "Any resolution that would change `plan.md` is NEEDS-DECISION."
- `SETTLED` is handled exactly like `GAPS`, using `gaps_fix_used`, with the resolve report as the fix pass's input. First append the report to `S/<branch>/resolve.md` under a `## A3 conflict <UTC time>` heading, so later fix passes keep it settled.
- `NEEDS-DECISION` sets `BLOCKED` with the resolve report's Needs you list.
