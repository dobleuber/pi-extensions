## 1. Profile contract and session state

- [x] 1.1 Add the two-profile catalog for `Luna Max` (`openai-codex/gpt-5.6-luna` + `max`) and `Astra High` (`openai-codex/gpt-6-astra` + `high`), including default/prompt source metadata
- [x] 1.2 Add router-owned session profile state initialized to Luna Max without changing global Pi startup settings
- [x] 1.3 Preserve the selected profile across later routed prompts and router off/on transitions, while allowing `Use Default:` to clear the explicit source
- [x] 1.4 Add strict English/Spanish extraction for `Use Astra:`/`Usa Astra:` and `Use Default:`/`Usa el modelo predeterminado:`, including case-insensitive matching, colon requirements, and control-text removal
- [x] 1.5 Ensure model mentions outside the leading control phrase and the removed `@thinking:<level>` prefix do not change profile state

## 2. Work-model application

- [x] 2.1 Add a Pi runtime adapter that resolves the profile’s exact provider/model through the existing model registry, including `openai-codex/gpt-6-astra`
- [x] 2.2 Apply the selected model and its fixed thinking level before work dispatch, then verify the effective provider/model and thinking level
- [x] 2.3 Make profile application atomic from the router’s perspective: report requested-profile failures visibly, do not dispatch under a substitute, and retain the prior profile for retry
- [x] 2.4 Keep the remote `openai-codex/gpt-5.6-luna` translation/classification model with reasoning disabled (`none`) independent from the selected work profile

## 3. Routing and command behavior

- [x] 3.1 Insert profile extraction and application into the routed-prompt pipeline before translation and dispatch
- [x] 3.2 Remove automatic thinking/model changes driven by router complexity, keyword, risk, or advisory output
- [x] 3.3 Enforce router ownership of `/model` and `/thinking` while routing is on, while preserving native Pi handling when routing is off
- [x] 3.4 Keep the existing router command and status transitions functional while profile state remains session-scoped

## 4. Details and documentation

- [x] 4.1 Extend router metadata and details with active profile, provider/model, thinking level, source, and requested/effective failure information
- [x] 4.2 Update the pi-router README with the two supported phrases, Spanish equivalents, fixed thinking levels, precedence, session lifetime, reset behavior, command boundary, failures, and costs
- [x] 4.3 Add migration guidance removing `@thinking` and the former implicit model-selection behavior
- [x] 4.4 Keep the tracked `extensions/pi-router` implementation as the source of truth and avoid importing unrelated installed-router behavior

## 5. Tests and verification

- [x] 5.1 Add parser tests for strict leading position, case-insensitivity, colon handling, English/Spanish phrases, reset phrases, phrase removal, and body/quote/code/context non-selection
- [x] 5.2 Add profile-state tests for Luna default, Astra selection, persistence, reset, router off/on behavior, and no automatic promotion or demotion
- [x] 5.3 Add model-application tests for exact registry resolution, fixed thinking levels, router/work-model separation, effective-state verification, and visible failure/no-fallback behavior
- [x] 5.4 Add input/extension integration tests for router-on native command gating and router-off native command passthrough
- [x] 5.5 Run the pi-router test suite, strict OpenSpec validation, and focused documentation/format checks
