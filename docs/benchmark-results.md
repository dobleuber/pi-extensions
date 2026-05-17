# Benchmark Results and Defaults

This document records the current default decisions and what still requires empirical measurement.

## Current defaults

| Area | Default | Fallback / baseline | Status |
|---|---|---|---|
| Wake word | NanoWakeWord LSTM model at `models/wake/nanowakeword/hola_roger_lstm/model/hola_roger_lstm.onnx` | Manual trigger, then openWakeWord if needed | Model loads and listener smoke-tested; no real audio benchmark yet |
| VAD | Silero VAD | WebRTC VAD | Silence smoke test passed with no speech timestamps |
| STT | faster-whisper | whisper.cpp | Tiny model silence transcription smoke test passed |
| TTS | Kokoro | Piper | Spanish synthesis smoke test passed with `ef_dora` |
| pi integration | RPC | SDK later if needed | Unit-tested fake RPC client |
| Online model | pi default | n/a | Implemented as no explicit model args |
| Offline model | Ollama | n/a | Args implemented; requires local Ollama server/model |

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
74 tests passing
OpenSpec validation passing
uv speech dependency group installed successfully
NanoWakeWord LSTM model load/listener smoke test passing
User live-tested the LSTM model and reported it works well
Silero VAD silence smoke test returns no speech timestamps
faster-whisper tiny silence transcription smoke test returns empty text
Kokoro `ef_dora` Spanish synthesis smoke test produced audio bytes at 24 kHz
pi RPC `get_state` smoke test returned the configured default model and session state
`roger listen-once --manual-wake --preview-action cancel --no-tts` smoke test passed without dispatching and prints phase feedback/transcription
`roger listen-once` supports clean Ctrl+C, quiet wake waiting by default, `--wake-debug`, and per-run `--wake-threshold`
`roger wake-file` scores recorded WAV files with the same wake adapter/detection rule as listen-once
```
