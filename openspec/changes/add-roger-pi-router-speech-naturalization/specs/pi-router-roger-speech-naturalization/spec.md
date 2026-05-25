## ADDED Requirements

### Requirement: Roger speech request metadata
pi-router SHALL recognize explicit Roger request metadata that asks for TTS-ready speech output without changing normal non-Roger routing behavior.

#### Scenario: Roger requests speech metadata
- **WHEN** a pi-agent request includes metadata identifying the source as Roger and speech output as enabled
- **THEN** pi-router SHALL treat the request as requiring structured Roger speech metadata
- **AND** pi-router SHALL preserve normal task execution semantics

#### Scenario: Non-Roger request
- **WHEN** a pi-agent request does not include Roger speech metadata
- **THEN** pi-router SHALL NOT add Roger-specific speech requirements to the response

### Requirement: Structured Roger response
pi-router SHALL provide a structured response for Roger speech requests containing canonical visual text and TTS-ready speech text.

#### Scenario: Roger task completes
- **WHEN** a Roger-marked task completes successfully
- **THEN** pi-router SHALL provide `display_text` containing the canonical visible task result
- **AND** pi-router SHALL provide `speech_text` containing a concise Spanish TTS-ready version of the result
- **AND** pi-router SHALL identify the speech language as `es`

#### Scenario: Roger task fails
- **WHEN** a Roger-marked task fails with a user-visible error or failure summary
- **THEN** pi-router SHALL preserve the canonical failure text in `display_text`
- **AND** pi-router SHALL provide a concise Spanish `speech_text` for Roger when possible

### Requirement: Spanish speech naturalization
pi-router SHALL generate Roger `speech_text` as natural Spanish speech while preserving technical Anglicisms, product names, paths, commands, and code identifiers when needed.

#### Scenario: English task response naturalized
- **WHEN** the canonical task result contains English prose such as `It's 8:39 and 9:05`
- **THEN** pi-router SHALL produce Spanish speech prose such as `Son las ocho treinta y nueve y nueve cinco`
- **AND** pi-router SHALL NOT require Roger to detect or translate English locally

#### Scenario: Technical terms retained
- **WHEN** the canonical task result contains terms such as `README`, `GitHub`, `Docker`, file paths, commands, or code identifiers
- **THEN** pi-router SHALL preserve or pronunciation-normalize those terms in `speech_text` without corrupting `display_text`

### Requirement: Provider-routed speech naturalization
pi-router SHALL perform model-backed Roger speech naturalization through pi-agent's configured provider/model routing rather than requiring Roger to call model endpoints directly.

#### Scenario: Offline Roger request
- **WHEN** Roger dispatches a speech-enabled task in offline mode
- **THEN** pi-router SHALL use the configured offline pi provider/model path for any model-backed speech naturalization

#### Scenario: Direct model endpoint avoided
- **WHEN** Roger needs speech naturalization for a task result
- **THEN** Roger SHALL receive speech metadata through pi-agent/pi-router
- **AND** Roger SHALL NOT call llama.cpp `/v1/chat/completions` directly for that naturalization
