---
name: resolve-open-items
description: Research each open item (a question, conflict, review finding, or PR comment) from the available sources and return what it settled with evidence and the few decisions that need you. Use when a story review, plan, alignment check, or review leaves open items, before asking the human.
---

# Resolve Open Items

Read-only: never edit code and never post. Any outward-facing text, such as a reply to a PR comment, is a draft for the human.

1. **Take the Items**: The input is numbered items, each with a kind (question, conflict, finding, or PR comment), plus paths to their context. Number any unnumbered item and infer a missing kind. With no items, say so and stop. Write the report to the path the caller gives; else to `~/.agent-workflows/<repo>/<branch>/resolve-open-items.md`, where `<repo>` is `basename(dirname(git rev-parse --path-format=absolute --git-common-dir))` and `<branch>` is `git branch --show-current`; or to no file when the caller asks for the report to be returned.
2. **Group Coupled Items**: Put items whose answers depend on each other, or that settle the same decision, into one group. Separate researchers on coupled items contradict each other.
3. **Dispatch Researchers**: Where the host supports subagents, dispatch one fresh subagent per item or group, in parallel. Use the mid tier (e.g. Sonnet) by default and the top tier (e.g. Opus) for architecture questions, Critical or Important findings, and groups; never the cheapest tier. Without subagents, research the items one at a time in this thread.
4. **Research Brief** (what each researcher gets):
   - Answer from reachable sources first: code, code search across repos, the tech spec, docs, tickets, chat, and `research-web` for external evidence.
   - Report each source as checked, unavailable, or not relevant.
   - Verify a cross-repo claim by code search; never assume it.
   - Check any claim the item makes, a human's correction included, against the source before accepting it.
   - Stay read-only, never post, and stay within the item's scope.
5. **Per-Item Result** (about 250 words at most):
   - **Verdict**: ANSWERED, with evidence; RECOMMEND, giving the simplest working option and the alternatives considered; or NEEDS-DECISION, giving who decides, the exact question, the options, and a recommended option.
   - Reserve NEEDS-DECISION for product or policy choices, another team's call, or evidence still conflicting after research.
   - Tag each piece of evidence VERIFIED or INFERRED with its location, and state a confidence.
   - For a finding, recommend fix, defer, or discuss.
   - When a plan is among the inputs, mark `(changes plan)` each item whose answer or recommended option differs from what the plan states or assumes.
6. **Synthesize**: Cross-check the results for contradictions; re-research a contradiction once, or make it NEEDS-DECISION. Rank NEEDS-DECISION items by impact times uncertainty and keep about 5 at most under Needs you. The rest go under Settled, marked deferred, where the human can override them; none is dropped. Write the full per-item reports to the report path.
7. **Report**:
   - **Settled**: one line per item: its number, verdict, and answer or option, plus `deferred` where it applies.
   - **Needs you**: each item's exact question, who decides, the options, and the recommended option.
   - Then the report path.
   - The caller proceeds on RECOMMEND and deferred items and lists them under Settled at its next gate; only Needs you stops a run.
