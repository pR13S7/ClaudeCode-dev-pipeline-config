---
description: Run tests with coverage, then loop fixing failures and coverage gaps until all thresholds pass.
argument-hint: "[test command, e.g. 'npm test'] (auto-detected if omitted)"
---

# Drive tests to green

Run the test suite with coverage and iterate until it passes.

**Target command:** $ARGUMENTS (if empty, detect from the repo —
`npm test` / `pytest` / `go test ./...` / `cargo test` / project script).

## Loop (max 3 iterations, then stop and report)

1. Run the test command with coverage enabled.
2. Parse the output: failing tests + coverage threshold violations.
   If everything passes, jump to step 5.
3. Diagnose before fixing. For each failure, state the root cause in one line
   (broken assertion vs. broken impl vs. flaky/env). **Fix the code when the test
   is right; fix the test only when the test itself is wrong** — never edit a test
   purely to make it pass and mask a real defect.
4. For coverage gaps, add tests for the genuinely uncovered branches/edge cases.
   Don't pad coverage with assertion-free tests.
5. Re-run. Repeat from step 1 until green or 3 iterations are used.

## Stop conditions
- All tests pass and thresholds met → report the final coverage summary.
- 3 iterations without convergence → STOP, show remaining failures and your
  diagnosis, and ask how to proceed. Do not claim success.

## Rules
- Fail loud: if any test was skipped or a threshold was lowered, say so explicitly.
- Never lower a coverage threshold to pass — surface it and ask first.
- Keep edits surgical; touch only what the failures require.
