## ADDED Requirements

### Requirement: Configurable routing domains
Roger SHALL allow new routing domains to be added through registry/configuration without changing the voice capture pipeline.

#### Scenario: Named project domain added
- **WHEN** configuration adds a named project domain with cwd, description, and routing rules
- **THEN** Roger SHALL be able to route matching accepted instructions to that domain session

#### Scenario: Non-project domain added
- **WHEN** configuration adds a domain such as communications or media with its own routing rules
- **THEN** Roger SHALL route matching instructions to that domain without changes to wake-word, VAD, STT, or TTS adapters

### Requirement: Rule explanation
Roger SHALL be able to explain why a route was selected or why clarification is required.

#### Scenario: Route selected by keyword rule
- **WHEN** a route is selected because a configured rule matched the instruction
- **THEN** Roger SHALL expose the matched domain and rule reason for logs or diagnostics

#### Scenario: Clarification required by ambiguous rule
- **WHEN** an instruction matches ambiguity or destructive-safety rules
- **THEN** Roger SHALL expose the safety reason and SHALL ask a clarifying question before dispatch

### Requirement: Destructive action safety
Roger SHALL keep destructive or high-impact actions conservative when routing confidence is low.

#### Scenario: Destructive instruction without target context
- **WHEN** the user asks Roger to delete, remove, kill, overwrite, uninstall, or otherwise perform a high-impact action without a clear target context
- **THEN** Roger SHALL ask for clarification before dispatching the task

#### Scenario: Safe non-destructive default exists
- **WHEN** an ambiguous instruction has a safe non-destructive interpretation and no configured destructive rule matches
- **THEN** Roger MAY choose the safe interpretation but SHALL record that the route was low-confidence

### Requirement: Session policy per domain
Roger SHALL associate each routing domain with its pi session policy.

#### Scenario: Domain reuses session
- **WHEN** a configured domain has reuse enabled and multiple instructions target that domain
- **THEN** Roger SHALL reuse that domain's pi session by default

#### Scenario: Domain requests fresh session
- **WHEN** the user or domain policy requests a fresh session for a task
- **THEN** Roger SHALL start or select a fresh pi session for that domain without affecting other domains

### Requirement: Router testability
Roger SHALL provide deterministic tests or diagnostics for configured routing behavior.

#### Scenario: Route dry-run
- **WHEN** a developer runs a route diagnostic for an instruction
- **THEN** Roger SHALL show the selected domain or clarification question without dispatching to pi-agent

#### Scenario: Invalid routing config
- **WHEN** a routing config references an unknown session or malformed rule
- **THEN** Roger SHALL report a configuration error during health checks or startup
