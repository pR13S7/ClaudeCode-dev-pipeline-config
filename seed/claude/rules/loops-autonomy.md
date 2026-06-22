Loops & autonomy rules:
- Always work on a git branch so changes can be reverted. Never start an autonomous loop without an iteration cap.
- Loops are only for work with programmatic verification (tests, lint, type checks, build). Do not loop on judgment-heavy work, design decisions, or long compute jobs — those are a script or the user's call, not a loop.
- State the stop condition in the transcript (show the passing run), not as a silent file assertion. "Done" must be demonstrable, not asserted.
- If a task has no programmatic check, say so before starting rather than looping with no stop condition.
- Prefer the autonomy commands over asking the user to type "continue": `/loop` for polling or repeating a check, `/pipeline` for plan → verify → implement → verify, `/test-green` for driving tests to green.
- When the cap is reached and you are still stuck: stop. Document what is blocking, what you tried, and suggested next steps. Do not thrash.
