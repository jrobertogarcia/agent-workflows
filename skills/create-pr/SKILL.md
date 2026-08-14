---
name: create-pr
description: Push the current branch and open a pull request with a synthesized title and description. Use when a reviewed branch is ready to submit.
model: sonnet
effort: medium
---

# Create Pull Request

## Execution

1. **Read the Diff**: Read the branch diff against its base integration branch. Reuse handover or review context already gathered in this thread rather than re-reading it.
2. **Draft the Title**: Match the title convention of recent merged pull requests in the repository, defaulting to Conventional Commits (e.g. `feat(auth): implement user authentication`) when none is established.
3. **Write the Body**: Write for a busy reviewer: short, plain, specific. Every body carries this content:
   ```markdown
   ## Why
   <the problem or dependency, in 1-2 sentences>

   ## What
   <one bullet per meaningful change, one clause each>

   ## Tested
   <only when verification is non-obvious from the diff>
   ```
   - **No PR template**: use those headings exactly.
   - **PR template exists** (e.g. `.github/pull_request_template.md`): its sections are the skeleton, so drop those headings and write the same content into it. Put Why and What in the free-form narrative section (`## Description`, `## Summary`, or similar), or split them across sections that already map to them (e.g. `## Motivation` and `## Changes`). When the template has no narrative section at all, put Why and What above its first heading. Add no headings beyond the template, fill its metadata fields (e.g. ticket links) from context, and leave checklist items unchecked unless you verified them yourself. Skip Tested when a checklist item already covers verification.
   - Leave out shell commands, merge instructions, and test inventories.
   - Compose the body into a temp file outside the repository.
4. **Check Before Creating**: Re-read the drafted body. Confirm Why and What are both covered, the headings match the template when one exists and the schema when it does not, and nothing was added beyond them.
5. **Push & Create**: Push the active branch to origin and open the pull request using the drafted body file.
   ```bash
   git push origin HEAD && gh pr create --title "<TITLE>" --body-file <body-file> --base <default-branch>
   ```
6. **Verify Creation**: Verify the pull request on the hosting platform (e.g. `gh pr view --web`).
7. **Release the Worktree**: When the working directory is a linked worktree (`git rev-parse --git-dir` and `git rev-parse --git-common-dir` return different paths), run `git checkout --detach` so the pushed branch can be checked out elsewhere for review. This preserves the directory and its ignored and uncommitted files. Report the reattach command (`git checkout <branch>`). Skip in a normal checkout.
8. **Preserve Workspace**: Keep unrelated files and existing worktrees intact.
