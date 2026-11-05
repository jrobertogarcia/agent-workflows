---
name: triage-feedback
description: Triage feedback on this project's skills into its GitHub issue backlog, checking each finding read-only against existing issues and writing only after the user approves a preview. Use when you have findings, bugs, or suggestions about these skills to report.
---

# Triage Feedback

Target `jrobertogarcia/agent-workflows` (`<target>`): pass `-R <target>` to every `gh issue`, `gh label` and `gh pr` call; `gh repo view` takes `<target>` positionally and `gh auth status` takes neither. Never use the current directory's repository or a fork.

1. **Preflight**: Run `gh auth status --hostname github.com`; if it fails, stop and tell the user to run `gh auth login`. Read `gh repo view <target> --json viewerPermission`: `ADMIN`, `MAINTAIN` or `WRITE` gets the full flow; anyone else gets contributor mode, which only creates new issues.
2. **Load**: Read the findings pasted in the invocation, every issue (`gh issue list -R <target> --state all --limit 500 --json number,title,body,labels,state`) and the labels (`gh label list -R <target> --limit 500`). Read the private note `~/.agent-workflows/agent-workflows/orchestrate-remediation.md` only if it exists.
3. **Triage Each Finding**: Dispatch one fresh mid-tier subagent per finding where the host supports subagents, in parallel, giving each the finding, the issue list and the labels; otherwise process findings one at a time in this thread. Triage is read-only either way: only Apply writes. Evidence is the finding itself plus, where present, the host's local session logs (e.g. `~/.claude/projects` on Claude Code) and `~/.agent-workflows/`, cited as pointers rather than contents; the root cause comes from the affected skill's spec. Each returns:
   - **extend #N** (an open duplicate), **new**, or **no change** (a closed issue already resolved it, or it is not justified), with the reason;
   - `observed` only when the finding reports a real run, else `speculative`; and an existing `theme:*` label, a proposed new one, or none;
   - the proposed title and body, per the Backlog Rules.
4. **Private Terms**: Take the patterns from the note when it exists. Otherwise propose candidates (ticket-key patterns seen in the findings, org and repo names from local git remotes, `~/` paths, UUIDs) and have the user confirm or edit the list. Grep every draft bound for `<target>` and fix each hit; the private note is exempt.
5. **Preview and Stop**: Show every write in one list and wait for the user's approval.
   - Full flow: issue edits, new issues, and note lines. A new `theme:*` label needs its own approval.
   - Contributor mode: new issues only, created without `--label`; the proposed labels and theme are stated in the body instead. For **extend** or **no change**, show the existing issue's link and file nothing.
6. **Apply**: Only this thread writes, with `gh label create -R <target> <name>`, `gh issue edit -R <target> <N> --body-file <file>` and `gh issue create -R <target> --title <title> --body-file <file>`, adding one `--label` per label in the full flow only. Before each write, re-read the issue it touches; if it changed since Load, stop.
   - Full flow: create any approved label first; edit issue bodies in place with current truth only, and post no comments; create the new issues; if the note exists, add or rewrite one evidence-map line per touched issue as `- #N <title>: <date span>; <paths>`.
   - Contributor mode: create each new issue with no `--label` flag, since it fails or is ignored without write access.
   - If any write fails, stop, report exactly what was written, and do not retry.
7. **Verify**: Read back every issue written. Grep what this run wrote to `<target>` for the private terms, which must find 0.
8. **Report**: At most ~15 lines: each finding's outcome with issue links, the verify results, and anything left undone.

## Backlog Rules

- Title: `<skill>: <symptom>`.
- Body: **Evidence:**, **Symptom:**, **Root cause:** and **Done when:** lines, then an optional **Prior art:** line and an optional `## Design` section. Evidence is one sentence (when, where, what happened); Symptom says what goes wrong without repeating Evidence.
- Labels: exactly one of `observed` or `speculative`, plus at most one `theme:*`.
- Nothing private in the public repo. Write "private repo; details in local note" only when the note holds those details; otherwise describe the evidence generically.
