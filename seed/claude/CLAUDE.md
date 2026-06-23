<!-- CODEGRAPH_START -->
## CodeGraph

CodeGraph builds a semantic knowledge graph of codebases for faster, smarter code exploration.

### If `.codegraph/` exists in the project

**NEVER call `codegraph_explore` or `codegraph_context` directly in the main session.** These tools return large amounts of source code that fills up main session context. Instead, ALWAYS spawn an Explore agent for any exploration question (e.g., "how does X work?", "explain the Y system", "where is Z implemented?").

**When spawning Explore agents**, include this instruction in the prompt:

> This project has CodeGraph initialized (.codegraph/ exists). Use `codegraph_explore` as your PRIMARY tool — it returns full source code sections from all relevant files in one call.
>
> **Rules:**
> 1. Follow the explore call budget in the `codegraph_explore` tool description — it scales automatically based on project size.
> 2. Do NOT re-read files that codegraph_explore already returned source code for. The source sections are complete and authoritative.
> 3. Only fall back to grep/glob/read for files listed under "Additional relevant files" if you need more detail, or if codegraph returned no results.

**The main session may only use these lightweight tools directly** (for targeted lookups before making edits, not for exploration):

| Tool | Use For |
|------|---------|
| `codegraph_search` | Find symbols by name |
| `codegraph_callers` / `codegraph_callees` | Trace call flow |
| `codegraph_impact` | Check what's affected before editing |
| `codegraph_node` | Get a single symbol's details |

### If `.codegraph/` does NOT exist

At the start of a session, ask the user if they'd like to initialize CodeGraph:

"I notice this project doesn't have CodeGraph initialized. Would you like me to run `codegraph init -i` to build a code knowledge graph?"
<!-- CODEGRAPH_END -->

## Rule 1 — Think Before Coding
**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

**Confusion Protocol:** The moment you detect ambiguity on a non-trivial or architectural decision, halt. Do not pick one interpretation and proceed. State each viable interpretation, the tradeoff between them, and your recommendation, then wait for the user to choose. Guessing on a decision that is expensive to reverse is the failure mode this prevents.

## Rule 2 — Simplicity First
**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## Rule 3 — Surgical Changes
**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## Rule 4 — Goal-Driven Execution
**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

## Rule 5 — Token budgets are not advisory
Per-task: 4,000 tokens. Per-session: 30,000 tokens.
If approaching budget, summarize and start fresh. Surface the breach.

## Rule 6 — Read before you write
Before adding code, read exports, immediate callers, shared utilities.
If unsure why code is structured a certain way, ask.

## Rule 7 — Checkpoint after every significant step
Summarize what was done, what's verified, what's left.
Don't continue from a state you can't describe back. Stop and restate.

## Rule 8 — Fail loud
"Completed" is wrong if anything was skipped silently.
"Tests pass" is wrong if any were skipped.
Default to surfacing uncertainty, not hiding it.

## Rule 9 — Revise additively, never from scratch
When revising an already-approved plan or document, pass the full prior content as the baseline.
Apply the targeted fix as an addition; preserve every previously-correct section. Never rewrite from scratch and drop what was already right.

## Text

Rules for human-readable text you produce (PR descriptions, comments, docstrings, commit messages, docs):

- No em-dashes or other long dashes. Use commas, periods, or parentheses instead.
- Cut filler and hedging: "um", "basically", "essentially", "it's worth noting", "of course".
- Vary sentence length. Do not pad a short, correct statement into a long fuzzy one, and do not chain choppy fragments either.
- Avoid the usual LLM tells: no "it's not just X, it's Y", no "delve", no overwrought openers.
- Reread what you wrote before you finish. Delete anything that does not earn its place.

@RTK.md