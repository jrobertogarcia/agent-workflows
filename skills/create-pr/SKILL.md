---
name: create-pr
description: Lean PR Creator with AI Metadata Synthesis and Automatic Push to Origin
---

# Create Pull Request

1. **Synthesize PR Metadata**: Synthesize accurate PR metadata from the branch diff and formulate a professional title following Conventional Commits (e.g., `feat(auth): implement user authentication`), adhering to standard English.
2. **Push & Create**: Push the active branch to origin and initiate the Pull Request targeting the base integration branch (e.g., `main` or `master`).
   * Run the appropriate git and platform-specific CLI command or submit via the web interface.
   * Example (GitHub CLI):
     ```bash
     git push origin HEAD && gh pr create --title "[TITLE]" --body "[BODY]" --base <default-branch>
     ```
3. **Verify Creation**: Verify PR creation on your VCS hosting platform.
   * Example (GitHub CLI):
     ```bash
     gh pr view --web
     ```
4. **Preserve Workspace**: Do not clean up unrelated files.
