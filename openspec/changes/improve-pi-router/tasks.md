## 1. Extension Structure and Configuration

- [x] 1.1 Create the Pi router extension package/module structure with installable entry points and tests.
- [ ] 1.2 Add router configuration for modes `off`, `on`, and `preview`, plus global, session, and single-prompt overrides.
- [ ] 1.3 Add configurable local router model settings for provider, model, base URL, timeout, fallback mode, and max input size.
- [ ] 1.4 Add status/diagnostic surfaces showing router mode, router model, work model, and degraded/fallback state.

## 2. Prompt Language Routing

- [ ] 2.1 Implement input-hook handling that skips slash commands, prompt-template invocations, and other raw command syntax.
- [ ] 2.2 Implement local llama.cpp/`gemma4` translation from Spanish or mixed prompts into concise English work prompts.
- [ ] 2.3 Preserve technical tokens such as code, commands, file paths, quoted strings, identifiers, and error output during prompt normalization.
- [ ] 2.4 Record original prompt, transformed prompt, source language, router model, and fallback metadata for logs/details inspection.
- [ ] 2.5 Add bounded timeout and fallback behavior for unavailable router model, translation failures, and oversized prompts.

## 3. Thinking-Level Routing

- [ ] 3.1 Implement deterministic thinking-level policy for low, medium, and high complexity prompts.
- [ ] 3.2 Combine deterministic policy with local model-assisted classification while clamping unsafe under-classification.
- [ ] 3.3 Apply selected thinking level through Pi extension/runtime APIs where available.
- [ ] 3.4 Add CLI/RPC-compatible thinking application path using `--thinking`, model shorthand, or RPC `set_thinking_level` when supported.
- [ ] 3.5 Record requested and effective thinking levels plus selection reason for diagnostics.

## 4. Preview, Bypass, and Details UX

- [ ] 4.1 Add optional preview UI showing original Spanish prompt, English work prompt, selected thinking level, and target work model.
- [ ] 4.2 Support preview actions: approve, edit translated prompt, bypass/send original, cancel, and remember session choice where applicable.
- [ ] 4.3 Add router bypass controls for global/session/single-prompt operation.
- [ ] 4.4 Add an inspectable router-details view or command for original prompt, transformed prompt, work model, thinking metadata, English answer, Spanish answer, and fallback events.
- [ ] 4.5 Ensure print/RPC mode records equivalent router metadata when interactive details UI is unavailable.

## 5. Final Answer Translation

- [ ] 5.1 Implement final assistant-answer translation from English to Spanish in message-completion handling.
- [ ] 5.2 Preserve code blocks, commands, paths, identifiers, exact errors, and generated artifact bodies during answer translation.
- [ ] 5.3 Retain original English answer in metadata/logs/details when Spanish translation is applied.
- [ ] 5.4 Add visible fallback behavior when final-answer translation fails or times out.

## 6. Work-Model Policy and Stratus Compatibility

- [ ] 6.1 Keep router model selection independent from Pi's selected work model.
- [ ] 6.2 Verify routed prompts dispatch to the existing Pi default work model without changing model selection.
- [ ] 6.3 Verify routed prompts dispatch to Stratus when the user selects a Stratus provider/model and credits are available.
- [ ] 6.4 Report Stratus or other work-model availability failures separately from router translation failures.
- [ ] 6.5 Verify model changes mid-session keep using the selected work model while preserving router policy.

## 7. Roger Integration

- [ ] 7.1 Update Roger pi-agent dispatch to allow the Pi-level router to handle prompt language and thinking selection.
- [ ] 7.2 Preserve Roger domain/session routing while delegating language/thinking routing to Pi.
- [ ] 7.3 Record Pi router metadata in Roger task logs when exposed by pi-agent/RPC.
- [ ] 7.4 Use Pi router Spanish final answers for Roger overlay and TTS summaries when available.
- [ ] 7.5 Add degraded-mode visibility when Pi router preview, translation, or metadata is unavailable for Roger entrypoints.

## 8. Tests and Documentation

- [ ] 8.1 Add prompt routing tests for Spanish, English, mixed technical prompts, slash commands, prompt templates, and fallback paths.
- [ ] 8.2 Add thinking-level tests for simple, routine, complex, ambiguous, risky/destructive, unsupported-model, and unavailable-control cases.
- [ ] 8.3 Add preview/details tests for approve, edit, bypass, cancel, metadata display, and non-interactive recording.
- [ ] 8.4 Add final-answer translation tests covering technical content preservation and translation failure fallback.
- [ ] 8.5 Add Roger integration tests for routed metadata, Spanish UX preservation, and degraded Pi-router behavior.
- [ ] 8.6 Update setup/troubleshooting docs for enabling the Pi router, local `gemma4` prerequisites, Stratus compatibility, thinking selection, bypass controls, and inspection surfaces.
- [ ] 8.7 Run full unit tests, Pi extension smoke tests, Roger smoke tests, and OpenSpec strict validation.
