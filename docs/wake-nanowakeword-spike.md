# NanoWakeWord Wake Word Spike

This spike evaluates **NanoWakeWord** for the fixed wake phrase:

```text
hola roger
```

Only three architectures are in scope for the first pass:

- `gru`
- `lstm`
- `tcn`

`openWakeWord` is reserved as a fallback only if these candidates fail.

## Generated configs

Generate the current training configs with:

```bash
PYTHONPATH=src python3 -m roger.cli spike wake --write-configs --output-dir configs/nanowakeword
```

This writes:

- `configs/nanowakeword/hola_roger_gru.json`
- `configs/nanowakeword/hola_roger_lstm.json`
- `configs/nanowakeword/hola_roger_tcn.json`

Each config includes:

- fixed positive samples for `hola roger`;
- automatic adversarial negatives;
- phoneme adversarial negatives;
- manual nearby negatives: `hola`, `roger`, `oye roger`, `hola rojo`, `hola royer`, `ola roger`.

## Selected model

The current LSTM model is stored outside git because `models/` is ignored:

```text
models/wake/nanowakeword/hola_roger_lstm/model/hola_roger_lstm.onnx
```

The listener defaults to this model.

## Training

NanoWakeWord's public API/CLI has moved quickly, so verify exact commands against the installed package before running a long training job:

```bash
python -m nanowakeword --help
nanowakeword --help
python - <<'PY'
import nanowakeword
print(nanowakeword)
PY
```

The intended reproducible sequence is one run per generated config:

```bash
nanowakeword train --config configs/nanowakeword/hola_roger_gru.json
nanowakeword train --config configs/nanowakeword/hola_roger_lstm.json
nanowakeword train --config configs/nanowakeword/hola_roger_tcn.json
```

If the installed package exposes only Python APIs, mirror the same stages in a wrapper script:

1. load generated JSON config;
2. generate positive and negative data;
3. train the selected architecture;
4. export ONNX and/or PyTorch artifacts;
5. save metrics and threshold data.

## Benchmark metrics

For each architecture, record:

- false positives per hour;
- false negative rate;
- p95 activation latency;
- idle CPU percent;
- RSS memory in MB;
- training duration;
- model artifact paths;
- threshold/cooldown settings.

The helper `roger.benchmarks.wake_benchmark.select_wake_architecture()` selects a default only when a candidate meets the configured reliability/resource thresholds. If none passes, keep the temporary/manual trigger and evaluate fallback options.
