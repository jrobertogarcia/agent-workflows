# Agentic Engineering Lifecycle Guide

This guide describes the agentic engineering lifecycle used by this repository. Agentic engineering is professional software delivery through human-directed collaboration with coding agents, supported by explicit context gathering, planning, implementation, verification, review, and release gates.

Rather than relying on a single "one-shot" generation pass, this repository implements a structured, multi-stage pipeline where developers guide intent, approve transitions, and use specialized skills to keep coding-agent work auditable.

---

## 1. Lifecycle Phases

This lifecycle is structured into clear, independent phases to maintain code quality, ensure alignment, and prevent context fatigue.

```mermaid
graph TD
    %% Analyzing Phase
    subgraph Analyzing ["1. Analyzing Phase (Utilities)"]
        GC["gather-context"]
        RW["research-web"]
        RS["review-story"]
        RC["root-cause"]
    end

    %% Branch & Plan Phase
    CB["2. Branch Creation<br>create-branch"]
    PB["3. Phase Breakdown<br>phase-breakdown"]
    
    subgraph Loop ["4. Implementation Loop (Verification Gates)"]
        PI["plan-implementation"]
        Code["Execute Code Changes"]
        
        %% Loop Utilities
        subgraph Utilities ["Verification Utilities (As needed)"]
            CA["check-alignment"]
            CC["check-compliance"]
            PT["plan-testing"]
            RF["refactor-code"]
        end
        
        PI --> Code
        Code --> Utilities
        Utilities --> PI
    end

    %% Handover & Review Phase
    PH["5. Handover Preparation<br>prepare-handover (Same Thread)"]
    Switch["Switch to New Thread<br>(Prevents Context Decay)"]
    RB["6. Branch Audit<br>review-branch (New Thread)"]
    
    %% Branch Review Fixes Decisions
    Decide{"Audit Outcome"}
    FixSame["Small fixes: Tackle in review thread"]
    FixNew["Complex fixes: Spawn new implementation thread"]
    Reverify["Re-verify changes<br>prepare-handover + review-branch"]
    
    %% PR Release Phase
    CPR["7. Pull Request<br>create-pr"]
    RPR["8. PR Review (Optional)<br>review-pr"]

    %% Flow connections
    Analyzing --> CB
    CB --> PB
    PB --> Loop
    Loop -->|Finish all phases| PH
    PH --> Switch
    Switch --> RB
    RB --> Decide
    Decide --> FixSame
    Decide --> FixNew
    FixSame --> Reverify
    FixNew --> Loop
    Reverify --> CPR
    CPR --> RPR
```

---

## 2. Deep Dive by Stage

### Stage 1: Analysis (Pre-Coding Utilities)
Before checking out a branch or modifying files, developers use analysis utilities to define requirements and identify system constraints. This gives coding agents the context needed to act deliberately. Developers can select any combination of these utilities depending on the task:
*   **`gather-context`**: Explores directory structures, configurations, and system boundaries.
*   **`research-web`**: Conducts lookup for modern standards and technical trade-offs.
*   **`review-story`**: Performs logic and sanity-checking checks on user stories.
*   **`root-cause`**: Gathers evidence to debug existing issues without rushing into solutions.

### Stage 2: Branching
Once requirements are clear, execute **`create-branch`** to set up a clean Git branch following Conventional Commits formatting rules.

### Stage 3: Phase Breakdown & Planning
For complex changes, do not write code immediately. Planning creates an explicit engineering contract between the developer and the coding agent.
1.  Run **`phase-breakdown`** to divide the work into discrete, incrementally verifiable steps.
2.  For each step in the breakdown, run **`plan-implementation`** to create an `implementation_plan.md` outlining the proposed edits.

### Stage 4: Implementation Loop (Verification Gates)
With the implementation plan established, coding-agent work proceeds through explicit verification gates. During this loop, the developer selects which verification utilities are needed:
*   **`check-alignment`**: Verifies that actual edits are strictly aligned with the plan.
*   **`check-compliance`**: Runs automated project-specific checks and standards audits.
*   **`plan-testing`**: Details testing sequences.
*   **`refactor-code`**: Refines code cleanly without changing system behavior.

### Stage 5: Handover, Audit, and Release
After implementation completes, run **`prepare-handover`** in the active implementation thread, then switch to a fresh thread for **`review-branch`**. Audit findings must be resolved before release:
*   *Small Issues*: Fix them in the review thread, then re-run **`prepare-handover`** and **`review-branch`** in a fresh thread to confirm the fixes.
*   *Major Issues*: Close the review thread and return to the implementation loop. After the fixes are complete, repeat handover and branch audit before release.
*   **`create-pr`**: Once the branch audit passes, push the branch to origin and prepare the pull request template with AI metadata summaries.
*   **`review-pr`**: Runs automated build validation and PR code reviews (typically performed in an independent PR review thread).

---

## 3. Thread Switching & Context Decay Mitigation

LLMs experience quality degradation as conversation history grows (context window bloat). To counteract this, these workflows actively manage thread boundaries.

### The Handover Protocol
1.  **Wrap Up Coding**: Complete the changes and run **`prepare-handover`** within the **active implementation thread** to summarize the work and verification details.
2.  **Migrate Threads**: Immediately open a **new conversation thread**.
3.  **Run the Audit**: In the fresh thread, run **`review-branch`** to audit the diff. This guarantees that code review is performed by a model with a clean context window, ensuring high review fidelity.
4.  **Tackle Audit Findings**:
    *   *Small Issues*: Fix them directly in the review thread, then re-run **`prepare-handover`** and **`review-branch`** in a fresh thread before opening a PR.
    *   *Major Issues*: Close the thread and spawn a new implementation thread to isolate the complex edits. After implementation completes, repeat handover and branch audit before release.

---

## 4. Operational Best Practices

### Selective Lesson Distillation (`distill-lessons`)
*   **Purpose**: To capture high-value patterns, solutions, or architectural guidelines and codify them into the repository documentation.
*   **Constraint**: Use this utility selectively. Distilling lessons too frequently bloats the guidelines files, eventually inflating the context window of future coding-agent sessions. Only run this skill when the underlying discovery is critical for future workflows.

### Pre-Commit Auditing (`validate-commit`)
*   **Purpose**: Runs linting, compiler validation, and test checks locally.
*   **Constraint**: This utility is optional if the codebase already relies on remote CI/CD pipelines to validate pull requests. Use it locally to catch errors early before pushing.
