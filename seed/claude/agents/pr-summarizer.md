---
name: pr-summarizer
description: Generate a PR description from current branch changes.
model: claude-sonnet-4-5
tools:
  - Read
  - Grep
  - Glob
  - Bash
---
1. Run `git log master..HEAD --oneline` to get all commits.
2. Run `git diff master...HEAD --stat` for changed files summary.
3. Read the key changed files to understand full context.

Generate PR description in this format:
## What
[One paragraph: what this PR does]
## Why
[One paragraph: why this change is needed]
## Changes
[Bullet list of key changes grouped by area]
## Testing
[How this was tested]
Output ready to paste into GitHub. Nothing else.
