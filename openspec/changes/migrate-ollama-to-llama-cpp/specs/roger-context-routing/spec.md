## MODIFIED Requirements

### Requirement: Online and offline model selection
Roger SHALL use pi's configured default model when online and SHALL use a llama.cpp-backed pi model when offline.

#### Scenario: Online mode available
- **WHEN** Roger determines that internet and the configured pi default provider are available
- **THEN** Roger SHALL dispatch the task to pi-agent using pi's configured default model

#### Scenario: Offline mode detected
- **WHEN** Roger determines that internet or pi's configured online provider is unavailable
- **THEN** Roger SHALL dispatch the task to pi-agent using the configured llama.cpp fallback model

#### Scenario: llama.cpp fallback unavailable
- **WHEN** Roger is offline and the llama.cpp fallback model or server is unavailable
- **THEN** Roger SHALL report that offline execution is unavailable and SHALL NOT silently drop the task
