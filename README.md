# Roger Laptop Interface

Roger is a local, voice-first laptop assistant backed by [`pi-agent`](https://github.com/earendil-works/pi-coding-agent). It listens for **“Hola Roger”**, captures a spoken instruction, routes it to the right pi session, executes real laptop/project tasks through pi, and responds with local speech plus a Wayland overlay.

Roger is designed for a Spanish-speaking user and an Omarchy/Hyprland laptop. Speech stays local/offline; task execution still uses pi-agent so Roger keeps the same tools, permissions, cwd/session behavior, and safety boundaries as a normal pi terminal session.

## Current Status

Implemented and archived OpenSpec changes:

- `add-roger-voice-laptop-interface`
- `migrate-ollama-to-llama-cpp`
- `harden-roger-runtime-followups`

Current canonical specs live under `openspec/specs/` and validate with:

```bash
openspec validate --specs --strict
```

> Note: `openspec/changes/improve-pi-router/` is separate Pi-router work and is not part of Roger’s current implementation status.

## Features

### Local voice pipeline

- Wake phrase: **“Hola Roger”**
- Wake backend: NanoWakeWord, currently using the local LSTM model:
  - `models/wake/nanowakeword/hola_roger_lstm/model/hola_roger_lstm.onnx`
- VAD: Silero
- STT: `faster-whisper` with Spanish transcription
- TTS: Kokoro local TTS
- Playback: PipeWire via `pw-play`, with `sounddevice` fallback
- No cloud STT/TTS fallback

Default speech profile:

| Component | Default |
|---|---|
| Wake | NanoWakeWord |
| VAD | Silero |
| STT | faster-whisper `large-v3-turbo`, CUDA, float16 |
| TTS | Kokoro `hexgrad/Kokoro-82M`, `ef_dora`, CUDA |
| Playback | `pw-play` |

Roger keeps a strict split between written output and spoken output. Preview, overlay, CLI, task logs, and retry/debug context keep the canonical text exactly as pi produced it. When TTS is enabled, Roger marks pi RPC prompts with Roger speech metadata so `pi-router` can return structured output: `display_text` for visible UI/logs and Spanish `speech_text` for Kokoro. Model-backed naturalization happens through pi-agent/pi-router, not through direct Roger llama.cpp calls. If structured speech metadata is absent, Roger only applies deterministic local cleanup for Markdown, times, and common Anglicisms. For example, Roger may show `Son las **10:30 am**. Revisa el README en GitHub.` while speaking “Son las diez y treinta de la mañana. Revisa el ridmi en guit jab.”

Kokoro prosody controls are limited to what the local API supports: voice, comma-separated voice blends when assets are available, speed, and split pattern. Roger does not claim direct Kokoro emotion/tone/style support; style profiles are implemented through phrasing and supported speed/voice settings.

### pi-agent execution

Roger dispatches accepted instructions to pi-agent instead of implementing task execution itself.

Current sessions:

| Session | Purpose | Default cwd |
|---|---|---|
| `system` | Laptop/system tasks | `$HOME` |
| `current-project` | Active project/code tasks | project dir |

Examples:

```bash
uv run roger task --session system "dime la fecha de hoy"
uv run roger task --session current-project "corre los tests"
```

If no session is forced, Roger routes the task by configured routing rules.

### Online/default model and offline llama.cpp fallback

Online mode leaves pi’s configured default model untouched.

Offline/fallback mode uses the local pi custom provider:

| Setting | Value |
|---|---|
| Provider | `llama-cpp` |
| Model | `gemma4` |
| Base URL | `http://127.0.0.1:11434/v1` |
| Default port | `11434` |

Offline pi launch args include:

```bash
pi --mode rpc --offline --provider llama-cpp --model gemma4
```

Roger checks the llama.cpp `/v1/models` endpoint before local dispatch and reports clear failures when the server or model is unavailable.

Expected local server wrapper:

```bash
llama-gemma4-server --no-warmup
```

A generic CUDA wrapper is also available locally on this machine:

```bash
llama-server-cuda --list-devices
```

### llama.cpp GPU runtime

The local llama.cpp build is CUDA-enabled and should detect the RTX GPU:

```bash
llama-gemma4-server --list-devices
# CUDA0: NVIDIA GeForce RTX 4080 Laptop GPU ...
```

The `gemma4` server wrapper uses:

- context: `8192`
- GPU layers: `99`
- port: `11434`
- local model registry: `~/.config/llama.cpp/models.json`
- model files: `~/.local/share/llama.cpp/models/`

### Omarchy/Hyprland overlay UX

Roger uses a Wayland layer-shell overlay as the definitive user-facing status surface. Notifications via `notify-send` are opt-in:

```bash
uv run roger daemon --desktop-notifications
```

Overlay phases include:

- listening/wake active
- instruction capture
- transcription
- dispatching
- completion/failure
- goodbye/no-input quick close

### Resilience and hardening

Roger includes:

- automatic online/offline model availability policy
- explicit `--offline` mode
- bounded offline pi RPC event timeout
- llama.cpp preflight checks
- empty-response handling
- local model chat-template cleanup
- safe TTS boundary: TTS/playback failures do not change task completion status
- degraded TTS warnings with rate limiting
- daemon error isolation so a failed cycle does not kill the daemon

### Task progress logs

Each pi-agent task gets a structured JSONL log under:

```text
.roger/logs/
```

The typed CLI prints a log path when available:

```text
log: .roger/logs/<timestamp>-system.jsonl
```

Logs include:

- instruction
- session
- selected model mode (`online` or `offline-fallback`)
- start/completion/failure events
- assistant text deltas
- tool execution start/update/end events
- prompt rejection and error details

### Cancellation

Roger recognizes stop phrases such as:

```text
para Roger
cancela Roger
detente Roger
stop Roger
```

For CLI/control use:

```bash
uv run roger cancel --session system
uv run roger cancel --session current-project --command abort_bash
uv run roger cancel --session system --command abort_retry
```

Cancellation reports whether the abort command was accepted separately from final task state.

### Configurable routing

Routing domains are registry/config driven. You can add new domains without changing the voice pipeline.

Example `roger.toml` snippet:

```toml
[sessions.notes]
cwd = "/home/user/Notes"
description = "Personal notes"
routing_keywords = ["nota", "notas"]
reuse_session = true
```

Dry-run route diagnostics:

```bash
uv run roger route "corre los tests"
```

Example output:

```text
Roger route result
status: routed
session: current-project
matched rule: keyword:tests
confidence: high
reason: matched routing keyword for current-project
```

## Setup

Create/sync the development environment with uv:

```bash
uv sync --group speech
```

Basic health check:

```bash
uv run roger health
```

Current health output reports:

- wake backend/model settings
- VAD/STT/TTS backends
- STT/TTS CUDA devices/settings
- online/offline model config
- automatic fallback flags
- llama.cpp base URL and timeout
- configured sessions
- routing config validity

## Common Commands

### Typed task

```bash
uv run roger task --session system --offline --no-tts --no-overlay "responde exactamente: ok"
```

### One-shot voice cycle

```bash
uv run roger listen-once
```

Useful debug flags:

```bash
uv run roger listen-once --wake-debug --wake-debug-min-score 0.0
uv run roger listen-once --manual-wake --no-tts --console-feedback
```

### Daemon

```bash
uv run roger daemon
```

Controlled smoke:

```bash
uv run roger daemon --manual-wake --max-cycles 1 --offline --no-tts --no-overlay --console-feedback
```

### Say text with Kokoro

```bash
uv run roger say "Hola, soy Roger."
```

### Overlay demo

```bash
uv run roger overlay-demo --transcript "corre pwd" --result "Listo" --duration 5
```

### Wake file scoring

```bash
arecord -f S16_LE -r 16000 -c 1 -d 3 /tmp/hola-roger.wav
uv run roger wake-file /tmp/hola-roger.wav --wake-threshold 0.85
```

### Autostart on Omarchy/Hyprland

```bash
uv run roger install-autostart
uv run roger uninstall-autostart
```

This manages the Roger daemon block in:

```text
~/.config/hypr/autostart.lua
```

## Verification

Run the full Python test suite:

```bash
uv run --group speech python -m unittest discover -s tests
```

Validate OpenSpec specs:

```bash
openspec validate --specs --strict
```

Validate an active change when working on one:

```bash
openspec validate <change-name> --strict
```

## Local Files and State

Important local/runtime paths:

| Path | Purpose |
|---|---|
| `.roger/daemon.pid` | daemon pid |
| `.roger/daemon.log` | daemon log |
| `.roger/logs/` | task JSONL logs |
| `.roger/pi-sessions/` | Roger pi RPC session dirs |
| `models/` | local model artifacts, ignored by git |
| `~/.config/llama.cpp/models.json` | llama.cpp model registry |
| `~/.pi/agent/models.json` | pi custom provider config |

## Troubleshooting Quick Checks

```bash
uv run roger health
llama-gemma4-server --list-devices
curl -fsS http://127.0.0.1:11434/v1/models
pi --list-models llama-cpp
uv run roger task --session system --offline --no-tts --no-overlay "responde exactamente: ok"
uv run roger say "Hola, soy Roger."
```

If TTS fails, Roger should continue text-only and keep task results visible. Use `--no-tts` for temporary text-only operation.

If `llama-server` fails with missing shared libraries, use the local wrappers such as `llama-gemma4-server` or `llama-server-cuda`; they set the needed `LD_LIBRARY_PATH` without exporting it globally.
