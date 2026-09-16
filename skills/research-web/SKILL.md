---
name: research-web
description: Research current best practices and trade-offs from authoritative sources. Use when a decision needs external evidence.
---

# Web Research

1. **Scope the Question**: Establish which decision the research must inform. Ask if it is ambiguous.
2. **Pin the Versions**: Read the project's manifest or lockfile, and tie every version-dependent recommendation to the versions actually in use. Say so when there is none.
3. **Search the Hierarchy**: Prefer specifications, official documentation, and source code, then maintainer writing (release notes, issues, design discussions), then reputable secondary sources, then blogs and forum answers. Record each source's date and flag it when it is old for the topic.
4. **Report**: Cite every claim with its source link. Cover the trade-offs and failure modes, not just the recommended option. Surface disagreement between sources along with your weighting, rather than silently picking a winner. Name any question you could not answer, then close with actionable next steps.
5. **No Code / No Plan**: Do not modify code or draft implementation plans during the research phase. Create a file only when requested.
