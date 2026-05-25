## 1. Extension Structure and Configuration

- [x] 1.1 Create the Pi router extension package/module structure with installable entry points and tests.
- [x] 1.2 Add router configuration for states `off` and `on`, plus global, session, and single-prompt overrides.
- [x] 1.3 Add configurable local router model settings for provider, model, base URL, timeout, fallback mode, and max input size.
- [x] 1.4 Add status/diagnostic surfaces showing router state, router model, work model, and degraded/fallback state.

## 2. Prompt Language Routing

- [x] 2.1 Implement input-hook handling that skips slash commands, prompt-template invocations, and other raw command syntax.
- [x] 2.2 Implement local llama.cpp/`gemma4` translation from Spanish or mixed prompts into concise English work prompts.
- [x] 2.3 Preserve technical tokens such as code, commands, file paths, quoted strings, identifiers, and error output during prompt normalization.
- [x] 2.4 Record original prompt, transformed prompt, source language, router model, and fallback metadata for logs/details inspection.
- [x] 2.5 Add bounded timeout and fallback behavior for unavailable router model, translation failures, and oversized prompts.
- [x] 2.6 Add context-aware faithful translation using conversation summary only for reference resolution, with metadata for resolved and unresolved references.

## 3. Thinking-Level Routing

- [x] 3.1 Implement deterministic thinking-level policy for low, medium, and high complexity prompts.
- [x] 3.2 Combine deterministic policy with local model-assisted classification while clamping unsafe under-classification.
- [x] 3.3 Apply selected thinking level through Pi extension/runtime APIs where available.
- [x] 3.4 Add CLI/RPC-compatible thinking application path using `--thinking`, model shorthand, or RPC `set_thinking_level` when supported.
- [x] 3.5 Record requested and effective thinking levels plus selection reason for diagnostics.

## 4. Bypass and Router Details UX

- [x] 4.1 Add a compact router-details entry before work-model dispatch containing original Spanish prompt, English work prompt, selected thinking level, and target work model.
- [x] 4.2 Add an expandable/collapsible router-details shortcut or command, with configurable keybinding and documented handling for the existing Ctrl+R session-rename conflict.
- [x] 4.3 Add router bypass controls for global/session/single-prompt operation.
- [x] 4.4 Keep router details collapsed by default and avoid introducing a separate preview mode or approval gate.
- [x] 4.5 Extend router details after completion with original English answer, Spanish answer, effective thinking metadata, and fallback events.
- [x] 4.6 Ensure print/RPC mode records equivalent router metadata when interactive details UI is unavailable.

## 5. Final Answer Translation

- [x] 5.1 Implement final assistant-answer translation from English to Spanish in message-completion handling.
- [x] 5.2 Preserve code blocks, commands, paths, identifiers, exact errors, and generated artifact bodies during answer translation.
- [x] 5.3 Retain original English answer in metadata/logs/details when Spanish translation is applied.
- [x] 5.4 Add visible fallback behavior when final-answer translation fails or times out.

## 6. Work-Model Policy and Stratus Compatibility

- [x] 6.1 Keep router model selection independent from Pi's selected work model.
- [x] 6.2 Verify routed prompts dispatch to the existing Pi default work model without changing model selection.
- [ ] 6.3 Verify routed prompts dispatch to Stratus when the user selects a Stratus provider/model and credits are available.
- [x] 6.4 Report Stratus or other work-model availability failures separately from router translation failures.
- [x] 6.5 Verify model changes mid-session keep using the selected work model while preserving router policy.

## 7. Roger Integration

- [x] 7.1 Update Roger pi-agent dispatch to allow the Pi-level router to handle prompt language and thinking selection.
- [x] 7.2 Preserve Roger domain/session routing while delegating language/thinking routing to Pi.
- [x] 7.3 Record Pi router metadata in Roger task logs when exposed by pi-agent/RPC.
- [x] 7.4 Use Pi router Spanish final answers for Roger overlay and TTS summaries when available.
- [x] 7.5 Add degraded-mode visibility when Pi router details, translation, or metadata is unavailable for Roger entrypoints.

## 8. Tests and Documentation

- [x] 8.1 Add prompt routing tests for Spanish, English, mixed technical prompts, slash commands, prompt templates, and fallback paths.
- [x] 8.2 Add thinking-level tests for simple, routine, complex, ambiguous, risky/destructive, unsupported-model, and unavailable-control cases.
- [x] 8.3 Add router-details tests for collapsed default display, expansion shortcut/command, keybinding configuration, bypass, metadata display, and non-interactive recording.
- [x] 8.4 Add final-answer translation tests covering technical content preservation and translation failure fallback.
- [x] 8.5 Add Roger integration tests for routed metadata, Spanish UX preservation, and degraded Pi-router behavior.
- [x] 8.6 Update setup/troubleshooting docs for enabling the Pi router, local `gemma4` prerequisites, Stratus compatibility, thinking selection, bypass controls, and inspection surfaces.
- [x] 8.7 Run full unit tests, Pi extension smoke tests, Roger smoke tests, and OpenSpec strict validation.
