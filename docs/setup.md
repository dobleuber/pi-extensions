# Roger Setup

Roger is currently a Python-first scaffold with local speech backend adapters and pi-agent RPC integration.

## Development environment

Use uv for Python and environment management. The project constrains Python to `>=3.11,<3.13` because several speech/ML packages commonly lag the latest Python releases.

```bash
uv sync
```

Optional speech dependencies are grouped under `speech`:

```bash
uv sync --group speech
```

Run tests:

```bash
uv run python -m unittest discover -s tests
```

Run OpenSpec validation:

```bash
openspec validate add-roger-voice-laptop-interface --strict
```

## Wake word: NanoWakeWord

The first wake-word spike targets:

```text
hola roger
```

Only these NanoWakeWord architectures are in scope:

- GRU
- LSTM
- TCN

Generate training configs:

```bash
PYTHONPATH=src python3 -m roger.cli spike wake --write-configs --output-dir configs/nanowakeword
```

Generated configs are committed under `configs/nanowakeword/` for reproducibility. See `docs/wake-nanowakeword-spike.md` for training and benchmark guidance.

Current selected local model path:

```text
models/wake/nanowakeword/hola_roger_lstm/model/hola_roger_lstm.onnx
```

Live listener smoke test:

```bash
uv run python scripts/nanowakeword/listen_hola_roger.py --duration 5 --min-print-score 0.2
```

## VAD

Default scaffold: Silero VAD.
Fallback/baseline: WebRTC VAD.

The expected audio normalization boundary is 16 kHz mono 16-bit PCM.

Dry-run the VAD spike:

```bash
PYTHONPATH=src python3 -m roger.cli spike vad --dry-run
```

## STT

Default scaffold: faster-whisper, multilingual `base`, Spanish language (`es`).
Fallback/baseline: whisper.cpp.

Dry-run the STT spike:

```bash
PYTHONPATH=src python3 -m roger.cli spike stt --dry-run
```

## TTS

Default scaffold: Kokoro.
Fallback/baseline: Piper.

Dry-run the TTS spike:

```bash
PYTHONPATH=src python3 -m roger.cli spike tts --dry-run
```

## pi-agent RPC

Roger uses pi RPC as the first integration path:

```bash
pi --mode rpc
```

The implemented `PiRpcClient` can start an RPC process, send JSONL prompts, read streamed events, collect text deltas, and terminate the process.

## Ollama fallback

Online mode leaves pi's configured default model untouched.
Offline mode builds pi args like:

```bash
pi --mode rpc --provider ollama --model <configured-ollama-model>
```

Ollama must be running separately:

```bash
ollama serve
```

Roger reports offline fallback unavailability instead of silently dropping tasks.
