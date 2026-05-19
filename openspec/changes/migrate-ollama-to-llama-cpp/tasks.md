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
