---
name: research-web
description: Research current best practices and trade-offs from authoritative sources. Use when a decision needs external evidence.
---

# Web Research

1. **Scope the Question**: Establish which decision the research must inform. Ask if it is ambiguous, and say so and stop if no web search or fetch tool is available.
2. **Pin the Versions**: Read the project's manifest or lockfile and tie every recommendation to the versions actually in use.
3. **Search the Hierarchy**: Prefer specifications, official documentation, and source code, then maintainer writing (release notes, issues, design discussions), then reputable secondary sources, then blogs and forum answers. Record each source's publication or version date, and flag when the best available source is old relative to how fast the topic moves.
4. **Resolve Conflicts**: When sources disagree, say so and state which one you weight more and why. Do not silently pick a winner.
5. **Report**: Cite every claim with its source link. Cover the trade-offs and failure modes, not just the recommended option. Name any question you could not answer rather than implying it was settled.
6. **Recommend**: Conclude with actionable next steps tied to this project's versions and constraints.
7. **No Code / No Plan**: Do not modify code or draft implementation plans during the research phase. Create a file only when requested.
