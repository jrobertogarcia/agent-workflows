---
name: create-pr
description: Push the current branch and open a pull request with a synthesized title and description. Use when a reviewed branch is ready to submit.
---

# Create Pull Request

## Execution

Takes an optional base branch, any related pull request URLs (e.g. a parent pull request), an optional keep-checkout flag, and an optional draft-only flag.

1. **Read the Diff**: Read the branch diff against the given base, else the repository's default branch. Read the handover at `~/.agent-workflows/<repo>/<branch>/handover.md` when it exists, where `<repo>` is `basename(dirname(git rev-parse --path-format=absolute --git-common-dir))` and `<branch>` is `git branch --show-current`. Treat it as the implementer's self-report.
   - Its `Branch tip:` SHA must prefix-match `git rev-parse HEAD`. Treat a mismatch or a missing line as stale and discard its verification claims.
   - Reuse context already gathered in this thread rather than re-reading it.
2. **Read Conventions & Draft the Title**: Read your recent merged pull requests:
   ```bash
   gh pr list --state merged --author @me --limit 5 --json title,body
   ```
   If that returns none, run it again without `--author @me`; if still none, no convention is established. Match their title convention, defaulting to Conventional Commits (e.g. `feat(auth): implement user authentication`) when none is established. Use the same pull requests for the body's tone and link wording in step 3, never for its headings, bullet count or length.
3. **Write the Body**: Write for a busy reviewer: short, plain, specific. Every body carries this content:
   ```markdown
   ## Why
   <the problem or dependency, in 1-2 sentences>

   ## What
   <at most 6 bullets, one per reviewer-visible change>

   ## Tested
   <only when verification is non-obvious from the diff>
   ```
   - **What bound**: at most 6 top-level bullets, each one sentence on one line of at most 160 characters, with no nested bullets and no other lines under What. Group rule-level edits under the one reviewer-visible change they serve. The bound also holds inside a PR template's narrative section.
   - **No PR template**: use the skeleton's headings exactly.
   - **PR template exists** anywhere in the repository (e.g. `.github/pull_request_template.md` or `docs/pull_request_template.md`): its sections are the skeleton, so drop those headings and write the same content into it. Put Why and What in the free-form narrative section (`## Description`, `## Summary`, or similar), or split them across sections that already map to them (e.g. `## Motivation` and `## Changes`). When the template has no narrative section at all, put Why and What above its first heading. Add no headings beyond the template, fill its metadata fields (e.g. ticket links) from context, and leave checklist items unchecked unless you verified them yourself. Skip Tested when a checklist item already covers verification.
   - **Links**: Build one link list from the handover's `Links` section and the related pull request URLs you were given, and include every link on it. The step 2 pull requests decide only how links are worded and which kinds (ticket, spec, issue, parent pull request) to expect; name each expected kind that has no link in your report. Without a PR template, put the link lines last, as one block after the last section and a blank line: plain lines with one link each, no bullet markers and no label-only lines (e.g. `Closes #56` or `Refs https://…`). Never invent a link and never put a placeholder for a missing one in the body.
   - **Process vocabulary**: Write about the change, not how it was produced. Leave out terms from your own process: approval gates, step names or ids, numbered questions or rulings, state or evidence file names, and references to "the author".
   - **Deviations and pending verification**: State a deviation from the requirement, or a check not yet run, plainly when the handover records one.
   - Leave out shell commands, merge instructions, and test inventories.
   - Compose the body into a temp file outside the repository.
4. **Check Before Creating**: Re-read the drafted title and body and fix them in place:
   - every step 3 rule holds, and nothing is added beyond the skeleton;
   - What passes the bound: at most 6 top-level bullets, none nested, each one sentence on one line of at most 160 characters; fix a failure by merging or cutting bullets, never by wrapping lines;
   - without a PR template, the trailing link block is plain lines with one link each, none starting with `- ` or `* `, and none label-only;
   - every claim about what changed matches the diff;
   - every claim about verification is backed by the handover's evidence, and only when the handover is not stale;
   - the Why matches the requirement or handover.

   Cut or correct each failing sentence, and state a verification claim you cannot confirm as unverified.

   When draft-only is requested, stop here. Push nothing, then report the title, the body, and any missing link kinds.
5. **Push & Create**: When a base is given, confirm it exists on origin (`git ls-remote --exit-code --heads origin <base>`) and stop if it does not. Push the active branch to origin and open the pull request using the drafted body file, passing `--base <base>` only when a base is given; otherwise omit it.
   ```bash
   git push origin HEAD && gh pr create --title "<TITLE>" --body-file <body-file> [--base <base>]
   ```
6. **Verify Creation**: Read the PR back with `gh pr view --json url,baseRefName` and report its URL. When a base was given, stop and report if `baseRefName` differs.
7. **Release the Worktree**: Skip when keep-checkout is requested. When the working directory is a linked worktree (`git rev-parse --git-dir` and `git rev-parse --git-common-dir` return different paths), run `git checkout --detach` so the pushed branch can be checked out elsewhere for review. This preserves the directory and its ignored and uncommitted files. Report the reattach command (`git checkout <branch>`). Skip in a normal checkout.
8. **Preserve Workspace**: Keep unrelated files and existing worktrees intact.
