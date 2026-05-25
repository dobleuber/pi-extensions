## ADDED Requirements

### Requirement: Roger speech metadata dispatch
Roger SHALL request pi-router speech metadata when dispatching a task that may produce spoken output.

#### Scenario: TTS-enabled task dispatched
- **WHEN** Roger dispatches an accepted task to pi-agent and TTS is enabled
- **THEN** Roger SHALL include request metadata indicating that the source is Roger and speech output is requested

#### Scenario: No-TTS task dispatched
- **WHEN** Roger dispatches an accepted task while no-TTS mode is enabled
- **THEN** Roger SHALL NOT require pi-router to produce speech metadata for that task

### Requirement: Structured pi-agent response consumption
Roger SHALL consume structured pi-router responses by separating canonical display text from speech text.

#### Scenario: Structured response received
- **WHEN** pi-agent returns a Roger structured response containing `display_text` and `speech_text`
- **THEN** Roger SHALL show `display_text` in overlay, CLI, and visible logs
- **AND** Roger SHALL send `speech_text` to local TTS

#### Scenario: Plain text response received
- **WHEN** pi-agent returns a legacy plain text response without Roger speech metadata
- **THEN** Roger SHALL treat the plain text as canonical display text
- **AND** Roger SHALL degrade speech safely without failing the task
