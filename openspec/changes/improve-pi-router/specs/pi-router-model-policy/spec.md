## ADDED Requirements

### Requirement: Local router model configuration
Pi SHALL use a configurable local router model profile for prompt translation, answer translation, and thinking classification.

#### Scenario: Default local router model configured
- **WHEN** the router loads its default configuration
- **THEN** Pi SHALL use the local llama.cpp `gemma4` profile as the router model unless configuration overrides it

#### Scenario: Router endpoint configured
- **WHEN** the router model is configured
- **THEN** Pi SHALL know the router provider, model name, base URL, timeout, and fallback mode needed to call it

#### Scenario: Router model separated from work model
- **WHEN** the router uses local `gemma4` for translation or classification
- **THEN** Pi SHALL NOT change the selected work model solely because the router model is `gemma4`

### Requirement: Work model independence
Pi SHALL send routed prompts to the work model selected by normal Pi model-selection mechanisms.

#### Scenario: User selected existing Pi default
- **WHEN** the user has not selected a special work-model profile
- **THEN** Pi SHALL dispatch the translated English prompt to Pi's currently selected default work model

#### Scenario: User selected Stratus
- **WHEN** the user selects a Stratus model or Stratus provider profile and Stratus is available
- **THEN** Pi SHALL dispatch the translated English prompt to Stratus as the work model

#### Scenario: User switches model mid-session
- **WHEN** the user changes the Pi work model using normal Pi controls
- **THEN** Pi SHALL keep using the selected work model while continuing to use the configured router model for routing tasks

### Requirement: Stratus compatibility
Pi SHALL treat Stratus as a supported work-model target for routed prompts without making Stratus credits a prerequisite for router operation.

#### Scenario: Stratus credits available
- **WHEN** Stratus credentials and credits are available and the user selects Stratus for work
- **THEN** Pi SHALL route translated English prompts to Stratus without additional user translation steps

#### Scenario: Stratus credits unavailable
- **WHEN** Stratus is selected but unavailable due to missing credits or provider failure
- **THEN** Pi SHALL report the work-model availability failure and SHALL NOT treat it as a router translation failure

#### Scenario: Non-Stratus work model selected
- **WHEN** the user selects a non-Stratus work model
- **THEN** Pi SHALL continue routing prompts and final answers using the same router policy

### Requirement: Router enablement controls
Pi SHALL provide controls for turning routing off or on without using a separate preview mode.

#### Scenario: Router disabled globally
- **WHEN** router configuration sets the default state to `off`
- **THEN** Pi SHALL send prompts to the selected work model without translation or automatic thinking selection

#### Scenario: Router enabled for session
- **WHEN** the user enables routing for the current session
- **THEN** Pi SHALL translate and classify normal prompts according to router policy until routing is disabled or bypassed

#### Scenario: Single prompt bypass
- **WHEN** the user marks one prompt to bypass routing
- **THEN** Pi SHALL send that prompt to the selected work model without translation or automatic thinking selection while preserving the session's router state

#### Scenario: Inspection remains separate from enablement
- **WHEN** the user expands or collapses router details
- **THEN** Pi SHALL NOT treat that inspection action as changing whether routing is enabled

### Requirement: Router observability and bypass
Pi SHALL provide visible router status and a way to bypass routing when necessary.

#### Scenario: Router active
- **WHEN** the router is enabled for a session
- **THEN** Pi SHALL expose that routing is active and identify the router model in status, logs, or diagnostics

#### Scenario: User bypasses router
- **WHEN** the user disables the router for a session, prompt, or launch profile
- **THEN** Pi SHALL send the user's prompt to the selected work model without translation or automatic thinking selection

#### Scenario: Router decision inspected
- **WHEN** the user or developer inspects a routed task
- **THEN** Pi SHALL expose the router model, work model, source language, target language, response language, selected thinking level, and fallback status when available

#### Scenario: Router status shown
- **WHEN** router state changes between `off` and `on`
- **THEN** Pi SHALL show the current state in status, logs, or diagnostics
