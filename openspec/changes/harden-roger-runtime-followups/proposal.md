## Why

Roger already has a working voice-to-pi MVP, but verification found several hardening gaps that matter once it becomes an always-on laptop assistant: automatic offline fallback, visible task progress, resilient TTS failure handling, in-flight cancellation, and easier domain expansion. Capturing these as future specs keeps the completed MVP stable while preserving the next reliability and UX contracts before implementation starts.

## What Changes

- Add automatic online/offline model selection so Roger can detect unavailable internet/pi providers and fall back to Ollama without requiring a manual `--offline` flag.
- Add a first-class task progress log fed by pi RPC events, including assistant text deltas, tool start/update/end events, command output, errors, and completion status.
- Add resilient spoken-output behavior so local TTS failures never block a completed task or hide the textual result.
- Add in-flight task cancellation using pi RPC control commands where available, with a clear result when abort is unsupported or fails.
- Add a more extensible routing contract so future domains can be added through configuration/rules without changing the wake/VAD/STT/TTS voice pipeline.

## Capabilities

### New Capabilities
- `roger-offline-model-fallback`: Automatic detection of online provider availability and safe fallback to configured Ollama-backed pi execution.
- `roger-task-progress-log`: Persistent visible progress logging for streamed pi-agent text, tool events, command output, errors, and task completion.
- `roger-resilient-spoken-output`: TTS failure isolation and textual fallback behavior for successful, failed, and clarification outcomes.
- `roger-task-cancellation`: User-facing stop/cancel semantics for active pi-agent work, mapped to pi RPC abort capabilities when technically available.
- `roger-extensible-context-routing`: Registry-driven routing extension points for new domains such as named projects, communications, or media.

### Modified Capabilities
- None yet. The current Roger MVP change has not been archived into main specs, so these follow-ups are captured as future capabilities instead of modifying archived specs.

## Impact

- Affected code areas: `src/roger/pi_rpc/`, `src/roger/manual_loop.py`, `src/roger/voice_loop.py`, `src/roger/tts_speaker.py`, `src/roger/routing/`, `src/roger/overlay.py`, and CLI/daemon wiring in `src/roger/cli.py`.
- Affected docs/tests: setup docs, task/daemon CLI tests, pi RPC client/runner tests, routing tests, overlay/log tests, and TTS failure tests.
- External systems: pi RPC mode, online pi providers, local Ollama server/model availability, local Kokoro/Piper-style TTS backends, and Omarchy/Hyprland overlay feedback.
- No breaking changes are intended; existing manual `--offline`, `--no-tts`, and `--no-overlay` flags should remain valid.
