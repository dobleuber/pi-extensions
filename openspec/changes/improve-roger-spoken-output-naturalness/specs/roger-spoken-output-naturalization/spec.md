## ADDED Requirements

### Requirement: Separate display text and speech text
Roger SHALL preserve canonical written output for user-visible text while generating a separate speech-only script for TTS.

#### Scenario: Markdown result spoken naturally
- **WHEN** Roger receives display text containing Markdown such as `son las **10:30 am**`
- **THEN** Roger SHALL keep the original Markdown text visible in preview, overlay, CLI, logs, and retry context
- **AND** Roger SHALL send a speech-friendly script such as “son las diez y treinta de la mañana” to TTS

#### Scenario: Technical spelling preserved visually
- **WHEN** Roger receives display text containing technical terms such as `README`, `GitHub`, `JSON`, file paths, commands, or code identifiers
- **THEN** Roger SHALL preserve those exact written tokens in visible output
- **AND** Roger MAY rewrite only the TTS speech text for more natural pronunciation

### Requirement: Local Gemma speech naturalizer
Roger SHALL use the configured local llama.cpp/Gemma profile as the preferred naturalizer for spoken summaries when available.

#### Scenario: Gemma naturalization succeeds
- **WHEN** Roger prepares a spoken task result and the configured local naturalizer responds within the timeout
- **THEN** Roger SHALL use the returned Spanish speech script for TTS
- **AND** Roger SHALL keep the original display text unchanged for visible surfaces

#### Scenario: Gemma naturalizer unavailable
- **WHEN** the local naturalizer model or llama.cpp server is unavailable
- **THEN** Roger SHALL use deterministic fallback cleanup for TTS speech text
- **AND** Roger SHALL NOT fail or change the underlying task result solely because naturalization failed

#### Scenario: Gemma naturalizer returns unsafe output
- **WHEN** the local naturalizer returns empty, malformed, or meaning-changing output that Roger rejects
- **THEN** Roger SHALL discard that naturalized output and use deterministic fallback cleanup

### Requirement: Deterministic speech cleanup fallback
Roger SHALL provide a local deterministic fallback that removes or rewrites common speech-hostile formatting without requiring a model call.

#### Scenario: Markdown punctuation cleanup
- **WHEN** speech text contains Markdown emphasis, headings, bullets, links, or repeated formatting punctuation
- **THEN** Roger SHALL remove or rewrite that formatting before sending text to TTS

#### Scenario: Time format cleanup
- **WHEN** speech text contains a common time expression such as `10:30 am`
- **THEN** Roger SHALL rewrite it to natural Spanish speech such as “diez y treinta de la mañana” when feasible

#### Scenario: Common anglicism pronunciation cleanup
- **WHEN** speech text contains a configured technical anglicism such as `GitHub`, `pull request`, `README`, `API`, `JSON`, or `Docker`
- **THEN** Roger SHALL rewrite the TTS speech text to a pronunciation-friendly form while preserving the canonical spelling outside TTS

### Requirement: Speech naturalization metadata
Roger SHALL make speech naturalization inspectable without making normal visual output noisy.

#### Scenario: Speech script recorded
- **WHEN** Roger naturalizes text for TTS during a task
- **THEN** Roger SHALL be able to record the canonical display text, speech text, naturalizer source, and degradation reason when available

#### Scenario: Normal overlay remains canonical
- **WHEN** the overlay shows a task result whose TTS speech text contains pronunciation spellings
- **THEN** the overlay SHALL show the canonical written result rather than the pronunciation spellings
