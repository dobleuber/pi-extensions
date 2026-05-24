# Research: Local VAD options for instruction capture — Silero VAD vs WebRTC VAD

## Summary
Silero VAD is the better default for local instruction capture when accuracy in noisy rooms and tunable endpointing matter; use its ONNX/PyTorch Python API at 16 kHz mono and finalize after a configurable silence window. WebRTC VAD is a very small, deterministic C VAD with Python bindings and strict frame constraints; it is ideal as a low-CPU first gate or fallback, but needs extra hangover/ring-buffer logic to avoid clipped commands.

## Findings
1. **Python integration: Silero is straightforward and supports offline CPU inference.** Install via `pip install silero-vad`, then load helpers with `load_silero_vad()` / `read_audio()` / `get_speech_timestamps()` or run streaming with `VADIterator`; ONNX Runtime is available for lightweight local deployment. For this project, prefer ONNX if packaging on Raspberry Pi or other constrained devices. [Silero VAD GitHub](https://github.com/snakers4/silero-vad), [Silero VAD PyPI](https://pypi.org/project/silero-vad/)

2. **Python integration: WebRTC VAD uses frame-by-frame boolean decisions.** The common Python package exposes `webrtcvad.Vad(mode)` and `vad.is_speech(frame, sample_rate)`; mode `0` is least aggressive and mode `3` is most aggressive. It does not return probabilities or timestamps, so the application must aggregate frame decisions into speech segments. [py-webrtcvad README](https://github.com/wiseman/py-webrtcvad)

3. **Audio format constraints differ and should be normalized at the capture boundary.** Silero expects mono audio at 8 kHz or 16 kHz, with streaming chunks of 256 samples at 8 kHz or 512 samples at 16 kHz. WebRTC VAD requires 16-bit mono PCM, sample rates of 8/16/32/48 kHz, and exactly 10/20/30 ms frames. Recommendation: capture/resample to **16 kHz, mono, 16-bit PCM**, then feed 512-sample chunks to Silero or 20/30 ms frames to WebRTC. [Silero VAD GitHub](https://github.com/snakers4/silero-vad), [py-webrtcvad README](https://github.com/wiseman/py-webrtcvad)

4. **Endpointing strategy: use hysteresis, padding, and a minimum-silence finalizer.** Silero already exposes endpointing controls such as `threshold`, `min_speech_duration_ms`, `max_speech_duration_s`, `min_silence_duration_ms`, and `speech_pad_ms`; for instruction capture start with `threshold≈0.5`, `min_speech_duration_ms=150–250`, `min_silence_duration_ms=500–800`, and `speech_pad_ms=100–300`, then tune against clipped/overlong commands. WebRTC should follow the example ring-buffer pattern: trigger when ~90% of recent frames are voiced and stop when ~90% are unvoiced, with ~300 ms padding/hangover as a baseline. [Silero VAD source/README](https://github.com/snakers4/silero-vad), [py-webrtcvad example](https://github.com/wiseman/py-webrtcvad/blob/master/example.py)

5. **Benchmark metrics for instruction capture should focus on user-visible failures, not just VAD accuracy.** Track: start latency, end latency after last word, clipped-start rate, clipped-end rate, false command-window activations per hour, missed instruction rate, accepted non-speech/noise segments, median/p95 segment duration overhead, CPU %, memory, and real-time factor. Silero advertises fast CPU inference, roughly sub-millisecond per 30+ ms audio chunk on a single CPU thread, making it practical for always-on local use; WebRTC is also very low overhead but lacks probability scores and built-in timestamp generation. [Silero VAD GitHub](https://github.com/snakers4/silero-vad), [py-webrtcvad README](https://github.com/wiseman/py-webrtcvad)

6. **Recommended architecture for this project.** Implement a VAD abstraction with normalized 16 kHz mono PCM input. Default backend: Silero ONNX for endpointing and timestamps. Optional backend: WebRTC VAD mode 1–2 for minimal CPU or as a pre-filter before Silero/ASR. Keep 200–500 ms pre-roll audio so wake/instruction starts are not clipped, and finalize an instruction only after the chosen VAD reports sustained silence.

## Sources
- Kept: Silero VAD GitHub (https://github.com/snakers4/silero-vad) — primary implementation docs for Python loading, supported sample rates, chunk sizes, timestamp utilities, streaming iterator, and performance claims.
- Kept: Silero VAD PyPI (https://pypi.org/project/silero-vad/) — package/install reference for Python integration.
- Kept: py-webrtcvad README (https://github.com/wiseman/py-webrtcvad) — primary Python binding docs for WebRTC VAD constraints: PCM format, sample rates, frame durations, and aggressiveness modes.
- Kept: py-webrtcvad example.py (https://github.com/wiseman/py-webrtcvad/blob/master/example.py) — practical endpointing/ring-buffer pattern using 90% voiced/unvoiced decisions and padding.
- Dropped: SEO/blog summaries of VAD libraries — redundant with primary repos and usually omit strict audio constraints.
- Dropped: Generic ASR endpointing articles — useful conceptually but less actionable than the backend-specific controls above.

## Gaps
No project-specific benchmark numbers exist yet. Next step: record a small local instruction corpus with quiet room, fan/noise, distance, and overlap conditions; run both backends with fixed settings; report clipped-start/end rates, false activations/hour, miss rate, end latency p50/p95, and CPU/RAM on the target device.
