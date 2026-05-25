## ADDED Requirements

### Requirement: Supported Kokoro prosody controls
Roger SHALL expose only Kokoro TTS controls that are supported by the installed local API.

#### Scenario: Speed configured
- **WHEN** Roger loads TTS configuration with a Kokoro speed value
- **THEN** Roger SHALL pass that speed value to the Kokoro pipeline call

#### Scenario: Split pattern configured
- **WHEN** Roger loads TTS configuration with a split pattern
- **THEN** Roger SHALL use that split pattern when chunking text for Kokoro synthesis

#### Scenario: Unsupported emotion not claimed
- **WHEN** Roger reports TTS capabilities or documents Kokoro behavior
- **THEN** Roger SHALL NOT claim direct Kokoro emotion, tone, or style controls unless the installed Kokoro API exposes them

### Requirement: Voice and voice-blend configuration
Roger SHALL allow configuring the Kokoro voice value used for synthesis, including voice blends supported by Kokoro's voice-loading behavior.

#### Scenario: Single voice configured
- **WHEN** Roger TTS config sets a single Kokoro voice such as `ef_dora`
- **THEN** Roger SHALL use that voice for synthesis

#### Scenario: Voice blend configured
- **WHEN** Roger TTS config sets a comma-separated Kokoro voice blend and all referenced voices are locally available or resolvable
- **THEN** Roger SHALL pass the blend value to Kokoro as the voice argument

#### Scenario: Missing voice asset
- **WHEN** Roger TTS config references a local voice asset that is unavailable
- **THEN** Roger SHALL report the missing voice clearly and preserve text-only task output

### Requirement: Roger speech style profiles
Roger SHALL support named speech style profiles that map to naturalizer instructions and supported Kokoro controls.

#### Scenario: Neutral style selected
- **WHEN** the neutral style profile is selected
- **THEN** Roger SHALL use normal speech naturalization and default configured Kokoro speed

#### Scenario: Concise status style selected
- **WHEN** a short status or progress message is spoken
- **THEN** Roger MAY use a concise style profile that shortens phrasing while preserving task meaning

#### Scenario: Urgent failure style selected
- **WHEN** Roger speaks an urgent failure or cancellation result
- **THEN** Roger MAY use clearer wording or supported speed adjustments without relying on unsupported Kokoro emotion controls
