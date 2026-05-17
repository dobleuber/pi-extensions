# Code Context

## Files Retrieved
1. `openspec/changes/add-roger-voice-laptop-interface/proposal.md` (lines 1-35) - high-level scope, new capabilities, integration impact.
2. `openspec/changes/add-roger-voice-laptop-interface/design.md` (lines 1-168) - implementation decisions, risks, migration slices, open questions.
3. `openspec/changes/add-roger-voice-laptop-interface/tasks.md` (lines 1-80) - ordered task breakdown and dependency cues.
4. `openspec/changes/add-roger-voice-laptop-interface/specs/roger-voice-interface/spec.md` (lines 1-130) - voice pipeline requirements and backend evaluation criteria.
5. `openspec/changes/add-roger-voice-laptop-interface/specs/roger-context-routing/spec.md` (lines 1-60) - routing/session/model-selection requirements.
6. `openspec/changes/add-roger-voice-laptop-interface/specs/roger-agent-execution/spec.md` (lines 1-75) - pi-agent dispatch, permissions, lifecycle/logging, cwd/cancellation requirements.

## Key Code
No implementation code exists yet. The repository is currently an OpenSpec-only workspace: `openspec/specs/` and `openspec/changes/archive/` are empty, and the active change contains only proposal/design/spec/task docs.

Critical implementation requirements:

- Roger is a Python-first daemon/orchestrator because local audio, wake-word, VAD, STT, and TTS candidates are Python-friendly (`design.md` lines 85-92).
- Voice pipeline: always-on local wake word for “Hola Roger” -> one instruction capture with VAD -> local STT -> visible transcription preview -> router -> pi-agent -> concise local TTS response -> return to listening (`specs/roger-voice-interface/spec.md` lines 3-130).
- Speech backend adapters are mandatory so wake/VAD/STT/TTS engines can be changed by config without touching routing or pi execution (`specs/roger-voice-interface/spec.md` lines 118-123).
- Initial backend candidates: NanoWakeWord GRU/LSTM/TCN; Silero/WebRTC VAD; faster-whisper/whisper.cpp; Kokoro/Piper (`design.md` lines 38-83).
- pi integration should start with `pi --mode rpc` JSONL, not SDK embedding or one-shot shelling, to preserve streamed events, sessions, and model switching (`design.md` lines 94-101).
- Sessions must be separate for `system` and `current-project`; routing is initially rule-based with clarification for ambiguity (`design.md` lines 103-115; `specs/roger-context-routing/spec.md` lines 3-34).
- Online work uses pi’s configured default model; offline work falls back to configured Ollama model and reports if Ollama is unavailable (`specs/roger-context-routing/spec.md` lines 36-49).
- Roger does not add an independent permission system in MVP; pi-agent runs with terminal-equivalent permissions. The required safety boundary is transcription preview/cancel before dispatch (`design.md` lines 117-124; `specs/roger-agent-execution/spec.md` lines 14-23, 66-75).

## Architecture
Recommended data flow:

1. `roger` CLI loads config, runs health checks/spikes, or starts daemon.
2. Daemon keeps only wake adapter active continuously.
3. Wake detection starts audio capture and VAD endpointing for one instruction.
4. STT adapter transcribes local audio; preview UI displays transcript with accept/cancel/timeout.
5. Router classifies accepted text to a session (`system` or `current-project`) and resolves cwd/model mode.
6. pi RPC client sends prompt to `pi --mode rpc`, streams text/tool/command events into log surface, and returns completion/error summary.
7. TTS adapter speaks a short summary; full logs remain textual.
8. Daemon returns to wake listening.

Suggested initial project structure:

```text
pyproject.toml
README.md
roger/
  __init__.py
  cli.py                  # entrypoint: daemon, health, benchmarks, manual loop
  config.py               # typed config for backends, paths, thresholds, sessions, models
  daemon.py               # top-level state machine / one-instruction loop
  audio/
    capture.py            # PipeWire/ALSA microphone capture abstraction
    playback.py           # local audio output for TTS
  backends/
    interfaces.py         # WakeWord, VAD, STT, TTS protocols
    wake_manual.py        # development/manual trigger
    wake_nanowakeword.py
    vad_silero.py
    vad_webrtc.py
    stt_faster_whisper.py
    stt_whisper_cpp.py
    tts_kokoro.py
    tts_piper.py
  benchmarks/
    wake.py
    vad.py
    stt.py
    tts.py
  pi_rpc/
    client.py             # JSONL process lifecycle, send prompt, stream events, stop/abort
    events.py
    sessions.py           # create/reuse per-domain sessions, cwd/model settings
  routing/
    registry.py           # system/current-project/future domains
    router.py             # rule-based classification and ambiguity handling
  ui/
    preview.py            # visible transcript accept/cancel/timeout
    logs.py               # task lifecycle + streamed pi logs
  summarization.py        # concise spoken summaries from final status/logs
  health.py               # dependency/model/audio/pi/Ollama checks
configs/
  roger.example.toml
models/
  wake/                   # generated/selected NanoWakeWord artifacts, gitignored if large
benchmarks/data/
  audio/
  transcripts/
tests/
  test_routing.py
  test_config.py
  test_preview.py
  test_pi_rpc_smoke.py
  test_backend_smoke.py
scripts/
  train_wake_nanowakeword.py
  run_benchmarks.py
```

## Task Dependencies

- Start with tasks 1.1-1.4: choose/create Python package, dependency management, config, CLI. Most other tasks need these foundations.
- Run spikes before hard-coding adapters: wake tasks 2.1-2.7 and speech tasks 3.1-3.6 produce selected defaults, thresholds, model paths, and licensing/install notes.
- Define adapter interfaces early (4.1) and keep manual trigger (4.2) available so pi/router/UI work can proceed without reliable wake detection.
- pi RPC integration (5.1-5.4) and router/session registry (6.1-6.5) can proceed in parallel after config exists; both are needed before end-to-end dispatch.
- Preview/logs (7.1-7.4) must be complete before any real pi dispatch because preview is the main STT safety boundary and logs carry detailed output.
- MVP manual loop (8.1-8.4) should be the first end-to-end validation path: typed/simulated transcript -> preview -> router -> pi RPC -> logs -> TTS.
- MVP voice loop (9.1-9.6) should wait for selected/working wake, VAD, STT, TTS adapters and a passing manual loop.
- Verification/docs (10.1-10.5) finalize setup, benchmark results, OpenSpec validation, smoke commands, and task checkoffs.

## Start Here
Open `openspec/changes/add-roger-voice-laptop-interface/tasks.md` first. It is the implementation checklist and shows the intended sequence from project foundation through spikes, adapters, pi integration, manual MVP, voice MVP, and verification.

## Constraints, Risks, Open Questions

- Target environment: CachyOS/Arch-like Linux laptop with PipeWire/ALSA, Hyprland tooling, pi-agent installed, Ollama installed but not running (`design.md` lines 1-5).
- All STT/TTS must be local/offline after model install; no cloud/browser speech APIs.
- Custom “Hola Roger” wake detection is the highest spike risk; keep manual/push-to-talk or openWakeWord fallback available.
- Verify package and model licensing, especially Piper package status/licensing and newer wake/TTS libraries.
- Decide preview UI surface: terminal, notification, Hyprland overlay, or minimal local web UI.
- Decide how `current-project` is inferred when launched outside a repository.
- Choose an Ollama fallback model suitable for tool-using pi sessions.
