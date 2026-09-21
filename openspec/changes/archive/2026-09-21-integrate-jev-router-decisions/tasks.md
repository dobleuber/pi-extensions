## Current scope correction

At the user's request, runtime Jev mode/approval flags and legacy persistent-profile compatibility have been removed. `/router on` now uses Jev directly; `/router off`, per-prompt directives, and conservative failure fallbacks remain. The completed tasks below document the implementation and its bounded offline evaluation; no expanded evaluation, release approval, or separate activation requirement is part of the current scope. Rubric/catalog v2 adds Terra Medium and task-based criteria without Luna latency claims. Verification: 148 tests pass; TypeScript checked after adding Terra to evaluation types.

## 1. Baseline and evaluation contract

- [x] 1.1 Verify the implementation worktree and installed Pi version; run the existing router suite and record the baseline before changes. Baseline: Node v26.7.0, pi-ai/pi-coding-agent 0.85.1, 107 tests passed, 0 failed (`npm test` in `extensions/pi-router`).
- [x] 1.2 Define task-based rubric/catalog v2 for Luna, Terra, Vega, and Astra, including substantive Luna fixtures with no latency criterion and Terra migration fixtures.
- [x] 1.3 Define offline calibration/held-out fixture splits and metric definitions for honest reporting. Added `src/jev-evaluation.ts` manifest; no runtime release-approval gate is required.
- [x] 1.4 Inspect the host input/dispatch lifecycle and create a failing integration test demonstrating that a queued future prompt cannot change an active tool continuation's model; identify the safe receiving-turn application boundary. Deferred profile application is exercised at `turn_start` after tool continuation settlement.

## 2. Jev configuration and typed decision adapter

- [x] 2.1 Add operational Jev configuration and tests for model, bounds, cost tier, credential ownership, and direct use whenever `/router on` is active. No Jev mode or approval flag is used.
- [x] 2.2 Pin a reviewed official TypeSafe SDK version and add an injectable adapter resolving TYPESAFE_API_KEY without logging or transmitting credentials as state. Pinned `@typesafe-ai/sdk` 0.6.0 and added injectable `src/jev.ts` transport.
- [x] 2.3 Define versioned input questions for profile suitability, translation necessity, and source language, plus a separate response translation question; test bounded request construction. Added versioned rubric/request builders and request-shape tests.
- [x] 2.4 Validate permitted choices, complete required fields, finite probabilities/confidence, and model/version metadata using offline success and malformed-response fixtures. Added normalization guards and malformed/low-confidence fixtures.
- [x] 2.5 Implement and test overall deadlines, disabled interactive retries, cancellation propagation, and rejection of late results; bound state plus question payloads. Added abort composition/deadline race and transport-boundary tests.

## 3. Per-prompt model selection

- [x] 3.1 Add failing tests proving that Use Default always forces Luna, other supported directives force their mapped profile, and the next unqualified prompt returns to automatic selection. Pipeline coverage verifies per-prompt Jev precedence.
- [x] 3.2 Implement deterministic precedence for current-prompt directives, eligible Jev recommendations, and Luna fallback; retain strict leading-position parsing and remove only the recognized prefix.
- [x] 3.3 Filter candidate profiles by approved mappings and deterministic eligibility/spending constraints; test unknown keys, included Terra, unavailable models, and empty candidate sets. Terra maps to `openai-codex/gpt-5.6-terra` with medium reasoning and tier 2; English/Spanish directives are covered.
- [x] 3.4 Apply and verify model/thinking state at the safe receiving-turn boundary from task 1.4; test explicit-profile failure without substitution and fallback failure without dispatch. Deferred queued profiles retain the active tool model.
- [x] 3.5 Keep Jev profile decisions per prompt, with no persistence as session or global profile preferences; test resume/fork boundaries, per-prompt directives, and unchanged global preferences.

## 4. Input translation gating

