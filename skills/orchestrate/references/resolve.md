# Orchestrate: Open Items

Read this on every run. It extends the orchestrate `SKILL.md`, whose terms, paths, halt, and BLOCKED rules apply here; each section names where that file points to it.

## Resolve Step

- Dispatch `resolve` only when the step before it reports an `Open items:` count above 0; at 0, skip it.
- A missing or non-numeric `Open items:` line from `story` or `plan`, or `Plan changes:` line from the `PLANNING` `resolve`, is transient.
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
- The human's answers in `requirements.md` override `resolve.md`; add that sentence to the instructions of every step that gets both.
- On Start's single `story` re-run:
  - after it returns, delete `resolve.md`;
  - resolve its questions again, and on `SETTLED` or `NEEDS-DECISION` write its report to `resolve.md`;
  - present the lists again.
- This adds no stop.

## PLANNING

- After writing this entry's first `plan.md`, delete any `S/<branch>/resolve.md`, so it never shows an earlier plan's lists. Dispatch `resolve` on the plan's numbered Open Questions & Assumptions, with `plan.md` as an input, and on `SETTLED` or `NEEDS-DECISION` write its report verbatim to `S/<branch>/resolve.md`.
- If the report's `Plan changes:` is above 0, dispatch `plan` once more with that report as an input, and write its `plan.md`. This happens at most once per entry to `PLANNING`: the count is held in this thread, and a crash re-runs `PLANNING` from the start.
- Do not resolve the second plan's open items.
- Then set `WAITING_PLAN_APPROVAL`.

## Gate 1

- Present `plan.md`, plus the Settled and Needs you lists from `S/<branch>/resolve.md` when it exists.
- A bare `approve` while Needs you items are open accepts each item's recommended option, which the presentation shows. The re-dispatched plan already assumes those options; when no re-dispatch ran, they did not differ from the plan.

## A3 CONFLICT

Stage A step 3 only.

- Dispatch `resolve` with each conflict in the `A3` report as kind `conflict`. Inputs: `plan.md`, `requirements.md`, `context.md` if any, and the `A3` report verbatim. Add the instruction: "Any resolution that would change `plan.md` is NEEDS-DECISION."
- `SETTLED` is handled exactly like `GAPS`, using `gaps_fix_used`, with the resolve report as the fix pass's input.
- `NEEDS-DECISION` sets `BLOCKED` with the resolve report's Needs you list.
