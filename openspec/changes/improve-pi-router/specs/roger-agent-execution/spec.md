## ADDED Requirements

### Requirement: Routed prompt execution metadata
Roger SHALL preserve Pi-level router metadata for tasks it dispatches through pi-agent.

#### Scenario: Transformed prompt dispatched
- **WHEN** Roger dispatches an instruction and Pi transforms it into an English work prompt
- **THEN** Roger SHALL keep the original Spanish instruction, transformed English prompt, target session, selected work model, and requested thinking level associated with the task log when those fields are available

#### Scenario: Router fallback recorded
- **WHEN** a Roger-dispatched task runs with Pi router fallback or degraded translation behavior
- **THEN** Roger SHALL record the fallback reason in the task log or visible task status

#### Scenario: Original prompt visible for retry
- **WHEN** a Roger-dispatched routed task fails and the user wants to retry or inspect it
- **THEN** Roger SHALL keep the original Spanish instruction visible for retry context

### Requirement: Spanish final result delivery
Roger SHALL use the Pi-level router's Spanish final answer for user-facing completion when available.

#### Scenario: Pi returns translated final answer
- **WHEN** Pi completes a Roger-dispatched task and provides a Spanish final answer
- **THEN** Roger SHALL use that Spanish answer for visible completion and TTS summary

#### Scenario: Pi translation unavailable
- **WHEN** Pi completes a Roger-dispatched task but final-answer translation is unavailable
- **THEN** Roger SHALL show the original work-model answer and visibly indicate that Spanish translation was unavailable

#### Scenario: Technical output preserved
- **WHEN** the Pi final answer contains commands, file paths, code blocks, or exact tool output
- **THEN** Roger SHALL preserve those technical details while presenting surrounding user-facing explanation in Spanish when available
