## ADDED Requirements

### Requirement: Structured speech metadata logging
Roger SHALL record pi-router-provided speech metadata in task logs while preserving canonical visible rendering by default.

#### Scenario: Structured speech response logged
- **WHEN** Roger receives `display_text`, `speech_text`, `speech_language`, or `speech_source` from pi-router
- **THEN** Roger SHALL record those fields in the structured task log

#### Scenario: Visible log rendered
- **WHEN** a user views the normal task log rendering
- **THEN** Roger SHALL show canonical `display_text` by default rather than pronunciation or speech-only text

#### Scenario: Speech debugging needed
- **WHEN** a developer inspects the JSONL task log after a spoken-output issue
- **THEN** the log SHALL expose the exact `speech_text` Roger attempted to send to TTS
