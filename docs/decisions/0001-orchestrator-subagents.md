# 0001. Orchestrated authoring of stacked PRs with subagents

**Status**: Proposed
**Date**: 2026-10-13

## Context

Today the skills run by hand across thread boundaries. `prepare-handover` writes a handover file that `review-branch` reads in a fresh thread, and `plan-implementation` stops for approval. Large changes need a stack of small PRs, and a person coordinating many layers by hand is the bottleneck.

This ADR covers authoring: from a requirement to each layer being `RELEASED`, meaning that layer's PR is open with the correct base and, from the second layer on, listed in the remote stack. Maintenance after release (review comments, upstream rebases) is covered in [ADR 0002](0002-stack-maintenance-and-rebasing.md).

The design keeps individual skills as the atomic building blocks and adds one coordinating skill, `orchestrate`, that drives them, owns the state on disk, and stops at two human gates.

## Decision

### D1. Skill set: 18 plus `orchestrate`

- **Removed**: `review-pr` (auditing someone else's PR is outside the authoring lifecycle).
- **Folded**: `plan-testing` into `plan-implementation`, so test scenarios and coverage boundaries live in the plan. `check-compliance` into `check-alignment`.
- **Merged checker**: `check-alignment` is one read-only pass over the actual diff with two sections, Plan fidelity and Standards. Its result is `ALIGNED` or `GAPS`. It never edits code or the plan. Standards runs without a plan. A conflict between the plan and a standard is reported, not resolved.
- **Kept**: `review-story` (requirements and assumptions before planning), `gather-context` (factual codebase context), `phase-breakdown` (becomes the stack decomposition step), `refactor-code` (on demand).
- **Quality checks**: `simplify-diff` runs at the end of Stage A (D7). `audit-tests` runs on demand only and is not part of the pipeline.
- **New**: `orchestrate`.

### D2. Dispatch

`orchestrate` is the only dispatcher. `delegate-plan` stays prompt-only: it produces a self-contained prompt and runs nothing.

- The orchestrator sends one self-contained prompt per step to a shipped agent definition, `orchestrate-step`: a generic worker that executes the prompt it is given. Its Markdown source lives in a new `agents/` directory.
- `setup.py` installs it per host:
  - `~/.claude/agents/`: Claude Code and Cursor (docs-confirmed).
  - `~/.gemini/config/agents/`: Antigravity (docs-confirmed).
  - `~/.codex/agents/`: Codex, as TOML generated from the Markdown source.
  - Copilot: user-level path unverified (open item 1).
  - Windsurf has no subagents and uses the printed-prompt fallback.
- Each step starts fresh. A step is never forked from the orchestrator's context. Fresh context is documented on Claude Code, Cursor, and Antigravity, and unverified on Codex and Copilot (open item 1). On Claude Code, interactive sessions fork by default, so the orchestrator always invokes `orchestrate-step` by name.
- Fallback: if the host has no subagent support or `orchestrate-step` is not installed, the orchestrator prints the prompt in a fenced block and stops, so a person can run it in a fresh thread.
- Skills name no host and no host tools. Host specifics live only in `setup.py` and this ADR.
- `review-branch` always runs in a fresh subagent so the reviewer shares no context with the implementer.

### D3. Stack and release

Large work is split into small, independently reviewable diffs, authored bottom to top.

- **Scope**: github.com only. GitHub Enterprise Server is unsupported until GitHub ships stacked PRs there. Stacked PRs are generally available on github.com since 2026-10-06 (GitHub changelog). Auto-merge for stacks is still rolling out (changelog; not trial-tested).
- **gh-stack**: the official `github/gh-stack` extension, minimum v0.2.1. It is a hard dependency with no plain-git fallback. If it is missing or older, the orchestrator stops and tells the user to install or upgrade it. Documented limits, not trial-tested: linear history, same-repository branches, at most 100 PRs. All three merge methods work (observed, see ADR 0002 D1 step 7).
- **Availability**: before the first stack command, `gh api repos/<o>/<r>/stacks` must return 200 (observed on a repository with stacks available). Anything else stops the run. The response when stacks are unavailable is unverified (open item 2).
- **Tracking**: every layer is created with `gh stack init` (layer 0) or `gh stack add` (later layers). A plain-git branch that is linked later is not tracked locally, and `gh stack sync` then fails (observed).
- **Open-layer cap**: at most 3 layers may be released but unmerged. `PENDING` layers do not count, and there is no limit on total layers. Before branching the next layer, if 3 are open, the orchestrator halts with "waiting on merge of <bottom PR>" and resumes after that PR merges with `git fetch origin`, the ADR 0002 D1 step 1 remote-only-commit check, then `gh stack rebase --upstack`. Merge state is read live with `gh pr view --json state`. The cap is fixed at 3 and is revisited only if a human reports it as a bottleneck.
- **Release**: at Gate 2, `create-pr` opens the layer's PR with base `git_anchor.target_branch` (the trunk for layer 0). `create-pr` takes an optional base argument. With no base it omits `--base`. It stops if the base is missing on origin and verifies `baseRefName` after creating the PR. Once two or more PRs exist, `gh stack link <every open layer PR, bottom to top>` creates or updates the remote stack and repairs wrong bases. `gh stack sync` and `gh stack submit` are not used for release.
- **Link facts** (observed): `gh stack link` creates a new stack from unstacked PRs. It pushes with `git push --atomic` and no force, so a non-fast-forward is rejected, nothing is pushed, and the exit code is 1. A failed link is re-run after resolving the cause. A locally amended or rebased layer with no divergent remote is expected to be rejected the same way (unverified).
- **RELEASED**: `gh pr view --json state,baseRefName` shows the PR open with the right base, and `gh api 'repos/<o>/<r>/stacks?pull_request=<N>'` lists the PR. Layer 0 alone needs only the base check. Exit codes are not evidence of success for `gh stack sync` or `gh stack view`.
- **Failure**: a failed `create-pr` or link is re-run after the cause is resolved, and the phase does not advance until the RELEASED check passes. If local tracking is lost, `gh stack init <every unmerged layer, bottom to top>` re-adopts the branches and finds their PRs (observed). A partial list leaves the stack unreconciled with exit 0. A list that includes a merged layer makes `gh stack sync` fail on a conflict.

### D4. State on disk

State lives outside the repository in `~/.agent-workflows/<repo>/`, so working trees stay clean and multiple worktrees share it.

```
stacks/<name>/stack.json
<branch>/state.json
<branch>/plan.md
<branch>/handover.md
<branch>/roadblocks.md
```

- `stack.json` is the roadmap: the epic, ordered layers, and the active layer.
- `state.json` is the ledger for one branch. It has a fixed shape of scalars and fixed keys, with no arrays that grow.
- `plan.md` and `handover.md` are the human-readable evidence.
- `roadblocks.md` is append-only. Each entry records a timestamp, the failing skill, the tip SHA, and the root cause.
- Each file has a single writer. The `orchestrate` thread writes `stack.json`. The thread driving a branch writes that branch's `state.json`. Everything else reads. If a second writer is ever added, guard the file with an `mkdir` lock, because `flock` is not available on macOS.
- All SHAs are full 40-character values.
- Writes go to a temp file in the same directory, then a rename:

```bash
dir="$HOME/.agent-workflows/<repo>/<branch>"
tmp="$(mktemp "$dir/state.json.XXXXXX")"
cat > "$tmp" <<'EOF'
{ ... }
EOF
mv -f "$tmp" "$dir/state.json"
```

- **Lifecycle**: a branch's state is read-only after `RELEASED`. `orchestrate` deletes the branch directory when its PR merges or closes, and deletes `stack.json` when the last layer merges. It detects both from the live read at resume or at the open-layer cap check.

### D5. Schemas

Stack manifest, `stacks/<name>/stack.json`. A layer's `status` is `PENDING`, `ACTIVE`, or `RELEASED`. There is no `MERGED` value, because merge state is read live from GitHub.

```json
{
  "schema_version": 1,
  "stack_name": "user-auth-epic",
  "trunk": "main",
  "active_layer_index": 1,
  "layers": [
    { "index": 0, "branch": "feat/auth-models", "pr": 101, "status": "RELEASED" },
    { "index": 1, "branch": "feat/auth-endpoints", "pr": null, "status": "ACTIVE" },
    { "index": 2, "branch": "feat/auth-ui", "pr": null, "status": "PENDING" }
  ],
  "updated_at": "2026-10-13T00:00:00Z"
}
```

Branch ledger, `<branch>/state.json`:

```json
{
  "schema_version": 1,
  "git_anchor": {
    "repo": "agent-workflows",
    "branch": "feat/auth-endpoints",
    "target_branch": "feat/auth-models",
    "base_sha": "b4e6975b23b56dbfeca9f10f250dc66ffae76e90",
    "branch_tip_sha": "f3367fc8b9b5af8570cf822440944d0496b38d11"
  },
  "lifecycle": { "phase": "WAITING_PLAN_APPROVAL", "active_skill": "plan-implementation" },
  "gates": { "gate_1_plan_approved": false, "gate_2_release_approved": false },
  "retries": { "count": 0, "max_allowed": 2 },
  "artifacts": {
    "plan_file": "plan.md",
    "handover_file": "handover.md",
    "roadblocks_file": "roadblocks.md",
    "last_verdict": null,
    "approved_sha": null
  },
  "updated_at": "2026-10-13T00:00:00Z"
}
```

- `base_sha` is the target's tip when the branch was last based on it.
- `branch_tip_sha` is updated after every orchestrator commit.
- `approved_sha` is `HEAD` when `review-branch` returns `APPROVE`. It is cleared on any return to `IMPLEMENTING`.

### D6. Lifecycle state machine

```mermaid
stateDiagram-v2
    [*] --> ANALYSIS: first layer
    [*] --> PLANNING: later layer
    ANALYSIS --> STACK_DECOMPOSITION: review-story and gather-context done
    STACK_DECOMPOSITION --> PLANNING: phase-breakdown done
    PLANNING --> WAITING_PLAN_APPROVAL: plan-implementation done
    WAITING_PLAN_APPROVAL --> IMPLEMENTING: Gate 1 approved
    WAITING_PLAN_APPROVAL --> PLANNING: Gate 1 rejected
    IMPLEMENTING --> IMPLEMENTING: counted failure below cap
    IMPLEMENTING --> AUDITING: Stage A passes
    IMPLEMENTING --> BLOCKED: cap reached, repeat transient, or plan vs standard conflict
    AUDITING --> IMPLEMENTING: REQUEST CHANGES below cap
    AUDITING --> BLOCKED: REQUEST CHANGES at cap
    AUDITING --> WAITING_RELEASE_APPROVAL: APPROVE
    WAITING_RELEASE_APPROVAL --> IMPLEMENTING: Gate 2 changes requested or HEAD moved
    WAITING_RELEASE_APPROVAL --> RELEASED: Gate 2 approved and PR confirmed
    BLOCKED --> IMPLEMENTING: human fix
    BLOCKED --> PLANNING: human re-plan
    RELEASED --> [*]
```

- The phase enum is the set of states above. A branch's `lifecycle.phase` holds one of them.
- A phase is written only after its action succeeds. A handoff that is still waiting, or a failed `create-pr` or link, leaves the phase unchanged.
- On resume, the orchestrator reconciles the ledger against git and PR evidence before acting (D10).
- A return from Gate 2 because `HEAD` moved is not a counted retry.

### D7. Verification loop

Polishing happens before review, so the reviewer sees the diff that will ship.

**Stage A**, per layer:

1. Implement.
2. `validate-commit`.
3. `check-alignment`.
4. `simplify-diff`.
5. The orchestrator applies the Safe Cuts and Simplifications that stay within the Gate 1 plan scope. Scope Reductions are not applied; they are listed for Gate 2.
6. `validate-commit`, then `check-alignment` again.
7. `prepare-handover`, which writes `Branch tip: <full 40-char SHA>` as the first line of the handover. `review-branch` prefix-matches it against `HEAD`.

**Stage B**: `review-branch` in a fresh subagent. `APPROVE` records `approved_sha`. `REQUEST CHANGES` returns to implementing (D9).

### D8. Human gates

Exactly two gates:

1. **Gate 1** (`WAITING_PLAN_APPROVAL`): the human approves the plan, dependencies, and blast radius. No code is written before `gate_1_plan_approved` is `true`.
2. **Gate 2** (`WAITING_RELEASE_APPROVAL`): the human sees the approved diff (`HEAD` equals `approved_sha`), the `review-branch` verdict, the validation evidence, and the listed Scope Reductions. No PR is created before `gate_2_release_approved` is `true`. If `HEAD` no longer equals `approved_sha`, the layer returns to `IMPLEMENTING`.

### D9. Retries

One counter, `retries.max_allowed` = 2, giving at most 3 attempts. On a counted failure: if `count >= max_allowed`, set `BLOCKED`. Otherwise increment `count`, append to `roadblocks.md`, and return to `IMPLEMENTING`.

- **Counted**: a handed-off tip that still fails after the implementer's single fix pass. That means an in-scope `validate-commit` failure after its auto-fix, `check-alignment` `GAPS` after one fix pass and a re-run, or `review-branch` `REQUEST CHANGES`.
- **Not counted**: formatter fixes, unrelated or pre-existing failures (logged), and Suggestions or Nitpicks.
- **Transient** (timeout, network, rate limit, host crash): one unchanged re-run, not counted. A second transient failure sets `BLOCKED`.
- **Plan vs standard conflict**: straight to `BLOCKED`.
- **Reset**: a human exit from `BLOCKED` resets `count` to 0, so the cap applies per stint. The orchestrator never resets it. `roadblocks.md` keeps the history.

### D10. Drift checks

On every boot, before any edit:

1. **Tip check (halt)**: `git branch --show-current` must equal `git_anchor.branch` and `git rev-parse HEAD` must equal `branch_tip_sha`. A mismatch halts the run, leaves the phase unchanged, and is reported.
2. **Base check (classify)**, against the local target ref with no fetch:
   - `git rev-parse <target>` equals `base_sha`: in sync.
   - `git merge-base --is-ancestor <base_sha> <target>` succeeds: upstream advanced, so rebase onto the target.
   - Otherwise: upstream was rewritten, so run `git rebase --onto <target> <base_sha>`.

After a rebase, set `base_sha` to the target tip and `branch_tip_sha` to `HEAD`, then re-run `validate-commit`. A conflict sets `BLOCKED`.

Plain-git rebases leave gh-stack's recorded SHAs stale. The next `gh stack rebase` refreshes them without moving any branch (observed locally, with no push in between).

### D11. Reference, don't duplicate

Prompts sent to subagents point at `skills/<name>/SKILL.md` rather than copying it. `agents/` holds only the generic `orchestrate-step`.

### D12. Human role

The human acts as technical lead at five touchpoints: define intent and scope (`review-story`), approve the plan (Gate 1), resolve `BLOCKED`, approve the release (Gate 2), and codify lessons (`distill-lessons`). The human also owns stack maintenance after release (ADR 0002).

## Consequences

- gh-stack v0.2.1+ and github.com are required.
- Each stint allows 3 attempts before the human is involved.
- Every stack step is confirmed by reading GitHub state, not by exit code.

## Open items

| # | Item | Status | What closes it |
| :-- | :-- | :-- | :-- |
| 1 | Copilot user-level agent path, and fresh context on Codex and Copilot | Unverified | Host docs or per-host trial |
| 2 | Stacks API response when stacks are unavailable | Unverified (200 observed when available) | Probe a repository without stacks |
