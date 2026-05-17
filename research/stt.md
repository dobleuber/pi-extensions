# Research: Local Spanish STT options — faster-whisper and whisper.cpp

## Summary
For local Spanish command recognition, prefer multilingual Whisper models (not `.en`) with `language="es"`, short audio windows, VAD, greedy decoding, and a command/intents matcher after transcription. `faster-whisper` is easiest from Python and usually fastest on CUDA or x86 CPU with int8; `whisper.cpp` is the most portable CLI/C++ option and is attractive for Arch/Linux, Raspberry Pi-like deployments, and quantized CPU inference.

## Findings
1. **Best integration split: Python service = faster-whisper; standalone/local CLI = whisper.cpp.** `faster-whisper` is a Python library built on CTranslate2 and exposes `WhisperModel.transcribe(...)`; it is not primarily a CLI tool, so use it through a small Python wrapper/service. `whisper.cpp` builds a native `whisper-cli`/examples binary and can be called directly from shell/subprocess. [faster-whisper](https://github.com/SYSTRAN/faster-whisper) [whisper.cpp](https://github.com/ggml-org/whisper.cpp)

2. **faster-whisper Python pattern for Spanish commands.** Use multilingual model names such as `tiny`, `base`, or `small`; set `language="es"`, `task="transcribe"`, `beam_size=1` for latency, `condition_on_previous_text=False` for independent commands, and optionally `vad_filter=True`. Example:
   ```python
   from faster_whisper import WhisperModel
   model = WhisperModel("base", device="cpu", compute_type="int8")
   segments, info = model.transcribe(
       "cmd.wav", language="es", task="transcribe",
       beam_size=1, vad_filter=True, condition_on_previous_text=False,
       temperature=0.0,
   )
   text = " ".join(s.text.strip() for s in segments)
   ```
   The README documents CTranslate2-backed inference, CPU/GPU compute types, VAD, batching, and model loading. [Source](https://github.com/SYSTRAN/faster-whisper)

3. **faster-whisper CLI approach.** If a CLI is required, either wrap the Python API above, or evaluate `whisper-ctranslate2`, a CLI around CTranslate2/Whisper-style models. Keep the wrapper thin so this project can enforce Spanish language, command timeout, VAD policy, and output JSON. [whisper-ctranslate2](https://github.com/Softcatala/whisper-ctranslate2)

4. **whisper.cpp CLI pattern.** Build from source, download a multilingual model, then run with Spanish forced:
   ```bash
   git clone https://github.com/ggml-org/whisper.cpp
   cd whisper.cpp
   cmake -B build
   cmake --build build -j --config Release
   sh ./models/download-ggml-model.sh base
   ./build/bin/whisper-cli -m models/ggml-base.bin -f cmd.wav -l es -t 4
   ```
   For live microphone/streaming, use the project’s stream examples or call `whisper-cli` on short captured WAV chunks and parse stdout/text output. [Source](https://github.com/ggml-org/whisper.cpp)

5. **Arch/Linux install constraints.** Use a project venv for Python because Arch discourages system-wide `pip`; install build tools with `pacman -S --needed base-devel cmake git python python-pip`. For `faster-whisper`, `pip install faster-whisper` usually avoids a separate FFmpeg install because PyAV bundles FFmpeg libraries, but CTranslate2 wheels/CPU features are the real constraint. For `whisper.cpp`, install `cmake`/compiler; install `sdl2` only if using microphone streaming examples. [Arch Python package guidelines](https://wiki.archlinux.org/title/Python/Package_guidelines) [faster-whisper](https://github.com/SYSTRAN/faster-whisper) [whisper.cpp](https://github.com/ggml-org/whisper.cpp)

6. **GPU/CUDA constraints favor version pinning.** Recent CTranslate2/faster-whisper releases have specific CUDA/cuDNN expectations; if using NVIDIA, pin versions according to the faster-whisper README/CTranslate2 install docs. For CPU-only Arch deployments, start with `compute_type="int8"`; for CUDA, test `float16` and `int8_float16`. [faster-whisper GPU notes](https://github.com/SYSTRAN/faster-whisper) [CTranslate2 installation](https://opennmt.net/CTranslate2/installation.html)

7. **Model recommendation for low-latency Spanish commands.** Start with `base` multilingual as the default quality/latency point. Use `tiny` only if latency is more important than accent/noise robustness; use `small` if `base` misses commands and latency budget permits. Avoid `.en` models because Spanish requires multilingual Whisper checkpoints. For whisper.cpp, test quantized `base`/`small` variants such as q5/q8 before very low-bit quantization. [OpenAI Whisper model list](https://github.com/openai/whisper) [whisper.cpp models](https://github.com/ggml-org/whisper.cpp)

8. **Command UX matters more than raw WER.** For a fixed Spanish command set, measure intent accuracy and false accept/reject rate, then normalize transcripts with lowercase, accent folding, punctuation removal, and fuzzy command matching. Whisper may output semantically correct but not exact strings; do not rely only on exact transcript equality. Use `initial_prompt`/allowed vocabulary only as a hint, not a hard grammar. [faster-whisper transcription options](https://github.com/SYSTRAN/faster-whisper)

9. **Benchmark metrics to collect.** For each engine/model/compute setting, collect: model load time; audio duration; wall-clock transcription time; real-time factor `RTF = transcribe_seconds / audio_seconds`; end-to-end command latency from speech end to command decision; peak RSS memory; CPU%; thread count; model size on disk; energy/temperature if on Pi/laptop; WER/CER on Spanish samples; command intent accuracy; false accept/false reject; and behavior under background noise. CTranslate2 documents quantization tradeoffs, and whisper.cpp includes benchmarking-oriented native builds/examples. [CTranslate2 quantization](https://opennmt.net/CTranslate2/quantization.html) [whisper.cpp](https://github.com/ggml-org/whisper.cpp)

10. **Suggested first benchmark matrix.** Test: `faster-whisper` `tiny/base/small` with CPU `int8`, `beam_size=1`; if NVIDIA exists, also `small` with `float16` and `int8_float16`. Test `whisper.cpp` `tiny/base/small` multilingual with 2/4/physical-core thread counts and q5/q8 quantization. Use 30–100 Spanish command clips, including silence/no-command clips and noisy variants.

## Sources
- Kept: SYSTRAN faster-whisper (https://github.com/SYSTRAN/faster-whisper) — primary docs for Python API, VAD, batching, compute types, FFmpeg/PyAV note, CUDA notes, and benchmarks.
- Kept: ggml-org whisper.cpp (https://github.com/ggml-org/whisper.cpp) — primary docs for native CLI, build process, model downloads, quantized/local inference, and streaming examples.
- Kept: CTranslate2 installation (https://opennmt.net/CTranslate2/installation.html) — dependency/runtime constraints behind faster-whisper.
- Kept: CTranslate2 quantization (https://opennmt.net/CTranslate2/quantization.html) — explains int8/float16 quantization options to benchmark.
- Kept: OpenAI Whisper repo/model card (https://github.com/openai/whisper) — canonical model sizes and multilingual vs English-only model distinction.
- Kept: Softcatala whisper-ctranslate2 (https://github.com/Softcatala/whisper-ctranslate2) — practical CLI option when faster-whisper-like CTranslate2 inference is desired from shell.
- Kept: Arch Linux Python packaging guidance (https://wiki.archlinux.org/title/Python/Package_guidelines) — supports venv/pip isolation guidance on Arch.
- Dropped: Generic blog posts and SEO benchmark pages — less authoritative than upstream READMEs/docs and often stale across Whisper/CTranslate2 releases.

## Gaps
- I could not run live web search or local benchmarks in this environment; verify current package versions before pinning CUDA/CTranslate2 on the target machine.
- Actual model choice depends on target hardware and microphone/noise conditions. Next step: implement a small benchmark harness that records the metrics above and tests `tiny`, `base`, and `small` on this project’s real Spanish command list.
