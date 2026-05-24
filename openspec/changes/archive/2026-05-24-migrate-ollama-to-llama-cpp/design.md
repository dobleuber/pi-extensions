## Context

Roger currently keeps the online work model as pi's configured default and uses an `offline` path that launches pi RPC with `--provider ollama` and an optional Ollama model. The laptop now has llama.cpp installed, Ollama has been removed, and the local llama.cpp registry contains a default `gemma4` GGUF model at port `11434` with wrappers under `~/.local/bin/`.

The goal is not to make Roger execute tasks directly through llama.cpp. Roger should still dispatch work through pi-agent so it preserves pi sessions, tools, permissions, and context handling. llama.cpp should appear to pi as a local OpenAI-compatible provider exposed by `llama-server`.

## Goals / Non-Goals

**Goals:**

- Replace Roger's offline fallback provider default from Ollama to llama.cpp.
- Register/use the current local llama.cpp model (`gemma4`) as the offline pi model.
- Keep the existing `--offline` user intent but make it select llama.cpp instead of Ollama.
- Expose llama.cpp provider/model details in `roger health` and docs.
- Verify llama.cpp locally through its OpenAI-compatible `/v1/models` and chat endpoints.

**Non-Goals:**

- Do not re-install llama.cpp or download new GGUF files; the user already installed llama.cpp and migrated models.
- Do not bypass pi-agent tools or sessions with direct llama.cpp calls from Roger.
- Do not change the online/default pi model path.
- Do not implement automatic online/offline detection in this change; that remains part of the hardening follow-up.

## Decisions

### Use pi custom provider configuration for llama.cpp

pi already supports custom OpenAI-compatible providers in `~/.pi/agent/models.json`. Roger will launch pi with `--provider llama-cpp --model gemma4` in offline mode. The provider points at `http://127.0.0.1:11434/v1`, which matches the llama.cpp wrapper and avoids the web-dev-reserved port `8080`.

Alternative considered: call llama.cpp directly from Roger. This was rejected because it would bypass pi-agent tool execution and session semantics.

### Keep Roger config generic but default it to llama.cpp

`ModelConfig` already stores a provider and model. The implementation should stop hard-coding `ollama_model` names in `PiSessionManager` and instead pass the configured offline provider/model. This keeps future local providers possible while changing the default to llama.cpp.

Alternative considered: add a llama.cpp-only config tree first. This is useful later for starting/stopping servers, but not required for the minimal migration because llama.cpp already has a registry/wrapper and pi only needs provider/model selection.

### Treat server lifecycle as an external prerequisite for now

This change will verify and document that `llama-gemma4-server` must be running for offline mode. Roger health can show configured provider/model, but automatic server startup and supervision should remain a later enhancement unless needed after smoke testing.

Alternative considered: always spawn `llama-server` from Roger before offline dispatch. This adds daemon/process lifecycle complexity and risks duplicate servers, so it is deferred.

### Configure compatibility for local OpenAI-compatible llama.cpp

The pi provider should use `api: "openai-completions"`, a literal dummy API key, and compatibility flags disabling unsupported OpenAI features such as developer role and reasoning effort. This matches pi guidance for local OpenAI-compatible servers.

## Risks / Trade-offs

- **llama.cpp server not running** → Health/docs and offline task errors must clearly report the local server requirement.
- **Model id mismatch between llama.cpp `/v1/models` and pi config** → Use the registry name `gemma4` for Roger/pi config and verify `/v1/models` before relying on dispatch.
- **Local model may be less capable for tool-heavy tasks** → Keep online default unchanged and describe llama.cpp as fast local/offline fallback.
- **Context window too small for pi tasks** → Start with the wrapper default context and expose model metadata in pi config; tune `LLAMA_CPP_CTX` later if needed.

## Migration Plan

1. Register a `llama-cpp` provider in `~/.pi/agent/models.json` pointing to `http://127.0.0.1:11434/v1` with model `gemma4`.
2. Change Roger defaults and session command generation so `--offline` uses `--provider llama-cpp --model gemma4`.
3. Update health text, CLI help, tests, and documentation to remove Ollama as the current fallback.
4. Verify llama.cpp server responses and run Roger tests/OpenSpec validation.
5. Leave automatic server startup and advanced latency benchmarking for a future task if the manual server prerequisite is acceptable.
