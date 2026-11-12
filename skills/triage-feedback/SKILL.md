---
name: triage-feedback
description: File feedback on this project's skills as GitHub issues, recording what the reporter saw without diagnosing it or proposing fixes, and linking matching issues instead of filing duplicates. Writes only after the user approves a preview. Use when you have findings, bugs, or suggestions about these skills to report.
---

# Triage Feedback

Record feedback faithfully; don't analyze it. Never add a root cause, a fix, a design, acceptance criteria, or a judgment of whether it is worth filing. A fix the reporter suggested stays in their words.

Target `jrobertogarcia/agent-workflows` (`<target>`): pass `-R <target>` to every `gh issue` call, never the current repository or a fork.

1. **Clarify**: Split the feedback into findings, one problem or suggestion each, merging any that describe the same thing. If a finding doesn't say which skill it concerns or what was expected, ask the user rather than guess.
2. **Match**: Search each finding against open and closed issues with `gh issue list -R <target> --state all --search "<keywords>" --json number,title,state,url`. A match is the same problem in the same skill, not just the same area; when unsure, treat it as no match.
3. **Draft**: A finding with no match gets a new issue:
   - Title: `<skill>: <what goes wrong>`.
   - **What happened:** what the reporter saw and when, or that it comes from reading the skill rather than a run.
   - **Expected:** what they expected or want instead, in their words.

   A match gets a short comment for the user to post: what they saw and when, noting it recurred if the issue is closed. Strip anything private from every draft: local paths, internal repository, organization or ticket names, people, and private links.
4. **Preview and Stop**: Show every draft in one list, with each match's link, and wait for the user's approval.
5. **File**: Create each approved issue with `gh issue create -R <target> --title <title> --body-file <file>`. Never comment on, edit, label or close an issue. If a write fails, stop and report what was filed; don't retry. End with each finding's link, and each comment ready to paste.
