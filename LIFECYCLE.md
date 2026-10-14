# Agentic Engineering Lifecycle Guide

The lifecycle splits one requirement into phases with explicit human gates: analyze, branch, plan, implement and verify, hand over, review in a fresh thread, and release. Run each skill by hand, or let `orchestrate` drive the whole run.

---

## 1. Overview

```mermaid
graph TD
    OR(["orchestrate (optional driver):<br>runs each step in a fresh subagent,<br>stops at the gates"])

    subgraph Analyzing ["1. Analyze"]
        RS["review-story"]
        GC["gather-context"]
        RW["research-web"]
        RC["root-cause"]
    end

    CB["2. create-branch"]
    PB["3. phase-breakdown"]

    subgraph Loop ["4. Implement & verify (per phase)"]
        PI["plan-implementation"]
        G1{{"Gate: plan approval"}}
        Code["Implement<br>(or delegate-plan)"]
        V["check-alignment · simplify-diff · refactor-code<br>audit-tests · validate-commit · create-commit"]
        PI --> G1 --> Code --> V --> PI
    end

    PH["5. prepare-handover<br>(same thread)"]
    RB["6. review-branch<br>(fresh thread)"]
    Decide{"Verdict"}
    G2{{"Gate: release approval"}}
    CPR["7. create-pr"]
    DL["distill-lessons (as needed)"]

    Analyzing --> CB --> PB --> Loop
    Loop -->|all phases done| PH --> RB --> Decide
    Decide -->|REQUEST CHANGES| Loop
    Decide -->|APPROVE| G2 --> CPR --> DL
    OR -.-> Analyzing
```

---

## 2. Phases

Each skill's description is in the [Skills Index](README.md#skills-index).

### Analyze
Before touching a branch, run whichever of `review-story`, `gather-context`, `research-web`, and `root-cause` the task needs.

### Branch and break down
`create-branch` starts the feature branch from the latest default branch; `phase-breakdown` splits a large change into small, independently verifiable phases.

### Plan, implement, verify
For each phase, `plan-implementation` writes the plan before any code. Save the approved plan to `~/.agent-workflows/<repo>/<branch>/plan.md`; `delegate-plan` and `check-alignment` read it from there by default. It holds the current phase's plan, replaced each phase. Implement it yourself or hand it to another agent with `delegate-plan`; when a delegated agent reports back, run `check-alignment` before trusting the result.

Then verify as needed: `check-alignment` against the plan, `simplify-diff` for cuts, `refactor-code` for structure, `audit-tests` when the suite itself is in question, `validate-commit` before committing, and `create-commit` to commit.

### Hand over, review, release
`prepare-handover` closes the implementation thread, `review-branch` reviews it in a fresh one, `create-pr` opens the pull request, and `distill-lessons` records anything durable learned along the way.

**Thread boundary.** Review quality drops as a conversation grows, so the review runs with a clean context:

1.  Run `prepare-handover` in the implementation thread. It writes `~/.agent-workflows/<repo>/<branch>/handover.md`.
2.  Open a new thread and run `review-branch`, which reads that handover.
3.  On `REQUEST CHANGES`, resolve the findings in the implementation loop and review again. On `APPROVE`, run `create-pr`.

In these paths `<repo>` is the main repository's directory name (shared by its worktrees) and `<branch>` is the current branch; each `/` in a branch name is a nested directory.

---

## 3. Orchestrated Mode

`orchestrate` drives one requirement end to end. When the breakdown yields one layer, it works on one branch; when it yields several, it builds a stack of branches with gh-stack, one pull request per layer, bottom first. Each step goes to a fresh `orchestrate-step` subagent with no conversation history, so every step, `review-branch` included, starts with a clean context. The orchestrator only coordinates and keeps its state under `~/.agent-workflows/<repo>/`; it never edits code.

What you do at each touchpoint:

*   **Story review**: answer the numbered questions from `review-story`, and confirm or replace the proposed stack name.
*   **Plan approval** (each layer): reply `approve`, or give feedback for a revised plan. No code is written before approval.
*   **Release approval** (each layer): read the diff summary, review verdict, handover, and scope reductions; reply `approve` to open the pull request, or give feedback for another fix pass.
*   **BLOCKED or halted**: read the reported cause, then reply `fix` with direction, `re-plan`, or `adopt` (accept the branch as it now stands). Before a branch exists, the only replies are `fix` with direction and `abandon`, which drops the run.

