## Context

The project starts as an empty workspace for designing Roger, a voice-first laptop interface backed by pi-agent. The target environment is a CachyOS/Arch-like Linux laptop with PipeWire/ALSA audio, Hyprland tooling available, pi-agent installed, and Ollama installed but not currently running. pi supports both RPC mode and SDK embedding; RPC is the best first integration point because it keeps Roger independent from pi internals while still allowing prompts, sessions, model switching, and streamed events.

Roger is intended to control the laptop broadly, not only a single code repository. It must be capable of installing software, updating the system, killing apps, creating projects, running tests, generating files/media, and later integrating with email or other apps. STT and TTS must remain local. The work model should use pi's configured default model while online and Ollama only as an offline fallback.

## Goals / Non-Goals

**Goals:**

- Provide an always-listening local wake-word interface for “Hola Roger”.
- Capture one spoken instruction after wake word for the MVP, then return to listening after response.
- Show a transcription preview before dispatching work to pi-agent.
- Route requests to separate pi-agent sessions by context/domain, starting with `system` and `current-project`.
- Use the same execution permissions as pi in the terminal; Roger does not add an independent permission system in the MVP.
- Keep detailed task logs visible while speaking concise final/status responses through local TTS.
- Support offline operation for the work model by falling back to Ollama when pi's online default model is unavailable.

**Non-Goals:**

- Multi-turn conversational voice sessions in the MVP; this is a later phase.
- A full desktop GUI in the MVP; a terminal UI, desktop notification, or simple overlay is sufficient for transcription preview and logs.
- Custom permission prompts beyond pi's normal terminal-level permissions.
- Email, calendar, browser automation, or image-generation integrations in the MVP; the architecture must allow them later.
- Replacing pi-agent internals; Roger is an orchestration layer over pi.

## Decisions

### Decision: Use a Roger daemon with local voice pipeline

Roger will run as a daemon or long-running foreground process that keeps only the lightweight wake-word detector active continuously. After detecting “Hola Roger”, it activates voice activity detection and local STT for the instruction. This avoids running heavy transcription continuously.

Alternatives considered:

- Push-to-talk first: simpler, but does not match the target experience.
- Continuous full STT: simpler conceptually, but higher CPU/GPU use and more privacy/noise risk.

### Decision: Treat “Hola Roger” wake-word detection as a spike risk

The intended wake word is custom. The preferred starting point is NanoWakeWord because it is actively maintained and is focused on training custom wake-word models with minimal effort. The wake-word spike will only train and compare NanoWakeWord GRU, LSTM, and TCN architectures for “Hola Roger”. `openWakeWord` remains a fallback/baseline only if NanoWakeWord fails to produce acceptable reliability or resource usage. If custom wake-word reliability is poor, the fallback for development may be a temporary push-to-talk trigger, a known pretrained wake word, or the openWakeWord baseline while preserving the rest of the architecture.

NanoWakeWord training will use `target_phrase: "hola roger"` with fixed positive samples, automatic adversarial negatives, phoneme adversarial negatives, and a small manual negative list for nearby phrases such as “hola”, “roger”, “oye roger”, “hola rojo”, “hola royer”, and “ola roger”.

Alternatives considered:

- NanoWakeWord GRU: balanced candidate for speed and robustness.
- NanoWakeWord LSTM: robustness candidate for a noisy environment and a multi-syllable phrase.
- NanoWakeWord TCN: modern sequential candidate for low latency and parallelizable inference.
- openWakeWord: mature and widely used; useful as a baseline/fallback, but less clearly optimized for this custom phrase workflow.
- NanoWakeWord DNN/CNN/RNN/QuartzNet/BcResNet/Transformer/CRNN/Conformer/E-Branchformer: intentionally excluded from the first spike to keep the comparison small.
- microWakeWord: strong embedded/ESPHome-oriented option, but excluded from the first spike because it is less aligned with a Python laptop daemon as the first implementation target.
- Use only pretrained keywords: faster but does not satisfy the “Roger” identity.
- Use STT to detect “Hola Roger”: flexible, but usually more resource-intensive for always-on use.

### Decision: Benchmark speech components behind adapters

Roger will isolate wake word, VAD, STT, and TTS behind adapters so the best local engine can be selected empirically without rewriting the orchestration layer.

Initial STT ranking:

1. `faster-whisper`: primary candidate because it offers strong Whisper accuracy with CTranslate2 acceleration and a Python-friendly API.
2. `whisper.cpp`: baseline/fallback candidate because it is highly portable, has excellent local/CLI ergonomics, and is actively maintained.
3. `sherpa-onnx`: future candidate if streaming ASR or a broader ONNX speech stack becomes more important.
4. Vosk: fallback for very low-resource/offline cases, but likely lower transcription quality for open-ended Spanish instructions than Whisper-family models.

Initial VAD ranking:

1. Silero VAD: primary candidate because it is accurate, local, actively maintained, and already widely used for speech pipelines.
2. WebRTC VAD: fallback candidate because it is tiny and proven, but less flexible and generally less accurate in noisy laptop environments.

Initial TTS ranking:

1. Kokoro: primary candidate to test because it is local, Apache-licensed, supports Spanish, has a simple Python API, and should produce more natural speech than older low-resource engines.
2. Piper: low-resource fallback/baseline because it is fast, local, scriptable, and has Spanish voices, but the original repository is archived and the PyPI/package licensing/story requires verification.
3. F5-TTS or Coqui XTTS: quality/voice-cloning candidates for later phases, but heavier and not the best MVP default for short assistant responses.

