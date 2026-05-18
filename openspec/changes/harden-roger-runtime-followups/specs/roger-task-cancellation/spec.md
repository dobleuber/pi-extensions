## ADDED Requirements

### Requirement: Active task cancellation intent
Roger SHALL recognize user intent to stop an active task and map it to the currently running pi-agent operation.

#### Scenario: Stop phrase during active task
- **WHEN** a task is running and the user says a configured stop phrase such as "para Roger" or "cancela Roger"
- **THEN** Roger SHALL attempt to cancel the active task instead of routing the phrase as a new normal task

#### Scenario: CLI cancellation requested
- **WHEN** the user invokes a documented CLI or control command to stop the active task
- **THEN** Roger SHALL attempt to cancel the active pi-agent operation for the selected session

### Requirement: pi RPC abort command
Roger SHALL use pi RPC abort capabilities to stop active agent work when technically available.

#### Scenario: General abort succeeds
- **WHEN** Roger sends pi RPC `abort` for an active operation and receives a successful response
- **THEN** Roger SHALL report that cancellation was accepted and SHALL wait for or record the resulting agent end state

#### Scenario: Bash abort needed
- **WHEN** a bash/tool command is actively running and pi RPC supports a more specific bash abort command
- **THEN** Roger MAY send `abort_bash` after or instead of general abort and SHALL record the command response

#### Scenario: Retry abort needed
- **WHEN** pi-agent is waiting in an automatic retry delay
- **THEN** Roger MAY send `abort_retry` and SHALL record whether retry cancellation succeeded

### Requirement: Cancellation result reporting
Roger SHALL clearly report the outcome of a cancellation attempt.

#### Scenario: Abort accepted and task ends aborted
- **WHEN** pi-agent reports that the active task ended because it was aborted
- **THEN** Roger SHALL mark the task as cancelled and SHALL provide a concise visible and spoken cancellation summary if TTS is available

#### Scenario: Abort command rejected
- **WHEN** pi RPC rejects an abort command or no active operation exists
- **THEN** Roger SHALL report that there was nothing cancellable or that cancellation failed

#### Scenario: Abort unavailable
- **WHEN** Roger cannot use pi RPC abort for the active task
- **THEN** Roger SHALL report the limitation and SHALL NOT pretend the task stopped successfully

### Requirement: Safe cancellation boundary
Roger SHALL avoid cancelling the wrong session or unrelated process.

#### Scenario: Multiple sessions exist
- **WHEN** multiple Roger sessions have recent activity but only one task is active
- **THEN** Roger SHALL target cancellation to the active session only

#### Scenario: Ambiguous active task
- **WHEN** Roger cannot determine which task the user wants to cancel
- **THEN** Roger SHALL ask for clarification before aborting any pi-agent operation
