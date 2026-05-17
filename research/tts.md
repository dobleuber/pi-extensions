# Research: Local Spanish TTS options — Kokoro and Piper

## Summary
For a local Spanish TTS feature, **Piper is the safer production/Raspberry Pi choice**: small ONNX voices, stable CLI, easy raw/WAV output, and official Spanish models. **Kokoro is the higher-quality/newer option** with a small 82M multilingual model and Spanish voices, but Spanish support and APIs are newer, dependencies are heavier, and local latency should be validated on target hardware.

## Findings
1. **Piper has the cleanest CLI path for this project** — install `piper-tts` or use the release binary, download an `.onnx` model plus matching `.onnx.json`, then run `echo "Hola" | piper --model es_ES-...onnx --output_file out.wav`; raw audio can be streamed to `aplay` for low-overhead playback. [Piper README](https://github.com/rhasspy/piper) / [PyPI](https://pypi.org/project/piper-tts/)

2. **Piper Python integration is available but CLI/subprocess is often simpler** — the package exposes `piper.voice.PiperVoice` for direct synthesis, but the CLI is better documented and isolates native dependency issues. Actionable integration: start with subprocess CLI, then move to `PiperVoice.load(model_path).synthesize(text, wav_file)` only if process startup becomes measurable. [Piper Python README/source](https://github.com/rhasspy/piper/tree/master/src/python_run)

3. **Piper Spanish model availability is strong** — official voice repository includes Spain Spanish voices such as `es_ES-carlfm-x_low`, `es_ES-davefx-medium`, `es_ES-mls_10246-low`, `es_ES-mls_9972-low`, `es_ES-sharvard-medium`, plus Mexican Spanish `es_MX-ald-medium`. Use medium voices first for intelligibility; use low/x_low only if Pi latency dominates. [Piper voices repository](https://huggingface.co/rhasspy/piper-voices/tree/main/es)

4. **Piper license/status gotchas** — Piper code is MIT-licensed, but model/voice licensing is per-voice/dataset, so check each model card/config before redistribution. The original `rhasspy/piper` repo has seen low maintenance/archival status in recent years, but the binaries/models remain widely used by Home Assistant/Rhasspy-style local voice stacks. [Piper GitHub](https://github.com/rhasspy/piper) / [Piper voices HF](https://huggingface.co/rhasspy/piper-voices)

5. **Piper latency expectation** — designed for local/embedded use and real-time CPU synthesis, including Raspberry Pi-class hardware. Expect first-run/model-load cost, then sentence synthesis generally near or faster than real time for low/medium voices on Pi 4/5; measure with real-time factor, `RTF = synthesis_seconds / output_audio_seconds`, and target `< 1.0`. [Piper README](https://github.com/rhasspy/piper)

6. **Kokoro has a straightforward Python API** — install the package, create a `KPipeline(lang_code='e')` for Spanish, choose a Spanish voice such as `ef_dora`, `em_alex`, or `em_santa`, and write the generated 24 kHz audio with `soundfile`. This is a good fit if the project is already Python-first and can tolerate PyTorch/ML dependencies. [Kokoro model card](https://huggingface.co/hexgrad/Kokoro-82M) / [Kokoro repo](https://github.com/hexgrad/kokoro)

7. **Kokoro CLI/local-server path is less canonical than Piper** — for command-line or lighter deployment, use ONNX community packaging such as `kokoro-onnx`, which provides local ONNX Runtime inference and examples. Treat this as an integration layer to pin and test, because it is separate from the core Kokoro model release. [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) / [PyPI kokoro-onnx](https://pypi.org/project/kokoro-onnx/)

8. **Kokoro Spanish availability exists but is narrower** — Kokoro-82M is multilingual and includes Spanish language code/voices, but the Spanish voice set is much smaller than Piper’s catalog. Use it if quality/naturalness beats Piper in your own samples; keep Piper as fallback for predictable embedded operation. [Kokoro model card](https://huggingface.co/hexgrad/Kokoro-82M)

9. **Kokoro license/status gotchas** — Kokoro-82M is published as an open-weight 82M parameter TTS model, commonly listed under Apache-2.0 on Hugging Face, but downstream voice packs, wrappers, and ONNX conversions should be checked individually. The project is newer and fast-moving, so pin exact versions of `kokoro`, `misaki`, `torch`/`onnxruntime`, and voice assets. [Kokoro HF](https://huggingface.co/hexgrad/Kokoro-82M) / [Kokoro GitHub](https://github.com/hexgrad/kokoro)

10. **Kokoro latency expectation** — the 82M model is small for neural TTS and should be usable locally on modern CPUs; ONNX is preferable for Pi-class deployments. Expect higher cold-start and dependency overhead than Piper, but potentially better voice quality. Benchmark both PyTorch and ONNX paths on the target Pi before committing. [Kokoro HF](https://huggingface.co/hexgrad/Kokoro-82M) / [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx)

11. **Benchmark metric to collect for both** — record cold start, warm start, time-to-first-audio if streaming, full synthesis time, output duration, memory RSS, and RTF. Test at least: short prompt `"Hola, ¿cómo estás?"`, medium assistant response ~20 words, and long paragraph ~100 words. Piper should be evaluated per voice quality (`x_low`, `low`, `medium`); Kokoro should be evaluated per wrapper (`kokoro` PyTorch vs `kokoro-onnx`).

## Recommended decision
- **Default implementation:** Piper CLI with `es_ES-davefx-medium` or `es_MX-ald-medium`, depending on accent target.
- **Quality experiment:** Kokoro Spanish via Python/ONNX; keep if subjective quality is clearly better and RTF on the target machine is acceptable.
- **Fallback policy:** ship Piper first; expose Kokoro as optional/provider-configurable after local benchmarks.

## Sources
- Kept: Piper GitHub (https://github.com/rhasspy/piper) — official CLI, install, license/status, embedded positioning.
- Kept: Piper PyPI (https://pypi.org/project/piper-tts/) — package/install reference.
- Kept: Piper voices on Hugging Face (https://huggingface.co/rhasspy/piper-voices/tree/main/es) — authoritative Spanish model list.
- Kept: Kokoro-82M Hugging Face (https://huggingface.co/hexgrad/Kokoro-82M) — model license, size, multilingual/voice info.
- Kept: Kokoro GitHub (https://github.com/hexgrad/kokoro) — Python usage and voice/language conventions.
- Kept: kokoro-onnx (https://github.com/thewh1teagle/kokoro-onnx) — practical ONNX/Python/CLI deployment route.

## Gaps
- No single public benchmark fairly compares Piper Spanish voices and Kokoro Spanish on Raspberry Pi-class hardware. Next step: run an in-project benchmark harness and save per-provider RTF/RSS/cold-start numbers.
- Voice licensing should be verified for the exact selected Piper/Kokoro voice files before redistribution or commercial packaging.
