---
description: Generate three distinct approaches to a problem from different angles before committing to one.
argument-hint: <the decision or problem to explore>
---

# Three approaches, different angles

For the following problem, produce **three genuinely distinct** approaches —
not three flavors of the same idea.

**Problem:** $ARGUMENTS

## Output

Present exactly three options, each optimizing for a different priority:

1. **Fastest to ship** — minimum viable, what unblocks today.
2. **Most maintainable** — what a senior would keep for years.
3. **Most robust / performant** — what survives scale or hostile input.

For each, give in 3-5 lines:
- The core idea.
- The main trade-off (what you give up to get its strength).
- When it's the right call.

## Then
- End with a one-line recommendation for *this* situation and why.
- STOP. Do not implement until the user picks an option.

## Rules
- The three must differ in approach, not just in wording. If two collapse into
  the same design, replace one.
- No essays — keep each option tight.