To resume, invoke `orchestrate` again on the layer's branch, or with the stack name before a branch exists. It also stops when three layers are open, the most it allows, until the lowest one merges; invoke it again after the merge. It halts when a pull request was closed with a layer above it; reopen the pull request to continue.

**Requirements**: the `gh` CLI, authenticated. A stack also needs gh-stack 0.2.1 or later (`gh extension install github/gh-stack`) and a github.com repository; without them, `orchestrate` offers to narrow the requirement to one branch.

**Without subagents**: if the host cannot dispatch an `orchestrate-step` subagent, `orchestrate` prints each step's prompt instead. Run it in a fresh thread and paste the report back.

State files, drift checks, retries, and gate rules are defined in [skills/orchestrate/SKILL.md](skills/orchestrate/SKILL.md).

---

## 4. Stack Maintenance After Release

Once layers are open as pull requests, addressing review comments, rebasing, and merging are manual and yours. Do this only while `orchestrate` is not acting on the stack: no layer is active, or the run is waiting at a gate or BLOCKED. On its next run, `orchestrate` accepts a moved layer automatically only when the layer's patches are unchanged, a pure rebase onto its parent. Any edit to the layer it is working on makes its next run halt until you reply `adopt`.

Once per clone, run `git config rerere.enabled true`. A layer checked out in a linked worktree can be edited only in that worktree, and `gh stack rebase --upstack` refuses while the worktree of any affected layer is dirty.

For a review comment on any released layer:

1.  **Sync**: `gh stack checkout`, then `git fetch origin`. For each unmerged layer `<b>`, this must print nothing; otherwise stop and integrate those remote commits first:
    ```bash
    git log --oneline --cherry-pick --right-only <b>...origin/<b> --not origin/<trunk>
    ```
    Then, from the bottom layer, run `gh stack rebase --upstack`. Do not use `gh stack sync` or `gh stack push` anywhere in maintenance: both force-push with leases from their own fetch, and `push` is not atomic.
2.  **Check the parent**: on the layer to edit, `git merge-base --is-ancestor <parent> HEAD` must succeed; otherwise stop.
3.  **Edit** the layer, then run `validate-commit` and `create-commit`.
4.  **Restack**: from the edited layer, run `gh stack rebase --upstack`, then `validate-commit` on each branch above it.
5.  **Push**: `gh stack rebase` fetches unless given `--no-trunk`, so run `git fetch origin` and the step 1 check again. Record `git rev-parse origin/<b>` for every unmerged layer, then, with no fetch in between, push all of them in one atomic push leasing each ref on its recorded SHA:
    ```bash
    git push --atomic origin \
      --force-with-lease=refs/heads/<b1>:<sha1> --force-with-lease=refs/heads/<b2>:<sha2> \
      refs/heads/<b1>:refs/heads/<b1> refs/heads/<b2>:refs/heads/<b2>
    ```
    Afterwards `git ls-remote origin` must show each layer at its local tip. A rejection pushes nothing; retry from the fetch.
6.  **Merge** the bottom layer with `gh stack merge <pr> --squash|--rebase|--merge --yes`. A bare number is tried first as a stack number, then as a PR number, and `--yes` skips confirmation, so first confirm `<pr>` is not also a stack number. Plain `gh pr merge` is refused for stacked pull requests.
7.  **Verify** after a merge: run `git fetch origin`. GitHub retargets the next pull request to trunk and rewrites the branches above, so the next maintenance starts at step 1. On each remaining layer `<b>`, `git log origin/<trunk>..<b>` must list only that layer's own commits. Otherwise run `git rebase --onto origin/<trunk> <headRefOid>` on it, taking the merged PR's `headRefOid` from `gh pr view <pr> --json headRefOid` (after a rebase merge neither the local branch nor trunk holds that layer's commits), then push again as in step 5.

When a pull request merges, `orchestrate` deletes that layer's state on its next run; maintenance never writes it.
