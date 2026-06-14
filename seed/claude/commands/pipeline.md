---
description: Run the full plan → verify-plan → implement → verify-implementation pipeline, pausing for approval at every step.
argument-hint: <describe the task to accomplish>
---

# Automated Build Pipeline

You are orchestrating a 4-stage pipeline for the following task:

**Task:** $ARGUMENTS

Run the stages strictly in order. **After every stage you MUST stop and ask
the user to confirm before continuing.** Do not start the next stage until the
user explicitly replies with "proceed" (or "yes"/"continue"). If the user gives
feedback instead, incorporate it and re-run the current stage, then ask again.

Delegate the heavy lifting to subagents at every stage — not only for review
quality, but to keep *your own* (the orchestrator's) context window lean so you
stay coherent across a long multi-stage run.

---

## Stage 0 — Survey the codebase (skip for trivial tasks)
- For any non-trivial task, dispatch one or more `Explore` subagents (in parallel)
  to produce a short, plain-English architecture summary of the areas the task
  touches: key files, existing patterns/utilities to reuse, and likely blast radius.
- For a trivial, well-scoped change (typo, one-line fix, rename), skip this stage.
- Pass the summary into the Stage 1 `planner` prompt so the plan is grounded
  without the planner having to re-explore from scratch.
- This is read-only; no approval gate. Proceed directly to Stage 1.

## Stage 1 — Write the plan
- Delegate to the `planner` subagent to produce a detailed implementation plan
  for the task above.
- Show the full plan to the user verbatim.
- Then ask: **"✅ Stage 1 (Plan) complete. Proceed to plan review? (proceed / give feedback)"**
- STOP and wait for the user's reply.

## Stage 2 — Verify the plan
- Delegate to the `plan-reviewer` subagent, passing it the approved plan from Stage 1.
- Show the review (BLOCKERS / WARNINGS / SUGGESTIONS) and its `VERDICT:` line.
- If the verdict is "NEEDS REVISION", send the required changes back to the
  `planner`, regenerate the plan, and re-review. Repeat this revise→re-review
  cycle **at most 3 times**.
- If it still reads "NEEDS REVISION" after the third revision, STOP. Surface the
  outstanding blockers and ask: **"⚠️ Stage 2 did not converge after 3 revisions.
  How do you want to proceed? (give feedback / simplify scope / abort)"** and wait.
- Once it reads "VERDICT: APPROVED", ask: **"✅ Stage 2 (Plan Review) complete — verdict: <verdict>. Proceed to implementation? (proceed / give feedback)"**
- STOP and wait for the user's reply.

## Stage 3 — Implement the plan
- Delegate to the `implementer` subagent, passing it the APPROVED plan.
- Show a file-by-file summary of what changed and any deviations.
- Then ask: **"✅ Stage 3 (Implementation) complete. Proceed to verification? (proceed / give feedback)"**
- STOP and wait for the user's reply.

## Stage 4 — Verify the implementation
- Delegate to the `impl-reviewer` subagent, passing it the approved plan and
  letting it run `git diff` plus any tests/build/lint.
- Show its findings (CRITICAL / WARNINGS / SUGGESTIONS) and its `VERDICT:` line.
- If the verdict is "FAIL":
  - For **localized fixes** (a missed step, a small correctness/quality issue),
    send the required fixes back to the `implementer` to patch in place.
  - For **structural/architectural** findings (the chosen approach is the
    problem, not its execution), route back to the `planner` to re-plan with the
    reviewer's diagnostics, then re-implement from the revised plan — rather than
    patching a flawed structure ("scrap it and implement the elegant solution").
  - Re-verify after either path. Repeat this fix→re-verify cycle **at most twice**.
- If it still reads "FAIL" after the second retry, STOP. Do not finalize. Surface
  the outstanding findings and ask: **"⚠️ Stage 4 did not converge after 2 retries.
  How do you want to proceed? (give feedback / revise plan / abort)"** and wait.
- Once it reads "VERDICT: PASS", show the findings and ask:
  **"✅ Stage 4 (Verification) complete — verdict: PASS. Finalize? (proceed / give feedback)"**
- STOP and wait for the user's reply before finalizing.

## Stage 5 — Finalize & capture learnings (after the user approves)
1. **Dead-code sweep (offered):** Offer to run the `dead-code` subagent over the
   diff to catch orphaned code or duplication introduced this run
   — **"Run a dead-code/duplication pass over the changes? (yes / skip)"**.
   Run it only if the user accepts; surface its findings, don't auto-delete.
2. **Self-improvement:** Review the corrections raised by `plan-reviewer` and
   `impl-reviewer` this run. If any reflect a *generalizable* mistake class (not a
   one-off), propose a single concise rule and offer to persist it — either to
   `CLAUDE.md` or as a `feedback`-type memory file per the memory system. **Ask
   before writing; never edit `CLAUDE.md`/memory without explicit approval.**
3. Report: **"🎉 Pipeline complete. Summary of all changes: ..."**

---

## Rules
- Never skip a stage or an approval gate.
- Always pass the relevant context (plan, review feedback, diff) to the next subagent.
- If any subagent reports it is BLOCKED, stop the pipeline and surface the blocker to the user.
- Keep your own commentary brief; let each subagent's output speak for itself.
