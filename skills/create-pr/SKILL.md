---
name: create-pr
description: Push the current branch and open a pull request with a synthesized title and description. Use when a reviewed branch is ready to submit.
model: sonnet
effort: medium
---

# Create Pull Request

## Description Structure
Write for a busy reviewer: short, plain, specific. Only as long as the change needs.
- **Why**: the problem or dependency, in one or two sentences.
- **What**: what the PR does, as prose or bullets sized to the diff.
- **Tested**: only when verification is non-obvious. Omit when the diff or the template checklist already covers it.

Follow the repository's PR template when one exists (e.g. `.github/pull_request_template.md`) and add no sections beyond it. Leave checklist items unchecked unless you verified them yourself. Omit restatements of the diff, test inventories, shell commands, and merge instructions.

## Execution
1. **Read the Diff**: Read the branch diff against its base integration branch. Reuse handover or review context already gathered in this thread rather than re-reading it.
2. **Synthesize Metadata**: Draft the title and body following the structure above. Match the title convention of recent merged pull requests in the repository, defaulting to Conventional Commits (e.g. `feat(auth): implement user authentication`) when none is established.
3. **Push & Create**: Push the active branch to origin and open the pull request against the base integration branch, using the platform CLI or web interface (e.g. `git push origin HEAD && gh pr create --title "[TITLE]" --body "[BODY]" --base <default-branch>`).
4. **Verify Creation**: Verify the pull request on the hosting platform (e.g. `gh pr view --web`).
5. **Preserve Workspace**: Do not clean up unrelated files.
