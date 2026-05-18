## ADDED Requirements

### Requirement: Intent routing
Roger SHALL classify each accepted instruction into a domain session before dispatching work to pi-agent.

#### Scenario: System task classified
- **WHEN** the user instruction asks to install software, uninstall software, update the system, kill an application, or manage laptop-level state
- **THEN** Roger SHALL route the task to the `system` session

#### Scenario: Current project task classified
- **WHEN** the user instruction asks to create a demo, edit files, inspect code, or run tests in the active working context
- **THEN** Roger SHALL route the task to the `current-project` session

### Requirement: Separate session contexts
Roger SHALL keep separate pi-agent sessions for distinct domains so that system tasks and project tasks do not share the same conversation context by default.

#### Scenario: System and project tasks are separate
- **WHEN** a system task is followed by a current-project task
- **THEN** Roger SHALL dispatch each task to its corresponding session and SHALL NOT merge their pi-agent histories into one global work session

#### Scenario: Session reused within same domain
- **WHEN** multiple tasks target the same domain session
- **THEN** Roger SHALL reuse that domain session unless the user explicitly requests a fresh session

### Requirement: Ambiguity handling
Roger SHALL ask for clarification when it cannot confidently choose a context or target session.

#### Scenario: Ambiguous project target
- **WHEN** the user references a project or location that Roger cannot resolve uniquely
- **THEN** Roger SHALL ask which project or directory to use before dispatching the task

#### Scenario: Ambiguous domain
- **WHEN** an instruction could reasonably apply to both system and project contexts
- **THEN** Roger SHALL ask a clarifying question or choose the safest non-destructive interpretation without executing destructive work

### Requirement: Online and offline model selection
Roger SHALL use pi's configured default model when online and SHALL use an Ollama-backed pi model when offline.

#### Scenario: Online mode available
- **WHEN** Roger determines that internet and the configured pi default provider are available
- **THEN** Roger SHALL dispatch the task to pi-agent using pi's configured default model

#### Scenario: Offline mode detected
- **WHEN** Roger determines that internet or pi's configured online provider is unavailable
- **THEN** Roger SHALL dispatch the task to pi-agent using the configured Ollama fallback model

#### Scenario: Ollama fallback unavailable
- **WHEN** Roger is offline and the Ollama fallback model or server is unavailable
- **THEN** Roger SHALL report that offline execution is unavailable and SHALL NOT silently drop the task

### Requirement: Context registry
Roger SHALL maintain a registry of known domains and their session configuration.

#### Scenario: MVP registry initialized
- **WHEN** Roger starts for the first time
- **THEN** Roger SHALL provide at least `system` and `current-project` session entries

#### Scenario: Future domain added
- **WHEN** a new domain such as communications, media, or a named project is added to the registry
- **THEN** Roger SHALL be able to route matching instructions to that domain without changing the voice pipeline
