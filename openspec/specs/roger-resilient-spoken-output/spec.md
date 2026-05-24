# Roger Resilient Spoken Output

## Purpose
Defines best-effort local TTS behavior and text-only degradation when speech output fails.

## Requirements

### Requirement: TTS failure isolation
Roger SHALL treat local TTS as best-effort output and SHALL NOT let speech synthesis or playback failures change the underlying task result.

#### Scenario: Completed task TTS fails
- **WHEN** pi-agent completes a task successfully but the local TTS backend fails while speaking the summary
- **THEN** Roger SHALL keep the task status as complete and SHALL show the textual result visibly

#### Scenario: Failure summary TTS fails
- **WHEN** Roger needs to speak a failure summary and TTS is unavailable
- **THEN** Roger SHALL still show the failure details textually and SHALL continue daemon operation

#### Scenario: Clarification TTS fails
- **WHEN** Roger asks a clarification question and TTS fails
- **THEN** Roger SHALL keep the clarification visible and SHALL NOT dispatch the ambiguous instruction

### Requirement: Local-only speech output
Roger SHALL continue to use only local TTS backends for spoken responses.

#### Scenario: TTS backend unavailable
- **WHEN** the configured local TTS backend or local model assets are unavailable
- **THEN** Roger SHALL NOT call a cloud TTS service and SHALL fall back to visible text-only output

#### Scenario: Audio playback unavailable
- **WHEN** synthesis succeeds but local audio playback fails
- **THEN** Roger SHALL record the playback failure and SHALL keep the synthesized task result visible textually

### Requirement: TTS health and degradation visibility
Roger SHALL make repeated TTS degradation visible without spamming the user.

#### Scenario: First TTS failure in daemon
- **WHEN** TTS fails for the first time in a daemon run
- **THEN** Roger SHALL show a visible warning that speech output is degraded

#### Scenario: Repeated TTS failures
- **WHEN** TTS continues failing across multiple interactions
- **THEN** Roger SHALL rate-limit repeated warnings while continuing text-only operation

### Requirement: Safe speaker boundary
Roger SHALL expose a safe speaker boundary that reports speech success or failure to callers.

#### Scenario: Caller speaks summary
- **WHEN** a caller asks the speaker to synthesize and play a summary
- **THEN** the speaker SHALL return or record whether speech succeeded without requiring the caller to catch backend-specific exceptions

#### Scenario: No-TTS mode enabled
- **WHEN** the user starts Roger with no-TTS mode
- **THEN** Roger SHALL skip synthesis and playback while preserving the same textual task flow
