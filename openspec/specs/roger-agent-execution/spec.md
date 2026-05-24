# Roger Agent Execution

## Purpose
Defines how Roger dispatches routed user instructions to pi-agent, exposes task lifecycle state, and preserves terminal-equivalent execution semantics.

## Requirements

### Requirement: pi-agent task dispatch
Roger SHALL dispatch accepted and routed instructions to pi-agent for execution rather than implementing task execution itself.

#### Scenario: Instruction dispatched to pi-agent
- **WHEN** the router selects a target session for an accepted instruction
- **THEN** Roger SHALL send the instruction to the corresponding pi-agent session for execution

#### Scenario: pi-agent unavailable
- **WHEN** Roger cannot start or communicate with pi-agent
- **THEN** Roger SHALL report the failure visibly and audibly if TTS is available

### Requirement: Terminal-equivalent permissions
Roger-dispatched pi-agent sessions SHALL execute with the same permissions and tool capabilities that pi has when launched from the terminal in the configured context.

#### Scenario: System task requires package installation
- **WHEN** the user asks Roger to install software and the task is routed to the `system` session
- **THEN** Roger SHALL allow pi-agent to use its normal terminal tools and permissions to perform the installation

#### Scenario: Project task requires file edits and tests
- **WHEN** the user asks Roger to modify a project and run tests
- **THEN** Roger SHALL allow pi-agent to read files, write files, edit files, and run commands according to pi's normal terminal capabilities

### Requirement: Task lifecycle visibility
Roger SHALL expose task lifecycle status for each dispatched pi-agent task.

#### Scenario: Task starts
- **WHEN** Roger dispatches an instruction to pi-agent
- **THEN** Roger SHALL show that the task has started and which session is handling it

#### Scenario: Task streams progress
- **WHEN** pi-agent emits text, tool execution events, or command output during the task
- **THEN** Roger SHALL make detailed progress visible in a log surface

#### Scenario: Task completes
- **WHEN** pi-agent finishes the task
- **THEN** Roger SHALL show completion status and prepare a concise response summary for TTS

#### Scenario: Task fails
- **WHEN** pi-agent reports an error or cannot complete the task
- **THEN** Roger SHALL show the error details in the log and speak a concise failure summary if TTS is available

### Requirement: Spoken summaries instead of full logs
Roger SHALL speak concise summaries of pi-agent task results and SHALL keep detailed logs textual by default.

#### Scenario: Long command output produced
- **WHEN** a task produces long command output or tool logs
- **THEN** Roger SHALL keep the full output visible in logs and SHALL NOT read the full output aloud by default

#### Scenario: User requests details aloud
- **WHEN** the user explicitly asks Roger to read details aloud
- **THEN** Roger MAY speak a selected summary or excerpt of the visible log

### Requirement: Session cwd handling
Roger SHALL launch or address each pi-agent session with the correct working directory for its domain.

#### Scenario: Current project session
- **WHEN** a task is routed to `current-project`
- **THEN** Roger SHALL use the configured current project directory as the pi-agent working directory

#### Scenario: System session
- **WHEN** a task is routed to `system`
- **THEN** Roger SHALL use the configured system working directory for laptop-level tasks

### Requirement: Cancellation boundary
Roger SHALL support cancelling before dispatch and SHOULD support aborting an in-flight pi-agent task when technically available.

#### Scenario: Cancel before dispatch
- **WHEN** the user cancels during transcription preview
- **THEN** Roger SHALL NOT send the instruction to pi-agent

#### Scenario: Abort in-flight task
- **WHEN** a task is already running and the user asks Roger to stop it
- **THEN** Roger SHALL attempt to abort the active pi-agent operation and report whether the abort succeeded
