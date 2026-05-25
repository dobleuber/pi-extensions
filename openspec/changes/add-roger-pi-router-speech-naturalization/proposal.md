## Why

Roger's spoken-output naturalization currently belongs at the wrong boundary: Roger can end up preparing TTS text outside pi-agent/pi-router, including direct local model calls or fragile validation/fallback behavior. Roger should keep task execution and model routing inside pi-agent, and pi-router should provide a Roger-aware speech surface so Kokoro receives a natural Spanish speech script while visible output remains canonical.

## What Changes

- Add a Roger-aware pi-router speech naturalization contract for requests originating from Roger.
- Extend routed pi-agent task responses so they can include both:
  - `display_text`: canonical task result for overlay, CLI, logs, retry/debug context.
  - `speech_text`: Spanish, TTS-ready naturalized speech text for Roger/Kokoro.
- Add request metadata/flag that indicates Roger needs a speech result, for example `source = "roger"` and/or `speech.enabled = true`.
- Move model-backed speech naturalization behind pi-agent/pi-router instead of letting Roger call llama.cpp directly.
- Preserve local/offline behavior by routing speech naturalization through the configured pi provider/model path, including `llama-cpp`/`gemma4` when offline.
- Remove the need for Roger-side anti-English validation; Roger should trust structured `speech_text` from pi-router and only perform minimal safe fallback when that field is absent.
- Keep Roger's visual output unchanged even when `speech_text` differs.

## Capabilities

### New Capabilities

- `pi-router-roger-speech-naturalization`: Defines Roger request metadata, structured response fields, and pi-router responsibility for generating Spanish TTS-ready speech text.

### Modified Capabilities

- `roger-agent-execution`: Roger task dispatch should request and consume structured pi-router speech metadata when TTS is enabled.
- `roger-resilient-spoken-output`: Roger should degrade safely when pi-router speech metadata is missing or invalid without using direct model calls or language-detection hacks.
- `roger-task-progress-log`: Task logs should record pi-router-provided display/speech fields for debugging while rendering canonical output by default.
- `roger-voice-interface`: Spoken task responses should use pi-router-provided `speech_text` while overlay/CLI keep `display_text`.
- `roger-llama-cpp-runtime`: Offline speech naturalization should still go through pi-agent's llama.cpp provider/model routing instead of direct Roger HTTP calls.

## Impact

- Affected Roger code: `src/roger/pi_rpc/runner.py`, `src/roger/pi_rpc/client.py` if RPC payloads need metadata support, `src/roger/manual_loop.py`, `src/roger/voice_loop.py`, `src/roger/cli.py`, `src/roger/summarization.py`, task logs, and tests.
- Affected pi-router code: router request metadata handling, response shaping, and speech naturalization prompt/execution path.
- Affected behavior: Roger no longer performs model-backed translation directly; model-backed naturalization becomes part of routed pi-agent output.
- Compatibility: Existing text-only pi-agent responses remain supported. If `speech_text` is absent, Roger keeps canonical visible output and uses only minimal deterministic fallback or skips speech, without changing task status.
