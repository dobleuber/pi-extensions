## 1. Model Availability and Offline Fallback

- [x] 1.1 Add a model availability policy abstraction that returns online, offline-fallback, or unavailable decisions.
- [x] 1.2 Add bounded connectivity/provider probes and config flags for automatic fallback, explicit offline, and fallback disabled modes.
- [x] 1.3 Update `PiSessionManager` command generation to include the llama.cpp provider/model profile and pi offline startup behavior when fallback is selected.
- [x] 1.4 Update `PiAgentRunner` to retry once on recognized online provider/network startup or prompt-acceptance failures.
- [x] 1.5 Add tests for online default, explicit offline, automatic fallback, unavailable llama.cpp server, and missing fallback model reporting.

## 2. Task Progress Logging

- [x] 2.1 Extend `TaskLog` to store structured assistant, tool, retry, queue, error, start, and completion events.
- [x] 2.2 Add event observer/callback support to `PiAgentRunner` so streamed pi RPC events are not discarded.
- [x] 2.3 Render task logs for CLI and overlay with concise current status plus a detailed textual surface or persistent log reference.
- [x] 2.4 Add size limits, truncation/rotation behavior, and documented log location for daemon runs.
- [x] 2.5 Add tests covering text deltas, tool start/update/end correlation, prompt rejection, task failure, and long output truncation.

## 3. Resilient Local Speech Output

- [x] 3.1 Add a safe speaker boundary that reports TTS synthesis/playback success or failure without leaking backend exceptions to task callers.
- [x] 3.2 Update manual loop, voice loop, typed task CLI, and daemon flows so TTS failure keeps textual results visible and does not change task completion status.
- [x] 3.3 Add visible warning/rate-limiting for repeated TTS degradation in daemon mode.
- [x] 3.4 Add tests for completed-task TTS failure, failure-summary TTS failure, clarification TTS failure, playback failure, and no-TTS mode.

## 4. In-flight Task Cancellation

- [ ] 4.1 Add active task tracking per Roger session so Roger knows which pi RPC client/session can be cancelled.
- [ ] 4.2 Implement pi RPC client commands for `abort`, `abort_bash`, and `abort_retry` with response parsing.
- [ ] 4.3 Add cancellation flow in the runner that reports command acceptance separately from final task end state.
- [ ] 4.4 Add stop-intent handling for active tasks via voice phrases and a CLI/control command.
- [ ] 4.5 Add tests for accepted abort, no active task, rejected abort, ambiguous active session, bash abort, retry abort, and unavailable abort capability.

## 5. Extensible Context Routing

- [ ] 5.1 Move routing domain metadata, keyword rules, ambiguity rules, and destructive safety rules into registry/config data structures.
- [ ] 5.2 Add route decision explanations including matched domain, rule, confidence/safety reason, and clarification text.
- [ ] 5.3 Add support for named project and non-project domains without modifying the voice pipeline.
- [ ] 5.4 Add a route dry-run/diagnostic path for tests and manual inspection.
- [ ] 5.5 Add health/startup validation for unknown sessions, malformed route rules, and invalid domain policies.
- [ ] 5.6 Add tests for configurable system/current-project parity, named project routing, communications/media-style domains, destructive ambiguity, fresh-session policy, and route explanations.

## 6. Documentation and Verification

- [ ] 6.1 Update setup docs with automatic offline fallback behavior, llama.cpp prerequisites, and visible fallback status.
- [x] 6.2 Document task log location, log retention/truncation behavior, and how to inspect recent daemon task logs.
- [ ] 6.3 Document cancellation phrases/CLI commands and limitations of pi RPC abort semantics.
- [ ] 6.4 Update troubleshooting docs for local TTS degradation and text-only fallback.
- [ ] 6.5 Run the full unit suite, focused smoke tests for typed tasks, and OpenSpec strict validation for this change.
