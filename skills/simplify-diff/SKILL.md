---
name: simplify-diff
description: Audit the work in flight for over-engineering and unnecessary code, and report the cuts that would shrink the diff. Use when a change is correct but larger than it needs to be.
model: opus
effort: medium
---

# Simplify Diff

## Anti-Patterns
- **Unwarranted Abstraction** — helpers, interfaces, wrappers, or config knobs introduced for a single call site.
- **Redundant Defense** — null, type, or range checks that the type system, a caller contract, or an upstream validation already guarantees.
- **Swallowed Failure** — broad catch blocks, fallbacks, and silent no-ops that mask distinct error conditions instead of letting them surface.
- **Speculative Extensibility** — parameters, hooks, and branches serving hypothetical future requirements rather than a present caller.
- **Compatibility Shims** — feature flags, re-exports, deprecated wrappers, and dead branches kept for callers that do not exist.
- **Narrating Comments** — comments and docstrings restating what the code already says, including references to the task or ticket that produced it.
- **Reinvented Primitives** — hand-rolled implementations of standard library or existing in-repo utilities.
- **Incidental Scope** — reformatting, renames, and unrelated fixes inflating a diff whose stated purpose is something else.

## Execution
1. **Enter Plan Mode**: Switch the session into plan mode (or the host's read-only planning equivalent) before reading anything, and stay in it until the plan is approved. If the host has no such mode, treat this run as read-only.
2. **Scope** — default to the branch diff against its target plus uncommitted changes; narrow if the user names a target. Reuse context already gathered in this thread rather than re-reading it.
3. **Read for Invariants** — read enough of the surrounding code, call sites, and type definitions to know what is already guaranteed. A check is only redundant if you have seen the guarantee.
4. **Audit** — record concrete instances of the anti-patterns above with file and line references, each with the specific cut and the code that remains. Report the absence of a problem as readily as its presence, and name any area you could not assess rather than implying it passed.
5. **Protect What Is Load-Bearing** — do not propose cutting validation at genuine system boundaries (user input, I/O, network, external APIs), handling for failure modes that actually occur, or anything the project's standards require. Say explicitly when a check that looks redundant is in fact carrying weight.
6. **Prioritize** — group findings by impact: Safe Cuts (removable with no behavioral question), Simplifications (same behavior, less structure), and Scope Reductions (changes that belong in a separate change entirely). Omit any group with no findings.
7. **Report Only** — do not modify code, delete anything, or write files. Route accepted cuts through `plan-implementation`.
