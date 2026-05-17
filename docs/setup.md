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

## Optional backend smoke checks

Silero VAD silence check:

```bash
uv run python - <<'PY'
from roger.backends.interfaces import AudioSegment
from roger.backends.vad_silero import SileroVadAdapter
print(SileroVadAdapter().detect_speech(AudioSegment(pcm16=b'\\x00\\x00' * 16000)))
PY
```

faster-whisper tiny silence check:

```bash
uv run python - <<'PY'
import tempfile, wave
from pathlib import Path
from roger.backends.interfaces import AudioSegment
from roger.backends.stt_faster_whisper import FasterWhisperSttAdapter
path = Path(tempfile.gettempdir()) / 'roger_silence.wav'
with wave.open(str(path), 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(b'\\x00\\x00' * 16000)
print(repr(FasterWhisperSttAdapter(model='tiny').transcribe(AudioSegment(path=path)).text))
PY
```

Kokoro Spanish synthesis check:

```bash
uv run python - <<'PY'
from roger.backends.tts_kokoro import KokoroTtsAdapter
speech = KokoroTtsAdapter(voice='ef_dora').synthesize('Hola Roger.')
print(len(speech.audio or b''), speech.sample_rate)
PY
```

## One-cycle CLI

A safe CLI smoke test that does not dispatch to pi-agent:

```bash
uv run roger listen-once --manual-wake --preview-action cancel --no-tts
```

This prints feedback only after wake activation, then instruction capture, transcription text, and final result. While waiting for the real wake word it stays quiet by default.

A real one-cycle run uses the configured wake/VAD/STT/pi/TTS path:

```bash
uv run roger listen-once
```

For early testing, keep `--no-tts` if you only want textual output. Without `--no-tts`, Roger plays the synthesized Kokoro response through the local audio output.

Roger uses Kokoro local files by default (`speech.tts.local_files_only = true`) and resolves the model from the Hugging Face cache without network calls. If needed, pin explicit paths in `roger.toml`:

```toml
[speech.tts]
backend = "kokoro"
voice = "ef_dora"
repo_id = "hexgrad/Kokoro-82M"
local_files_only = true
config_path = "~/.cache/huggingface/hub/models--hexgrad--Kokoro-82M/snapshots/<revision>/config.json"
model_path = "~/.cache/huggingface/hub/models--hexgrad--Kokoro-82M/snapshots/<revision>/kokoro-v1_0.pth"
voice_path = "~/.cache/huggingface/hub/models--hexgrad--Kokoro-82M/snapshots/<revision>/voices/ef_dora.pt"
```

To validate real pi-agent execution without microphone/STT uncertainty, use a typed task:

```bash
uv run roger task --session current-project --no-tts "corre pwd y dime el directorio actual"
```

For OS-level feedback, Roger sends desktop notifications with `notify-send` when available for wake activation, capture, transcription, dispatch, and completion. Console output remains as a fallback/diagnostic surface.

If the real wake word appears to hang, print model scores and lower the threshold for that run:

```bash
uv run roger listen-once --no-tts --wake-debug --wake-debug-min-score 0.0 --wake-threshold 0.75
```

The default wake threshold is `0.85`, matching the standalone listener script. Roger also detects by `score >= threshold`, matching that script's detection rule.
Pressing `Ctrl+C` exits cleanly without a traceback.

To debug with a recording instead of live microphone input:

```bash
arecord -f S16_LE -r 16000 -c 1 -d 3 /tmp/hola-roger.wav
uv run roger wake-file /tmp/hola-roger.wav --wake-threshold 0.85
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
