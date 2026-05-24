## 1. Local llama.cpp and pi Provider Setup

- [x] 1.1 Verify the local llama.cpp registry has a default model and server wrapper available.
- [x] 1.2 Register a `llama-cpp` provider/model in `~/.pi/agent/models.json` without removing existing providers.
- [x] 1.3 Verify the llama.cpp server `/v1/models` and a minimal chat completion request.

## 2. Roger Configuration Migration

- [x] 2.1 Update Roger's default offline provider/model from Ollama to llama.cpp/gemma4.
- [x] 2.2 Replace Ollama-specific pi session command generation with generic offline provider/model arguments.
- [x] 2.3 Update CLI help and health output to describe llama.cpp offline mode.

## 3. Documentation and Tests

- [x] 3.1 Update docs and benchmark notes that currently describe Ollama as the offline fallback.
- [x] 3.2 Add or update tests for config defaults, pi session command generation, CLI help/health, and offline task runner wiring.
- [x] 3.3 Run unit tests and OpenSpec validation.

## 4. Verification Findings Hardening

- [x] 4.1 Add tests for llama.cpp offline unavailable reporting and empty pi-agent responses.
- [x] 4.2 Add a llama.cpp preflight check before offline dispatch so Roger reports unavailable local runtime clearly.
- [x] 4.3 Add bounded pi RPC read timeouts for offline/local runs so near-real-time tasks do not hang indefinitely.
- [x] 4.4 Update docs/health text with the llama.cpp base URL and timeout expectations.
- [x] 4.5 Re-run unit tests, OpenSpec validation, and focused offline smoke checks.
- [x] 4.6 Enable a genuinely near-real-time llama.cpp runtime by installing/using a GPU-enabled llama.cpp build or selecting a lower-latency GGUF model; current local `llama-server --list-devices` reports no GPU devices and pi prompt eval exceeds the offline timeout.

## 5. Runtime Wrapper and Kokoro GPU

- [x] 5.1 Create and verify a generic `llama-server-cuda` wrapper for direct llama.cpp server commands.
- [x] 5.2 Verify whether Kokoro can use CUDA locally and choose the simplest acceleration path.
- [x] 5.3 Add config/factory support for running Kokoro on CUDA by default.
- [x] 5.4 Update health output and docs to show the Kokoro device.
- [x] 5.5 Re-run tests, OpenSpec validation, and a Kokoro CUDA synthesis smoke check.
