## ADDED Requirements

### Requirement: Offline speech naturalization through pi provider
Roger SHALL route offline model-backed speech naturalization through pi-agent's configured llama.cpp provider rather than calling the llama.cpp endpoint directly.

#### Scenario: Offline speech-enabled task
- **WHEN** Roger dispatches a TTS-enabled task in offline mode
- **THEN** any model-backed speech naturalization SHALL use pi-agent's `llama-cpp` provider and configured model

#### Scenario: llama.cpp endpoint unavailable
- **WHEN** the local llama.cpp endpoint is unavailable during an offline speech-enabled task
- **THEN** Roger SHALL rely on pi-agent/pi-router offline availability reporting and SHALL NOT start a separate direct naturalization call to llama.cpp
