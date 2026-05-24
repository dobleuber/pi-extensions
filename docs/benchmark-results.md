# Benchmark Results and Defaults

This document records the current default decisions and what still requires empirical measurement.

## Current defaults

| Area | Default | Fallback / baseline | Status |
|---|---|---|---|
| Wake word | NanoWakeWord LSTM model at `models/wake/nanowakeword/hola_roger_lstm/model/hola_roger_lstm.onnx` | Manual trigger, then openWakeWord if needed | Model loads and listener smoke-tested; no real audio benchmark yet |
| VAD | Silero VAD | WebRTC VAD | Silence smoke test passed with no speech timestamps |
| STT | faster-whisper `large-v3-turbo` on CUDA/float16 | whisper.cpp | Tiny silence smoke passed; default moved to GPU quality mode |
| TTS | Kokoro on CUDA | Piper | Spanish synthesis smoke test passed with `ef_dora`; Roger config sets `speech.tts.device = "cuda"` |
| pi integration | RPC | SDK later if needed | Unit-tested fake RPC client |
| Online model | pi default | n/a | Implemented as no explicit model args |
| Offline model | llama.cpp (`llama-cpp` provider, `gemma4`) | Ollama (deprecated) | Args implemented; requires local llama.cpp server/model |

## Wake-word architecture decision

No final NanoWakeWord architecture has been selected yet because GRU, LSTM, and TCN must be trained and measured on real local audio first. Until that benchmark exists, the safe development fallback is the manual wake trigger adapter. `openWakeWord` remains a fallback only if the NanoWakeWord candidates fail reliability/resource thresholds.

Selection helper:

```python
from roger.benchmarks.wake_benchmark import select_wake_architecture
```

Required metrics:

- false positives per hour;
- false negative rate;
- p95 activation latency;
- idle CPU percent;
- RSS memory;
- training duration.

## Verification evidence

Latest verified commands:

```bash
uv run python -m unittest discover -s tests
openspec validate add-roger-voice-laptop-interface --strict
uv run roger health
uv run roger spike wake --dry-run
uv run roger spike vad --dry-run
uv run roger spike stt --dry-run
uv run roger spike tts --dry-run
```

Current local test evidence from this implementation session:

```text
128 tests passing
OpenSpec validation passing
uv speech dependency group installed successfully
NanoWakeWord LSTM model load/listener smoke test passing
User live-tested the LSTM model and reported it works well
Silero VAD silence smoke test returns no speech timestamps
faster-whisper tiny silence transcription smoke test returns empty text
Roger STT default is faster-whisper `large-v3-turbo` on CUDA with `float16` compute; RTX 4080 Laptop GPU and CTranslate2 CUDA float16 support verified. Roger re-execs voice commands with discovered CUDA library paths when needed so CTranslate2 can load `libcublas.so.12`.
Kokoro `ef_dora` Spanish synthesis smoke test produced audio bytes at 24 kHz
pi RPC `get_state` smoke test returned the configured default model and session state
`roger listen-once --manual-wake --preview-action cancel --no-tts` smoke test passed without dispatching and prints phase feedback/transcription
`roger listen-once` supports clean Ctrl+C, quiet wake waiting by default, `--wake-debug`, and per-run `--wake-threshold`
`roger wake-file` scores recorded WAV files with the same wake adapter/detection rule as listen-once
`roger task --session current-project --no-tts "..."` supports typed real pi-agent dispatch without speech uncertainty
`roger task --no-tts "dame la hora en colombia"` routes to `system` and dispatches successfully
`gracias Roger` is handled as a dialogue-closing phrase: Roger says goodbye, does not dispatch to pi-agent, and closes the overlay quickly
Empty/no-input captures close the overlay quickly and do not dispatch, speak, or run STT; Silero VAD returns empty audio when no speech starts within `no_speech_timeout_seconds`
NanoWakeWord interpreter resets after detection and daemon waits 5 seconds after goodbye/no-input before listening again to avoid immediate reactivation from residual audio
Roger sends OS-level `notify-send` feedback when available and plays Kokoro TTS audio through `sounddevice`
Kokoro TTS defaults to local cached config/model/voice files (`local_files_only = true`) with explicit repo id to avoid implicit HF downloads/warnings
`roger daemon` runs continuous wake/instruction cycles and supports `--max-cycles` plus clean Ctrl+C summaries
`roger overlay-demo` verifies the Siri-like floating overlay, and `listen-once`/`daemon` enable the overlay by default with `--no-overlay` opt-out
On Omarchy/Hyprland, the overlay uses a system-Python `gtk-layer-shell` helper as the definitive Wayland-native feedback surface, defaults to readable 36pt/34pt Pango fonts, keeps transcript/result visible through execution, and falls back to Tk only when layer-shell is unavailable; duplicate `notify-send` notifications are opt-in via `--desktop-notifications`
`roger say "..."` provides an isolated TTS/audio playback smoke command; playback prefers PipeWire `pw-play` on Omarchy and falls back to `sounddevice`
Overlay helper keeps final result visible after the parent CLI exits, so `listen-once`/`task` results do not vanish immediately
`roger daemon` holds each result before the next wake cycle (`--result-hold-seconds`, default 10), speaks clarification/failure messages as well as successful task results, and reports per-cycle errors to the overlay instead of exiting
`roger install-autostart` manages a marked Roger block in `~/.config/hypr/autostart.lua`, creates backups, and validated with `hyprctl reload && hyprctl configerrors`
```
