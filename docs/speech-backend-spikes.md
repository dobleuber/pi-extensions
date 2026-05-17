# Speech Backend Spikes

Roger keeps VAD, STT, and TTS behind adapters. These spikes select defaults and record the metrics needed before wiring the full voice loop.

## VAD: Silero vs WebRTC

Default selected for MVP scaffolding: **Silero VAD**.

Reasoning:

- Better endpointing controls and probability/timestamp APIs.
- More robust for noisy laptop environments.
- WebRTC remains a very small fallback or pre-filter.

Initial Silero thresholds:

- `threshold`: `0.5`
- `min_speech_duration_ms`: `200`
- `min_silence_duration_ms`: `700`
- `speech_pad_ms`: `200`
- `max_capture_seconds`: `30`

Metrics to record:

- start latency;
- p50/p95 end latency;
- clipped-start and clipped-end rates;
- false command windows per hour;
- missed instruction rate;
- CPU and RSS memory.

## STT: faster-whisper vs whisper.cpp

Default selected for MVP scaffolding: **faster-whisper** with multilingual `base`, `language="es"`, CPU `int8` first.

Reasoning:

- Python-native integration for the first Roger daemon.
- Strong Whisper transcription quality for Spanish.
- `whisper.cpp` remains the portability/CLI fallback.

Initial faster-whisper options:

```python
{
  "language": "es",
  "task": "transcribe",
  "beam_size": 1,
  "condition_on_previous_text": False,
  "temperature": 0.0,
}
```

Models to compare:

- `tiny`
- `base`
- `small`

Metrics to record:

- model load time;
- transcription time;
- real-time factor;
- speech-end-to-text latency;
- peak RSS and CPU;
- WER/CER on Spanish samples;
- intent accuracy;
- false accept/reject rate.

## TTS: Kokoro vs Piper

Default selected for MVP scaffolding: **Kokoro**.

Reasoning:

- Strong local quality candidate for Spanish assistant responses.
- Python-first integration aligns with the daemon.
- Piper remains the low-resource fallback/baseline, especially if Kokoro latency or dependencies are too heavy.

Kokoro voices to try:

- `ef_dora`
- `em_alex`
- `em_santa`

Piper voices to try:

- `es_ES-davefx-medium`
- `es_MX-ald-medium`

Metrics to record:

- cold start;
- warm synthesis time;
- time to first audio;
- output audio duration;
- real-time factor;
- peak RSS and CPU;
- subjective voice quality;
- package/model status and license verification;
- offline behavior.

## Programmatic plans

The current benchmark matrices are available from:

```python
from roger.benchmarks.speech import build_vad_plan, build_stt_plan, build_tts_plan
```
