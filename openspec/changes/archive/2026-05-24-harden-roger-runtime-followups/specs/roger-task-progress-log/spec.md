## ADDED Requirements

### Requirement: Structured task log
Roger SHALL create a structured task log for every dispatched pi-agent task.

#### Scenario: Task dispatch starts
- **WHEN** Roger sends an accepted instruction to pi-agent
- **THEN** Roger SHALL create a task log containing the instruction, target session, selected model mode, start time, and running status

#### Scenario: Task dispatch rejected
- **WHEN** pi-agent rejects the prompt before accepting the task
- **THEN** Roger SHALL record the rejection details in the task log and mark the task failed

### Requirement: Streamed assistant text logging
Roger SHALL capture streamed assistant text from pi RPC into the task log while preserving the final concise response summary.

#### Scenario: Assistant text delta received
- **WHEN** pi RPC emits a `message_update` event with a text delta
- **THEN** Roger SHALL append the delta to the visible task text in the log

#### Scenario: Assistant message error received
- **WHEN** pi RPC emits a message update whose reason indicates error or abort
- **THEN** Roger SHALL record the reason and expose it as task status context

### Requirement: Tool event logging
Roger SHALL capture pi RPC tool execution start, update, and end events in the task log.

#### Scenario: Tool starts
- **WHEN** pi RPC emits `tool_execution_start`
- **THEN** Roger SHALL record the tool name, tool call id, and safe argument summary

#### Scenario: Tool streams output
- **WHEN** pi RPC emits `tool_execution_update`
- **THEN** Roger SHALL update the corresponding tool log entry with the latest accumulated partial output

#### Scenario: Tool ends
- **WHEN** pi RPC emits `tool_execution_end`
- **THEN** Roger SHALL record the final output summary and error flag for the tool call

### Requirement: Log surface visibility
Roger SHALL make detailed task progress visible textually without reading full logs aloud by default.

#### Scenario: Long-running task produces output
- **WHEN** a pi-agent task emits multiple text or tool events before completion
- **THEN** Roger SHALL keep the detailed events visible in a textual log surface and SHALL only speak concise milestones or the final summary

#### Scenario: Overlay result shown
- **WHEN** a task completes or fails
- **THEN** Roger SHALL show the final status and a pointer or concise excerpt from the detailed log in the overlay or CLI output

### Requirement: Log persistence and bounds
Roger SHALL retain task logs long enough for troubleshooting while bounding disk and memory usage.

#### Scenario: Log exceeds configured size
- **WHEN** a task log grows beyond the configured visible size limit
- **THEN** Roger SHALL truncate or rotate the visible representation while preserving a reference to any full output path when available

#### Scenario: Daemon restarts
- **WHEN** Roger daemon restarts after a previous task
- **THEN** recent persisted task logs SHALL remain discoverable through a documented location or CLI command
