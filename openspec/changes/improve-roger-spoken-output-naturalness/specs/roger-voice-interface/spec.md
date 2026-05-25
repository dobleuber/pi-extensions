## MODIFIED Requirements

### Requirement: Local spoken response
Roger SHALL produce spoken responses using a local text-to-speech backend that can operate without internet connectivity, and SHALL prepare those spoken responses from a TTS-only speech script rather than from canonical display text when naturalization is enabled.

#### Scenario: Task response available
- **WHEN** pi-agent produces a final response or status summary for a dispatched task
- **THEN** Roger SHALL speak a concise response through local TTS

#### Scenario: Natural spoken response prepared
- **WHEN** Roger prepares a final response or status summary for local TTS
- **THEN** Roger SHALL generate or select a speech-friendly Spanish script for TTS
- **AND** Roger SHALL keep the canonical written response visible unchanged

#### Scenario: TTS unavailable
- **WHEN** the local TTS backend is unavailable or fails
- **THEN** Roger SHALL keep the textual response visible and SHALL NOT block task completion

#### Scenario: Speech naturalizer unavailable
- **WHEN** the speech naturalizer is unavailable or fails
- **THEN** Roger SHALL keep the textual response visible unchanged
- **AND** Roger SHALL use deterministic fallback cleanup or skip speech without blocking task completion
