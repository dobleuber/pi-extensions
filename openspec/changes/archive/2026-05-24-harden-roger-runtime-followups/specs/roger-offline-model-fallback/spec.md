## ADDED Requirements

### Requirement: Automatic model availability decision
Roger SHALL decide whether each pi-agent task should use pi's configured online default model or the configured llama.cpp fallback before dispatch.

#### Scenario: Online provider available
- **WHEN** Roger determines that the network and configured online pi provider are available
- **THEN** Roger SHALL launch or reuse the target pi session without overriding pi's default provider/model

#### Scenario: Explicit offline override
- **WHEN** the user starts Roger with an explicit offline mode flag or config setting
- **THEN** Roger SHALL skip online provider probing and SHALL use the configured llama.cpp fallback launch profile

#### Scenario: Online provider unavailable before dispatch
- **WHEN** Roger detects that internet access or the configured online provider is unavailable before dispatch
- **THEN** Roger SHALL use the configured llama.cpp fallback launch profile for the task

### Requirement: Fallback after pi startup or prompt failure
Roger SHALL attempt offline fallback when an online pi session cannot start or rejects a prompt due to provider/network availability, unless fallback is disabled.

#### Scenario: Online pi startup fails with provider error
- **WHEN** pi RPC startup or prompt acceptance fails with a recognized online-provider or network availability error
- **THEN** Roger SHALL retry the task once using the configured llama.cpp fallback session

#### Scenario: Non-provider task failure
- **WHEN** pi-agent accepts the task and later reports a normal task/tool error
- **THEN** Roger SHALL NOT automatically rerun the task on llama.cpp unless the user explicitly asks

### Requirement: Offline fallback unavailable reporting
Roger SHALL visibly and audibly report when offline execution cannot be used because llama.cpp or the configured fallback model is unavailable.

#### Scenario: llama.cpp server unavailable
- **WHEN** Roger needs offline fallback and cannot connect to the llama.cpp server
- **THEN** Roger SHALL report that offline execution is unavailable and SHALL NOT silently drop the task

#### Scenario: Fallback model missing
- **WHEN** Roger needs offline fallback and the configured llama.cpp model is not installed
- **THEN** Roger SHALL report the missing model name and SHALL keep the instruction visible for retry

### Requirement: Offline mode visibility
Roger SHALL indicate when a task is running in offline fallback mode.

#### Scenario: Fallback task starts
- **WHEN** Roger dispatches a task using the llama.cpp fallback profile
- **THEN** Roger SHALL show offline/fallback status in the overlay or textual task log

#### Scenario: Fallback task completes
- **WHEN** a fallback task completes
- **THEN** Roger SHALL include enough visible context for the user to know the result came from the offline model
