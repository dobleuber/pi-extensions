## ADDED Requirements

### Requirement: Pi-level router delegation
Roger SHALL delegate prompt language transformation and thinking-level selection to the configured Pi-level router when dispatching work through pi-agent.

#### Scenario: Roger dispatches Spanish instruction
- **WHEN** Roger accepts a Spanish voice or typed instruction and routes it to a Pi session
- **THEN** Roger SHALL allow the Pi-level router to transform the work prompt and select the thinking level before the work model receives the task

#### Scenario: Roger preserves domain routing
- **WHEN** Roger delegates language and thinking routing to Pi
- **THEN** Roger SHALL still choose the target domain session according to Roger context-routing rules

#### Scenario: Pi router unavailable for Roger task
- **WHEN** Roger dispatches through Pi and the Pi-level router is unavailable or disabled
- **THEN** Roger SHALL continue using the selected Pi session according to the configured fallback behavior and SHALL make the degraded routing mode visible

### Requirement: Spanish Roger UX with Pi routing
Roger SHALL keep its Spanish user experience while Pi handles work-prompt language and thinking policy.

#### Scenario: Voice preview shown
- **WHEN** Roger previews a captured Spanish instruction before dispatch
- **THEN** Roger SHALL show the original Spanish instruction rather than only the transformed English work prompt

#### Scenario: Clarification needed before dispatch
- **WHEN** Roger cannot choose a safe target domain or context
- **THEN** Roger SHALL ask the clarification in Spanish before sending any transformed prompt to Pi

#### Scenario: Routed task completes
- **WHEN** a Roger-dispatched Pi task completes through the Pi-level router
- **THEN** Roger SHALL present the final user-facing result in Spanish when the Pi router provides a Spanish translation

#### Scenario: Pi router preview requested
- **WHEN** Roger dispatches through Pi while router preview mode is enabled
- **THEN** Roger SHALL expose the translated prompt preview through a visible confirmation surface or SHALL clearly report that preview mode is unavailable for the current Roger entrypoint
