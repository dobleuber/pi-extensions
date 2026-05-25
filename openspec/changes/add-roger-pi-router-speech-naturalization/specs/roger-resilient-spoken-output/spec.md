## ADDED Requirements

### Requirement: Missing pi-router speech metadata degradation
Roger SHALL degrade safely when pi-router speech metadata is missing, unavailable, or unusable.

#### Scenario: speech_text missing
- **WHEN** a TTS-enabled Roger task completes but pi-router does not provide `speech_text`
- **THEN** Roger SHALL keep the canonical result visible
- **AND** Roger SHALL either use minimal deterministic formatting cleanup or skip speech without changing task status

#### Scenario: speech_text invalid for TTS
- **WHEN** pi-router provides speech metadata that cannot be sent safely to local TTS
- **THEN** Roger SHALL keep the canonical result visible
- **AND** Roger SHALL report spoken-output degradation without changing task status

### Requirement: No Roger model-backed speech fallback
Roger SHALL NOT use a direct model-backed translator or naturalizer when pi-router speech metadata is unavailable.

#### Scenario: pi-router speech naturalization unavailable
- **WHEN** pi-router cannot produce `speech_text`
- **THEN** Roger SHALL NOT call llama.cpp or another LLM endpoint directly to replace pi-router speech naturalization
- **AND** Roger SHALL use visible text-only or minimal deterministic fallback behavior
