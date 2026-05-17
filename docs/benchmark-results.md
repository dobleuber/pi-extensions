# Benchmark Results and Defaults

This document records the current default decisions and what still requires empirical measurement.

## Current defaults

| Area | Default | Fallback / baseline | Status |
|---|---|---|---|
| Wake word | NanoWakeWord candidate set: GRU, LSTM, TCN | Manual trigger, then openWakeWord if needed | Training configs generated; no real audio benchmark yet |
| VAD | Silero VAD | WebRTC VAD | Benchmark plan implemented; no real audio benchmark yet |
| STT | faster-whisper | whisper.cpp | Benchmark plan implemented; no real audio benchmark yet |
| TTS | Kokoro | Piper | Benchmark plan implemented; no real audio benchmark yet |
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
43 tests passing
OpenSpec validation passing
uv speech dependency group installed successfully
```
