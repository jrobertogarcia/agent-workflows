# Orchestrate: Open Items

It extends the orchestrate `SKILL.md`, the core, whose terms, paths, Halt, and BLOCKED rules apply here; each section names where the skill points to it.

## Resolve Step

- After `story` or `plan`, dispatch `resolve` only when that step reports an `Open items:` count above 0; at 0, skip it. `B` tiers its own findings, so no `resolve` follows it.
- A missing or non-numeric `Open items:` line from `story`, `plan`, or `B`, or `Plan changes:` line from the `PLANNING` `resolve`, is transient.
- A `resolve` that returns `STOPPED` or hits a second transient does not set `BLOCKED`. Instead:
  - append `- <UTC time> resolve-open-items <tip SHA, or none>: <cause>` to the applicable `roadblocks.md`;
  - present the items unresearched.
- Before the stack exists, append the log line to `<provisional>/roadblocks.md`, which moves with the folder per Start in `<start>`.

## Start

- After `story`, dispatch `resolve` with the story report's numbered questions as kind `question`; inputs: `requirements.md` and the `story` report file.
- Present the story report, the Settled and Needs you lists, and the default stack name.
- After the folder moves, `mv` `S/stacks/<name>/reports/resolve-story.md` to `S/stacks/<name>/resolve.md`.
- A Needs you item the human leaves unanswered proceeds on its recommended option; in an unattended run the list is not presented as a question, and unanswered items take their recommended option.
- Add this sentence to the instructions of every step that gets both `requirements.md` and `resolve.md`: "The human's answers in `requirements.md` override `resolve.md`; an unanswered Needs you item takes its recommended option."
- On Start's single `story` re-run (in `<start>`):
  - resolve its questions again, with the first round's Settled list as an input and the instruction: "Carry each Settled item forward unless `requirements.md` overrides it.";
  - on `SETTLED` or `NEEDS-DECISION`, append `## Story re-run` and `S/stacks/<name>/reports/resolve-story-rerun.md` to `resolve.md` by concatenation, keeping the first round's report;
  - present the lists again.
- This adds no stop.

## PLANNING

- After this entry's first `plan.md` is written, delete any `S/<branch>/resolve.md` and `S/<branch>/fix-input.md`, so neither carries an earlier plan's lists or settlements into this one. Dispatch `resolve` on the plan's numbered Open Questions & Assumptions, with `plan.md` as an input, and on `SETTLED` or `NEEDS-DECISION` `mv -f S/<branch>/reports/resolve-plan.md` to `S/<branch>/resolve.md`.
- If the report's `Plan changes:` is above 0, dispatch `plan` once more with `S/<branch>/resolve.md` as an input; it writes `plan.md` itself. This happens at most once per entry to `PLANNING`: the count is held in this thread, and a crash re-runs `PLANNING` from the start.
- Do not resolve the second plan's open items.
- Then set `WAITING_PLAN_APPROVAL`.

## Gate 1

- Lead with a summary: **Scope** (the Goal and the files under Changes in 2-3 lines, Out of Scope in one) and **Risks** (the highest-risk Verification areas, or `none stated`), together at most 6 lines; **Open questions** (each numbered Open Questions & Assumptions item in one line, then each Needs you item with its recommended option). Then give the absolute path of `S/<branch>/plan.md` and the Settled list from `S/<branch>/resolve.md` when it exists. Do not paste the plan, and add nothing the plan lacks.
- Unattended per `<boot>`: when no Needs you item lacks a recommended option, record the auto-answer and proceed as `approve` without presenting; otherwise stop as attended. A Needs you item lacks a recommended option when its resolve report entry has no recommended option line.
- A bare `approve` while Needs you items are open accepts each item's recommended option, which the presentation shows. The re-dispatched plan already assumes those options; when no re-dispatch ran, they did not differ from the plan.

## Findings

`AUDITING`, after `B` `APPROVE`, and after `REQUEST CHANGES` before `<review-fix>` decides; `<feedback>` and `<review-fix>` read the `review.md` this writes.

- **At 0 findings**: delete `S/<branch>/review.md` and go to Draft per `<release>`.
- **Otherwise**, replace `S/<branch>/review.md` with `{ echo '## Review'; cat S/<branch>/reports/B.md; }` via a temp file and `mv -f`, printing nothing. A finding with no `Item <n>:` line is untiered.
- **Gate 2 presentation**: on the first presentation per Re-presentation in `<release>`, read `review.md` and present every finding in it, numbered as `B` numbered it, most severe first, Suggestions and Nitpicks included. Each shows its action and tier from its `Item` line, if any; list the `discuss` findings again after them as the ones needing the human's call. On a re-presentation after a new review, present `New` findings in full, each carried finding as one line (number, severity, action), then the `discuss` list, and the `review.md` path; otherwise name `review.md` unchanged per Re-presentation.
- **Unresolved, when unattended**: the verdict is `REQUEST CHANGES`, or `review.md` holds a line matching `^Finding [0-9]+: (Critical|Important) ` (any suffix, so `carried` findings count; per Item lookups in `<dispatch>`), or any `Item` line has action `discuss`. A `defer` action on a non-blocking finding does not stop.
