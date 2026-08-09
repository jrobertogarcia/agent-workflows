---
name: create-branch
description: Check out the latest default branch and create a new feature branch using Conventional Commits. Use when starting new work.
---

# Create Feature Branch

1. **Update Default Branch**: Ensure you are on the latest state of the main development trunk branch (e.g., `main` or `master`).
   ```bash
   git checkout <default-branch> && git pull
   ```

2. **Branch Naming**: Based on the context of the current conversation, determine a branch name that follows Conventional Commits naming conventions (e.g., `feat/<name>`, `fix/<name>`, `chore/<name>`, `refactor/<name>`).

3. **Branch Creation**: Create and switch to the new feature branch locally.
   ```bash
   git checkout -b <branch-name>
   ```