All selected components must work without internet after their models and dependencies are installed.

Alternatives considered:

- Cloud STT/TTS: better in some cases, but violates the local-only constraint.
- Browser speech APIs: convenient, but not reliably offline/local.
- A single all-in-one speech framework: simpler packaging in theory, but premature before measuring wake-word, VAD, STT, and TTS quality independently.

### Decision: Keep Python as the first orchestrator runtime

Roger should start as a Python daemon because the best local audio, wake-word, VAD, STT, and TTS candidates are Python-friendly. The pi integration can still use RPC, so the Python orchestrator does not need to link directly against pi internals.

Alternatives considered:

- Node/TypeScript: attractive if using the pi SDK directly, but weaker for the local speech stack.
- Shell scripts: useful for spikes, but too brittle for a daemon that manages audio streams, sessions, and task state.

### Decision: Integrate with pi through RPC first

Roger will start and control pi-agent via `pi --mode rpc` using JSONL commands/events. This gives Roger programmatic control from Python or Node without coupling to pi's SDK types. The SDK remains a later option if lifecycle, resource loading, or custom tools require tighter integration.

Alternatives considered:

- Pi SDK: type-safe and powerful, but a larger initial integration surface.
- Shelling out to `pi -p` per instruction: simpler, but weaker for long-running tasks, event streaming, sessions, and model switching.

### Decision: Use a global router and separate pi sessions

Roger will maintain a lightweight global router that classifies intent and dispatches to a domain session. The MVP supports two domains:

- `system`: laptop/system administration tasks such as installing packages, updating, killing apps, and managing applications.
- `current-project`: tasks for the active working directory/project, such as creating demos, editing files, and running tests.

Future domains include named projects, communications, media generation, and browser/app automation.

Alternatives considered:

- One global session: simpler but contaminates context and increases ambiguity.
- Fully manual session selection: safer but makes voice interaction feel rigid.

### Decision: Preview transcription, not every action

Before dispatching to pi-agent, Roger will display the recognized instruction and provide a short opportunity for correction/cancellation. The MVP does not require a separate confirmation for every command or destructive action because Roger is meant to have the same permissions as pi in terminal. The preview is the main guardrail against STT mistakes.

Alternatives considered:

- Confirm every task: safer but too slow for a laptop interface.
- No preview: faster but dangerous when STT mishears commands.

### Decision: Speak summaries, show logs

Roger will speak concise status/final summaries through local TTS while keeping the full pi-agent stream/log visible. Long command output and detailed tool logs should not be spoken by default.

Alternatives considered:

- Speak everything: noisy and unusable for long tasks.
- Text-only output: fails the hands-free goal.

## Risks / Trade-offs

- Custom wake word has poor reliability or high false positives → run an early spike, tune thresholds, and keep a temporary fallback trigger for development.
- Newer wake/TTS libraries may be less stable than mature alternatives → keep mature baselines in the benchmark and hide each engine behind an adapter.
- Component package licensing may differ from repository licensing → verify licenses during the spike before locking dependencies.
- STT mishears destructive instructions → require transcription preview and cancellation/correction before dispatch.
- Offline fallback model is weaker than online pi default → keep task scope realistic offline, expose when Roger is in offline mode, and use Ollama models configured for tool-capable coding tasks.
- Long-running pi tasks may exceed a voice interaction window → stream visible status, speak milestones only, and allow Roger to return to listening or report completion later.
- Session router chooses the wrong context → ask a clarification question when confidence is low or when a target domain/project is ambiguous.
- Audio/TTS stack differs across Linux machines → isolate audio capture/playback behind adapters and document the tested PipeWire/ALSA path first.
- Same-permissions execution can perform dangerous actions → do not hide the transcript/log, preserve pi's normal behavior, and keep the transcription preview as a mandatory dispatch boundary.

## Migration Plan

This is a new capability, so no data migration is required. Implementation should proceed in slices:

1. Prove local audio capture, VAD, STT, TTS, and pi RPC independently.
2. Run one-component-at-a-time benchmarks: NanoWakeWord GRU vs LSTM vs TCN, faster-whisper vs whisper.cpp, Silero vs WebRTC VAD, and Kokoro vs Piper.
3. Add a manual trigger path to test the full instruction-to-pi-to-voice loop.
4. Add wake-word detection for “Hola Roger” using the selected wake engine.
5. Add the router with `system` and `current-project` sessions.
6. Add online/default-model vs offline/Ollama selection.
7. Harden logs, cancellation, and error states.

Rollback is simply stopping Roger; it should not replace pi or system shell behavior.

## Open Questions

- Which NanoWakeWord architecture among GRU, LSTM, and TCN works best for “Hola Roger” on this laptop in false positives, false negatives, latency, and idle CPU?
- Does faster-whisper provide better Spanish latency/accuracy than whisper.cpp on the available CPU/GPU, or is whisper.cpp sufficient and simpler?
- Does Kokoro provide acceptable Spanish quality and latency locally, or should Piper remain the MVP default despite its maintenance status?
- What UI should host transcription preview first: terminal, desktop notification, Hyprland overlay, or a minimal web/local UI?
- How should Roger infer `current-project` when launched outside a repository or project directory?
- Which Ollama model should be the offline default for tool-using pi sessions?
