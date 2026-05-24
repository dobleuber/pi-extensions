## Why

Roger's offline/local work model currently assumes an Ollama-backed pi provider, but the user's target UX is a near real-time voice assistant. llama.cpp is expected to reduce local inference overhead and latency compared with Ollama, making it a better fit for quick spoken turns after wake-word and STT have already added their own latency.

## What Changes

- Migrate Roger's offline/local fallback model path from Ollama-oriented configuration and launch semantics to a llama.cpp-backed runtime.
- Add llama.cpp runtime configuration for server command, endpoint, model path or model id, context size, GPU layer/offload settings, temperature, and request timeout.
- Add health checks that verify the llama.cpp server/runtime is available, the configured model can load, and Roger can dispatch a minimal pi-agent prompt through the local provider path.
- Add latency-focused smoke/benchmark support so local fallback choices are evaluated against Roger's near-real-time voice UX goals.
- Update documentation and CLI output that currently describe offline execution as Ollama-based.
- Keep pi's online default model behavior unchanged when online; the migration only changes the local/offline fallback path.

## Capabilities

### New Capabilities
- `roger-llama-cpp-runtime`: Local llama.cpp-backed runtime configuration, health checking, latency benchmarking, and pi-agent launch/profile integration for Roger's local fallback execution path.

### Modified Capabilities
- `roger-context-routing`: Change offline model selection from an Ollama-backed pi model to a llama.cpp-backed local model/runtime, including unavailable-runtime reporting.

## Impact

- Affected code: `src/roger/config.py`, `src/roger/cli.py`, `src/roger/pi_rpc/sessions.py`, `src/roger/pi_rpc/runner.py`, and tests covering config, CLI health, pi session command generation, and offline task dispatch.
- Affected docs: `docs/setup.md`, `docs/benchmark-results.md`, README references, and any future hardening docs that currently mention Ollama fallback.
- External systems: llama.cpp binary/server, local GGUF model files, pi provider/model configuration, GPU offload settings for the laptop, and any OpenAI-compatible endpoint configuration needed for pi to talk to llama.cpp.
- Compatibility: online mode remains pi default; existing `--offline` intent remains valid but should target llama.cpp after migration. Ollama-specific config may need migration or deprecation guidance.
