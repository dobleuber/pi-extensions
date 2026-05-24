# Research: NanoWakeWord custom wake phrase “hola roger”

## Summary
NanoWakeWord custom training should be treated as an audio-classification pipeline: prepare 16 kHz mono positives for the exact phrase, hard negatives/partials, train three separate configs/models (`gru`, `lstm`, `tcn`), then compare exported TFLite/ONNX/Keras artifacts on the target runtime. The largest implementation risks are dependency/version drift in TensorFlow/Keras/TFLite conversion, TCN custom-layer export, and false accepts from Spanish partial phrases like “hola” or “roger”.

## Findings
1. **Train the phrase from audio, not just text.** For “hola roger”, collect/augment positives that include Spanish pronunciation, microphone distance, noise, and speaker variety; add negatives containing “hola”, “roger”, similar names, TV/radio Spanish speech, and household noise. Wake-word systems commonly operate over short sliding audio windows, so clip length, leading/trailing silence, and label alignment matter as much as model architecture. [openWakeWord custom wake-word docs](https://github.com/dscripka/openWakeWord), [microWakeWord training docs](https://github.com/kahrendt/microWakeWord)

2. **Use one config per architecture and keep preprocessing identical.** Compare GRU, LSTM, and TCN only after fixing sample rate, mel/MFCC settings, window size, hop length, augmentation, train/validation/test split, and thresholds. A practical config shape is:

   ```yaml
   project: hola_roger
   data:
     positive_dir: data/hola_roger/positive
     negative_dir: data/hola_roger/negative
     validation_dir: data/hola_roger/validation
     sample_rate: 16000
   features:
     type: log_mel
     n_mels: 40
     frame_ms: 30
     hop_ms: 10
   model:
     type: gru        # repeat as lstm, tcn
     units: 32        # tune per architecture
     dropout: 0.1
   training:
     batch_size: 64
     epochs: 50
     learning_rate: 0.001
     seed: 1337
   export:
     keras: true
     tflite: true
   ```

   Verify exact NanoWakeWord field/flag names against the installed package or repo help before scripting, because small wake-word projects often change CLI schemas between releases. [TensorFlow audio recognition tutorial](https://www.tensorflow.org/tutorials/audio/simple_audio), [TensorFlow Lite conversion guide](https://www.tensorflow.org/lite/models/convert/convert_models)

3. **Expected CLI/API workflow is config-driven: train, evaluate, export, then threshold-test.** Look for current commands equivalent to:

   ```bash
   nanowakeword train --config configs/hola_roger_gru.yaml
   nanowakeword train --config configs/hola_roger_lstm.yaml
   nanowakeword train --config configs/hola_roger_tcn.yaml
   nanowakeword evaluate --model runs/hola_roger_gru/model.tflite --data data/hola_roger/test
   nanowakeword infer --model runs/hola_roger_gru/model.tflite --wav samples/live.wav
   ```

   If the package exposes Python APIs instead of stable CLIs, mirror the same stages: dataset loader → feature extractor → model factory `{gru,lstm,tcn}` → trainer → exporter → streaming scorer. [NanoWakeWord package/project page](https://pypi.org/project/nanowakeword/), [TensorFlow Keras GRU API](https://www.tensorflow.org/api_docs/python/tf/keras/layers/GRU), [TensorFlow Keras LSTM API](https://www.tensorflow.org/api_docs/python/tf/keras/layers/LSTM)

4. **Dependency constraints to pin before training.** Pin Python, TensorFlow, Keras, NumPy, and audio libraries in the same environment used for export; TensorFlow releases have strict Python/platform support and have historically lagged NumPy major-version changes. For Raspberry Pi deployment, decide whether inference uses full TensorFlow, `tflite-runtime`, ONNX Runtime, or a project-specific runner; do not assume artifacts produced on x86 will load unchanged on ARM. [TensorFlow pip install compatibility](https://www.tensorflow.org/install/pip), [TensorFlow Lite Python quickstart](https://www.tensorflow.org/lite/guide/python), [ONNX Runtime Python docs](https://onnxruntime.ai/docs/get-started/with-python.html)

5. **GRU/LSTM vs TCN export gotchas.** Keras GRU/LSTM can convert to TFLite, but stateful/dynamic-shape RNNs and unsupported ops may require changing layer options or enabling Select TF Ops, which increases runtime size. TCNs are attractive for embedded inference because they are usually Conv1D/dilation stacks, but third-party TCN layers may serialize as custom Keras objects; prefer an implementation made from standard Keras layers before export. [TensorFlow Lite supported ops](https://www.tensorflow.org/lite/guide/ops_compatibility), [TensorFlow Lite Select TF Ops](https://www.tensorflow.org/lite/guide/ops_select)

6. **Artifacts to expect/check in each run directory.** A complete run should preserve: training config YAML/JSON, label map/class names, feature/preprocessing metadata, checkpoints, final Keras model (`.keras` or SavedModel), exported `.tflite` and/or `.onnx`, metrics/history, threshold/ROC data, and example inference scores. For integration, treat preprocessing metadata as part of the model contract; a correct `.tflite` with mismatched sample rate or mel settings will fail silently via poor scores. [TensorFlow SavedModel guide](https://www.tensorflow.org/guide/saved_model), [TensorFlow Lite conversion guide](https://www.tensorflow.org/lite/models/convert/convert_models)

7. **Thresholding is deployment-specific.** Evaluate with continuous audio from the target Pi microphone, not only cropped test WAVs. Track false accepts per hour and miss rate separately; use a cooldown/refractory period after detection and require multiple consecutive high scores if NanoWakeWord does not already smooth scores. [microWakeWord project](https://github.com/kahrendt/microWakeWord), [openWakeWord project](https://github.com/dscripka/openWakeWord)

## Sources
- Kept: NanoWakeWord PyPI page (https://pypi.org/project/nanowakeword/) — likely package entry point for current install/version metadata; verify exact CLI from installed release.
- Kept: openWakeWord GitHub (https://github.com/dscripka/openWakeWord) — practical reference for custom wake-word data generation/evaluation and streaming wake-word inference.
- Kept: microWakeWord GitHub (https://github.com/kahrendt/microWakeWord) — relevant embedded wake-word training/deployment reference, especially for artifact/threshold expectations.
- Kept: TensorFlow install docs (https://www.tensorflow.org/install/pip) — authoritative dependency/platform constraints.
- Kept: TensorFlow Lite conversion and ops docs (https://www.tensorflow.org/lite/models/convert/convert_models, https://www.tensorflow.org/lite/guide/ops_compatibility, https://www.tensorflow.org/lite/guide/ops_select) — authoritative export/runtime constraints.
- Kept: TensorFlow Keras GRU/LSTM docs (https://www.tensorflow.org/api_docs/python/tf/keras/layers/GRU, https://www.tensorflow.org/api_docs/python/tf/keras/layers/LSTM) — official layer behavior and arguments affecting export.
- Dropped: Generic SEO blog posts and non-primary tutorials — excluded because CLI names/dependency pins can become stale quickly.

## Gaps
- I could not verify the exact current NanoWakeWord repository README/CLI flags from live web search in this environment. Before implementation, run `python -m nanowakeword --help`, `nanowakeword --help`, or inspect the package README/`pyproject.toml` for exact commands and supported config schema.
- Need empirical choice among GRU/LSTM/TCN. Train all three with identical data/preprocessing, then select by target-Pi latency, RAM, false accepts/hour, and miss rate rather than validation accuracy alone.
- Need final dependency pins from the actual NanoWakeWord release; lock them in `requirements.txt`/`uv.lock` after confirming successful TFLite export and Pi inference.
