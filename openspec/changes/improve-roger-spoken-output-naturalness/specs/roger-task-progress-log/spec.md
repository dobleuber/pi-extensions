## ADDED Requirements

### Requirement: Speech naturalization logging
Roger SHALL retain speech naturalization metadata in structured task logs when spoken output is attempted.

#### Scenario: Naturalized speech recorded
- **WHEN** Roger prepares speech text for a task result
- **THEN** the task log SHALL be able to record the canonical display text, TTS speech text, naturalizer source, style profile, and degradation reason when available

#### Scenario: Fallback naturalization recorded
- **WHEN** Roger uses deterministic fallback cleanup because the local Gemma naturalizer is unavailable, times out, or returns invalid output
- **THEN** the task log SHALL record that fallback speech preparation was used

#### Scenario: Visible log remains canonical
- **WHEN** a task log is rendered for normal user inspection
- **THEN** it SHALL show canonical written task output by default rather than pronunciation spellings intended only for TTS