- [x] 4.1 Add tests for a single combined input decision call, including prompts with explicit model directives that still require translation checks. The adapter builds one input request and explicit-directive pipeline coverage still calls Jev.
- [x] 4.2 Build bounded task/recent-context state without uploading whole transcripts; test quoted evidence, code, technical-only prompts, contextual references, and oversize fallback. State fields are bounded and oversize requests retain the generative path.
- [x] 4.3 Integrate accepted input bypass as unchanged task text after control removal; retain the generative path for required, uncertain, incomplete, or failed decisions.
- [x] 4.4 Preserve response-language policy independently of input bypass; test Spanish output requirements and Roger speech requests after English input bypass.
- [x] 4.5 Test existing prompt formatting, literal preservation, command/bypass guards, translator failure policy, and cancellation without fallback dispatch. Existing router suite remains green with Jev cancellation coverage.

## 5. Final-response translation gating

- [x] 5.1 Add failing tests for already-Spanish, English, mixed-language, and technical-only final responses, including multiple text blocks and Markdown tables. Existing final-answer coverage plus Jev response-gate tests cover the boundaries.
- [x] 5.2 Add a separate bounded final-response decision covering all relevant prose when Spanish output is required; exclude commentary, tool calls, and aborted/error completions. Response state masks protected code and calls one response decision for the joined final blocks.
- [x] 5.3 Preserve final text on accepted bypass and invoke the existing translator on required, uncertain, invalid, oversized, or timed-out decisions; reject partial-coverage bypass. Adapter bounds and response-failure tests retain the generative path.
- [x] 5.4 Preserve technical masking, translation repairs, partial-translation warnings, and English context restoration across translated and unchanged output.
- [x] 5.5 Keep Roger display/speech envelope construction and completion bookkeeping independent of translation execution; test both translated and bypassed responses.

## 6. Turn isolation and diagnostics

- [x] 6.1 Bind input/profile and response-translation decision scope, response-language policy, cancellation, and metadata to the originating turn; test queued prompts, tool continuations, late results, and abandoned turns.
- [x] 6.2 Expose effective profile, selection source, input/response gating outcomes, fallback reasons, Jev version, policy revisions, and duration in router details.
- [x] 6.3 Verify diagnostics redact credentials and avoid new raw-content telemetry; test missing credentials and TypeSafe failures without affecting unrelated turns.
- [x] 6.4 Verify `/router on` uses Jev decisions directly, `/router off` performs no Jev input decisions, and uncertainty/failures use deterministic fallback without a runtime evaluation gate.

## 7. Evaluation evidence

- [x] 7.1 Create a reproducible evaluation runner using synthetic or explicitly approved cases; keep any live provider calls explicitly authorized and separately budgeted from offline tests. Added `npm run evaluate:jev` using offline fixtures only.
Tasks 7.2–7.6 (expanded live evaluation, calibration, downstream/adversarial testing, and quantitative release approval) were removed from this change at the user's request. They were not completed or passed. Existing smoke-test evidence remains available; these removals do not change the direct Jev runtime path.

## 8. Documentation and final verification

- [x] 8.1 Update README/configuration guidance for direct Jev use while `/router on` is active, TypeSafe credentials/data sharing, per-prompt directives, Use Default forcing Luna, fallback behavior, and Git rollback.
- [x] 8.2 Document that Jev profiles are per-prompt and are not persisted as session/global preferences; record Git rollback and local-only deployment guidance. No legacy compatibility branch is retained.
- [x] 8.3 Run the full router suite and focused host-lifecycle tests; verify all specified deterministic invariants and record commands/results. `npm test`: 148 passed; `npx tsc --noEmit` and focused lifecycle/adapter suites pass.
- [x] 8.4 Run strict OpenSpec validation and diff checks; review implementation coverage against all three capability specifications and report any blocked acceptance tasks. Strict validation passes; tasks 7.2–7.6 were removed from scope at the user's request, not marked as verified.
