---
description: Delete local git branches whose remote tracking branch is gone (merged/deleted upstream). Lists first, confirms, never force-deletes.
argument-hint: "[--current-repo-only] (default: just this repo)"
---

# Clean up stale local branches

Delete local branches that no longer exist on the remote — safely.

## Steps

1. Run `git fetch --prune` so remote-tracking refs are current.
2. List candidates: branches whose upstream is `[gone]`.
   ```
   git for-each-ref --format '%(refname:short) %(upstream:track)' refs/heads | grep '\[gone\]'
   ```
3. Exclude the current branch and any protected branch (`main`, `master`, `develop`).
4. Show the candidate list to the user and ask:
   **"Delete these N stale branches? (yes / pick / no)"**
   - "pick" → let the user name which to keep.
   - STOP and wait.
5. On confirmation, delete with `git branch -d` (safe — refuses unmerged).
   - If `-d` refuses a branch because it's unmerged, do **not** silently `-D`.
     List the unmerged ones separately and ask explicitly before any `-D`.
6. Report what was deleted and what was skipped.

## Rules
- Never `-D` (force) without a separate explicit confirmation per the unmerged list.
- Never delete the current branch or a protected branch.
- ponytail: pure git plumbing, no script needed — run the commands inline.
