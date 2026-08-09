---
name: gather-context
description: Gather and organize context for a given file, folder, or component before planning or coding. Use when starting work on unfamiliar code.
---

# Gather Context

1. **Target**: Establish the file, folder, or component in scope. Ask if it is ambiguous.
2. **Read**: Read the target in full, then whatever it references and whatever references it (e.g. imports, callers, configs, schemas, tests, docs).
3. **Expand Only As Needed**: Go one hop further only where it is required to understand the target. Note what you skipped rather than crawling the full graph.
4. **Report**: Output an organized summary in the response. Do not analyze, evaluate, suggest, plan, modify code, or write files.
