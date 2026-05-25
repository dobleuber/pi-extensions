## MODIFIED Requirements

### Requirement: TTS failure isolation
Roger SHALL treat local speech preparation, synthesis, and playback as best-effort output and SHALL NOT let speech naturalization, speech synthesis, or playback failures change the underlying task result.

#### Scenario: Completed task TTS fails
- **WHEN** pi-agent completes a task successfully but the local TTS backend fails while speaking the summary
- **THEN** Roger SHALL keep the task status as complete and SHALL show the textual result visibly

#### Scenario: Completed task naturalization fails
- **WHEN** pi-agent completes a task successfully but speech naturalization fails before TTS
- **THEN** Roger SHALL keep the task status as complete
- **AND** Roger SHALL use deterministic fallback speech cleanup or skip speech while keeping the textual result visible

#### Scenario: Failure summary TTS fails
- **WHEN** Roger needs to speak a failure summary and TTS is unavailable
- **THEN** Roger SHALL still show the failure details textually and SHALL continue daemon operation

#### Scenario: Failure summary naturalization fails
- **WHEN** Roger needs to speak a failure summary and the speech naturalizer is unavailable or times out
- **THEN** Roger SHALL still show the failure details textually
- **AND** Roger SHALL continue daemon operation with fallback or skipped speech

#### Scenario: Clarification TTS fails
- **WHEN** Roger asks a clarification question and TTS fails
- **THEN** Roger SHALL keep the clarification visible and SHALL NOT dispatch the ambiguous instruction

#### Scenario: Clarification naturalization fails
- **WHEN** Roger asks a clarification question and speech naturalization fails
- **THEN** Roger SHALL keep the clarification visible and SHALL NOT dispatch the ambiguous instruction

### Requirement: TTS health and degradation visibility
Roger SHALL make repeated TTS or speech-naturalization degradation visible without spamming the user.

#### Scenario: First TTS failure in daemon
- **WHEN** TTS fails for the first time in a daemon run
- **THEN** Roger SHALL show a visible warning that speech output is degraded

#### Scenario: First naturalization failure in daemon
- **WHEN** speech naturalization fails for the first time in a daemon run
- **THEN** Roger SHALL show a visible warning that spoken output is using degraded speech preparation

#### Scenario: Repeated TTS failures
- **WHEN** TTS continues failing across multiple interactions
- **THEN** Roger SHALL rate-limit repeated warnings while continuing text-only operation

#### Scenario: Repeated naturalization failures
- **WHEN** speech naturalization continues failing across multiple interactions
- **THEN** Roger SHALL rate-limit repeated warnings while continuing fallback or text-only operation

### Requirement: Safe speaker boundary
Roger SHALL expose a safe speaker boundary that reports speech preparation, synthesis, and playback success or failure to callers.

#### Scenario: Caller speaks summary
- **WHEN** a caller asks the speaker to prepare, synthesize, and play a summary
- **THEN** the speaker SHALL return or record whether speech succeeded without requiring the caller to catch backend-specific exceptions

#### Scenario: Speech text differs from display text
- **WHEN** speech naturalization produces a TTS script different from the canonical display text
- **THEN** the safe speaker boundary SHALL keep those values separate for callers and logs

#### Scenario: No-TTS mode enabled
- **WHEN** the user starts Roger with no-TTS mode
- **THEN** Roger SHALL skip naturalization, synthesis, and playback while preserving the same textual task flow
