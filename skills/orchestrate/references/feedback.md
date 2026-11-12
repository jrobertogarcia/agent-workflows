# Orchestrate: Feedback Tiers

It extends the orchestrate `SKILL.md`, the core, whose terms, paths, Halt, and BLOCKED rules apply here; each section names where the skill points to it. `S/<branch>/review.md` is written by Findings in `<resolve>`.

## Tiered Replies

- Tiered: Gate 2 feedback; BLOCKED `fix` with `gate_1_plan_approved` true, including `fix <n>, <m>` after `reopen`.
- Not tiered: Gate 1 feedback, BLOCKED `re-plan`, BLOCKED `fix` with the flag false, `redraft`, and the automatic counted pass on `FAIL-IN-SCOPE`. `REQUEST CHANGES` is tiered per `<review-fix>`.

## Tier

- **Tagged**: `fix small: <text>` or `fix large: <text>` names the tier; the feedback is the text.
- **`fix <n>, <m>`** (Gate 2, or `BLOCKED` from `RELEASED` with `S/<branch>/comments.md`):
  - Look each number up per Item lookups in `<dispatch>`, never reading the file: at Gate 2 the `Finding` and `Item` patterns in `review.md`; from `BLOCKED` `grep -m1 -E '^Comment <n>: '` and the `Item` pattern in `comments.md`, with `Human tier:` from `head -1`. If the file is missing, or any number has no `Finding` or comment line, stop naming the numbers that matched nothing, and change no state.
  - The feedback is the selection block per Fix Input in `<dispatch>`. Each entry's tier is the `Tier:` of its `Item` line, except that from `BLOCKED` the item from the human takes `Human tier:` when that is not `none`.
  - The reply is large if any entry is large, else small; an entry with no `Item` line counts as small.
- **Untagged text**: small. A reply that is exactly `small`, `large`, or `file`, `defer` or `drop` with `N<n>` numbers is a form this skill no longer takes (from an older run): say so and ask again, changing no state.

## Small

- Build the fix-pass input per Fix Input in `<dispatch>`, and append `## Small fix <UTC time>` and that input to `S/<branch>/resolve.md` by concatenation, so `B` keeps it in the plan on this and later fix passes.
- Run a fix pass with it per Retries, as a short fix pass where `<review-fix>` allows: not counted from Gate 2, after `BLOCKED`'s reset, with `gate_2_release_approved` false, leaving `plan.md` and `gate_1_plan_approved` untouched.
- A small fix that would leave the plan's bounds makes `A1f` or `A1-fix` stop per the `A1` row, which sets `BLOCKED`; the human then replies `fix large:` or `re-plan`.
- `B` and Gate 2 always run again.

## Large

- Append the human's text, or the selection block, to `plan-feedback.md` under a `## <UTC time>` heading.
- Set `gate_2_release_approved` false and enter `PLANNING`, with resolve and Gate 1 per `<resolve>`.
