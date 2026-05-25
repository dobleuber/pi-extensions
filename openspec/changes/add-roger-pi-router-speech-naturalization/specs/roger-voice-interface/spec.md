## ADDED Requirements

### Requirement: Voice responses use pi-router speech text
Roger voice responses for dispatched tasks SHALL use pi-router-provided `speech_text` when available.

#### Scenario: Task response has speech_text
- **WHEN** a dispatched task completes and pi-router provides `speech_text`
- **THEN** Roger SHALL speak that `speech_text` through local TTS
- **AND** Roger SHALL keep `display_text` visible in the overlay and CLI

#### Scenario: Task response lacks speech_text
- **WHEN** a dispatched task completes but no `speech_text` is available
- **THEN** Roger SHALL keep the canonical task result visible
- **AND** Roger SHALL degrade speech safely without blocking the return-to-listening flow
