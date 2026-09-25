---
description: Implement an approved OpenSpec change, run its tests, and verify it
---

Run the implementation, testing, and verification workflow for exactly one existing OpenSpec change. The requested change is: $@

This command is only for applying an already-planned change. Do not explore or propose a change, rewrite its design/specs, archive it, commit it, or publish anything. If implementation exposes a design/spec problem or requires scope expansion, stop and ask before changing the plan.

## 1. Select and preflight the change

- Require one unambiguous change name. If none is provided, run `openspec list --json` and ask the user to select; do not guess.
- Run `openspec status --change <name> --json` and `openspec instructions apply --change <name> --json`.
- If planning is blocked or required artifacts are missing, stop and report that; do not start implementation.
- Read every context file returned by the apply instructions. Report the schema, task progress, pending tasks, and the test/validation commands you intend to use before editing.
- Determine project test commands from the change tasks and design, repository instructions (`AGENTS.md`/`README`), and the relevant package scripts or test configuration. Prefer focused tests for each changed area; do not run broad suites repeatedly when a focused test is sufficient. If the right test command remains unclear, ask rather than inventing one.

## 2. Implement and test each pending task

- Follow the `openspec-apply-change` procedure and work through pending tasks in order, one task at a time.
- After each implementation task, run the focused tests or checks relevant to that task before marking its checkbox complete. For a task that explicitly requires no test, record why. Never mark a task complete when its required test failed or was not run.
- If a test fails, investigate and fix within the approved change, then rerun the failing test and any directly affected checks. Do not hide failures or claim a pass from partial output.
- Pause if requirements are ambiguous, a test is blocked, or implementation requires a design/spec change. Report completed tasks, test evidence, remaining work, and the blocker.

## 3. Run final checks and verify

After all implementation tasks are complete:

1. Run the repository's documented final test/typecheck/lint commands relevant to the changed areas, avoiding an identical suite rerun if it already passed after the last relevant code change.
2. Run `openspec validate <name> --strict --json --no-interactive`.
3. Follow the `openspec-verify-change` procedure to check completeness, correctness, scenario coverage, and design coherence against the change artifacts.
4. If verification requires a code fix, make it within scope, rerun the affected tests and OpenSpec validation, then verify again.

Finish with a concise report naming the change, tasks completed, exact test/validation commands and outcomes, and any verification warnings. Do not archive or commit; leave that as a separate user decision.