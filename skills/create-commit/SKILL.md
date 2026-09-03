---
name: create-commit
description: Stage the in-scope changes and commit them with a message matching the repository's convention. Use after a logical piece of work is complete and verified.
---

# Create Commit

1. **Read the Convention**: Inspect recent commits (`git log`) to infer the repository's message convention: prefix style, scope usage, and whether bodies and trailers are customary. Default to Conventional Commits (e.g. `feat(auth): add session refresh`) when none is established.
2. **Scope the Change**: Review the working tree and stage only the files belonging to this logical piece. Leave unrelated modifications unstaged rather than sweeping them in, and name what you deliberately left out.
3. **Write the Message**: Follow the detected convention. Describe the outcome, not the process, and do not reference the task or conversation that produced the change.
4. **Commit and Read Back**: Commit, then confirm the message and the file list are what you intended.
   ```bash
   git commit -m "<message>" && git log -1 --stat
   ```
5. **One Piece Per Commit**: When the working tree holds more than one logical change, commit them in sequence rather than together. Do not stage everything and split it afterward.
