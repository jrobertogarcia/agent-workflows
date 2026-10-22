---
name: triage-feedback
description: Triage a batch of findings on this repo's skills into the GitHub issue backlog, one fresh read-only subagent per finding, writing only after the maintainer approves a preview. Maintainer-only; use when the maintainer pastes findings to triage.
---

# Triage Feedback

1. **Load**: Read the findings pasted in the invocation, the open issues (`gh issue list --state open --json number,title,body,labels`), the pinned index #50, and the private note `~/.agent-workflows/agent-workflows/orchestrate-remediation.md`.
2. **Triage Each Finding**: Dispatch one fresh mid-tier subagent per finding, in parallel, giving each the finding and the full open-issue list. Subagents are read-only: no `gh` writes, no repo or note edits. Each finds evidence in `~/.claude/projects/*/*.jsonl` and `~/.agent-workflows/` (it returns pointers, not contents) and the root cause in the affected skill's spec, then returns:
   - **extend #N** (duplicates land here), **new**, or **no change** (already resolved or not justified, with the reason);
   - `observed` or `speculative`, and an existing `theme:*` label, a proposed new one, or none;
   - the proposed title and body, per the Backlog Rules.
3. **Preview and Stop**: Run the step 5 private-term grep on the drafted titles and bodies and fix every hit. Show every write in one list: issue edits, new issues, the new #50 list, and note lines. Wait for the maintainer's approval. A new `theme:*` label needs its own explicit approval, and its position in #50 is proposed here.
4. **Apply**: Only this thread writes. Create any approved new label first. Edit issue bodies in place with current truth only, and post no comments. Create the new issues. Rewrite #50's list in place, keeping its preamble, and place each new issue under its theme (or Unthemed) with `observed` before `speculative`. In the private note's evidence map, add or rewrite one line per touched issue as `- #N <title>: <date span>; <paths>`. If any write fails, stop, report exactly what was written, and do not retry.
5. **Verify**:
   - Read back every edited or created issue and #50.
   - Grep all open titles and bodies for private terms, which must find 0. The terms are ticket keys, internal repo names, private PR numbers, company-internal skill names, `~/` paths and transcript UUIDs; take the concrete patterns from the private note.
   - Check that every open labelled issue appears exactly once in #50.
6. **Report**: At most ~15 lines: each finding's outcome with issue links, the verify results, and anything left undone.

## Backlog Rules

- Title: `<skill>: <symptom>`.
- Body: **Evidence:**, **Symptom:**, **Root cause:** and **Done when:** lines, then an optional **Prior art:** line and an optional `## Design` section.
- Labels: exactly one of `observed` or `speculative`, plus at most one `theme:*`.
- Nothing private in the public repo: evidence there says "private repo; details in local note", and the pointers go in the note.
