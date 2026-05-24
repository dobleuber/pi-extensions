# Roger llama.cpp Runtime

## Purpose
Defines Roger's llama.cpp-backed local runtime profile for offline pi-agent execution.

## Requirements

### Requirement: llama.cpp local runtime profile
Roger SHALL support a llama.cpp-backed local runtime profile for offline pi-agent execution.

#### Scenario: Default llama.cpp runtime configured
- **WHEN** Roger loads its default configuration
- **THEN** the offline model provider SHALL be `llama-cpp` and the offline model SHALL reference the configured local llama.cpp model

#### Scenario: llama.cpp provider selected for offline task
- **WHEN** the user starts Roger with offline mode enabled
- **THEN** Roger SHALL launch pi-agent with the configured llama.cpp provider and model arguments

### Requirement: llama.cpp server health visibility
Roger SHALL make the configured llama.cpp provider/model visible in health output and documentation.

#### Scenario: Health command run
- **WHEN** the user runs `roger health`
- **THEN** Roger SHALL show the offline provider and model configured for llama.cpp

#### Scenario: Server prerequisite documented
- **WHEN** the user reads setup documentation for offline mode
- **THEN** the documentation SHALL explain how to start the configured llama.cpp server wrapper before dispatching offline tasks

### Requirement: llama.cpp local endpoint compatibility
Roger SHALL rely on a pi custom provider that talks to llama.cpp through an OpenAI-compatible local endpoint.

#### Scenario: pi provider registered
- **WHEN** the local pi models configuration is inspected
- **THEN** it SHALL include a `llama-cpp` provider with an OpenAI-compatible `/v1` endpoint and the configured local model

#### Scenario: llama.cpp endpoint responds
- **WHEN** the configured llama.cpp server is running
- **THEN** `/v1/models` SHALL expose a model usable by pi's `llama-cpp` provider

### Requirement: Ollama not required
Roger SHALL NOT require Ollama for offline/local fallback execution after migration.

#### Scenario: Ollama absent
- **WHEN** Ollama is not installed or not running
- **THEN** Roger's offline configuration and health output SHALL still point to llama.cpp rather than Ollama
