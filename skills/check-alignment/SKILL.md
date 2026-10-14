---
name: check-alignment
description: Verify the actual diff against the agreed plan and the project's standards, and report ALIGNED or GAPS without editing. Use after implementing a change and before review.
---

# Check Alignment

One read-only pass over the actual diff, never a self-reported summary of what changed. Do not modify code or the plan.

Takes an optional plan and an optional phase start commit.

1. **Locate the Plan**: Use the plan given, else `~/.agent-workflows/<repo>/<branch>/plan.md`, where `<repo>` is `basename(dirname(git rev-parse --path-format=absolute --git-common-dir))` and `<branch>` is `git branch --show-current`. Stop and say so when `git branch --show-current` is empty. Ask first when the plan is absent; skip Plan Fidelity, and say so, only when told there is no plan.
2. **Scope**: Audit the changes the plan covers: by default the branch diff against its target plus uncommitted changes; when the plan covers only the current phase of a longer branch, only the changes made since the phase start commit. Ask for that commit when it is unclear.
3. **Plan Fidelity**:
   - **Scope**: Do the changes match the agreed scope, adding nothing and dropping nothing?
   - **Logic**: Does the implementation follow the planned design?
   - **Tests**: Did the planned verification run and pass? Confirm from its output rather than a claim that it ran, and run it yourself when no output exists. Report the command and result, or say the plan named no verification.
4. **Standards**: Identify the guidelines, design standards, and requirements that govern the changed files, reusing those already read in this thread. Verify the changed code against them. Name any standard you could not evaluate rather than assuming a pass.
5. **Conflicts**: When the plan and a standard disagree, report both and the point of conflict. Do not resolve it.
6. **Report**: Present Plan Fidelity and Standards as two sections, each gap with file and line evidence, and any conflicts in their own subsection. End with `ALIGNED` when neither section has a gap or conflict, else `GAPS`. Conflicts make `GAPS`. List unevaluated standards, a skipped Plan Fidelity, and verification that did not run as caveats under the verdict line; they do not by themselves make `GAPS`.
