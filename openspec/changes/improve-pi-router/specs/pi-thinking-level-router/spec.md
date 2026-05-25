## ADDED Requirements

### Requirement: Prompt-aware thinking selection
Pi SHALL select a thinking level for each normal user prompt based on prompt complexity, ambiguity, risk, and expected tool use.

#### Scenario: Simple prompt selects low thinking
- **WHEN** the user asks a greeting, short factual question, status check, or other simple low-risk task
- **THEN** Pi SHALL select `low` thinking for the work-model turn when the active model supports it

#### Scenario: Routine coding task selects medium thinking
- **WHEN** the user asks for a routine coding, documentation, test, or OpenSpec artifact task with clear requirements
- **THEN** Pi SHALL select `medium` thinking for the work-model turn when the active model supports it

#### Scenario: Complex task selects high thinking
- **WHEN** the user asks for architecture work, multi-file refactoring, ambiguous debugging, performance analysis, security-sensitive changes, or high-impact/destructive operations
- **THEN** Pi SHALL select `high` thinking for the work-model turn when the active model supports it

#### Scenario: Uncertain classification is conservative
- **WHEN** Pi cannot confidently classify the prompt complexity
- **THEN** Pi SHALL select at least `medium` thinking rather than under-allocating reasoning budget

### Requirement: Thinking application through Pi interfaces
Pi SHALL apply the selected thinking level through Pi's supported model controls before the work model processes the transformed prompt.

#### Scenario: Interactive extension applies thinking
- **WHEN** the router runs inside an interactive Pi extension
- **THEN** Pi SHALL apply the selected level using the runtime thinking-level API before agent execution starts

#### Scenario: CLI or wrapper applies thinking
- **WHEN** the router runs through a Pi CLI wrapper or launch profile
- **THEN** Pi SHALL apply the selected level using `--thinking` or model `:<thinking>` shorthand when available

#### Scenario: RPC client applies thinking
- **WHEN** the router runs for an RPC-based Pi session
- **THEN** Pi SHALL apply the selected level using the RPC thinking-level command before sending the transformed prompt

### Requirement: Thinking capability fallback
Pi SHALL handle models that do not support the requested thinking level without failing the task solely because of thinking selection.

#### Scenario: Active model clamps thinking
- **WHEN** the selected work model does not support the requested thinking level
- **THEN** Pi SHALL allow Pi's model capability handling to clamp or disable thinking and SHALL continue the task

#### Scenario: Thinking control unavailable
- **WHEN** the current Pi entrypoint cannot apply thinking controls
- **THEN** Pi SHALL continue with the transformed prompt and record that thinking selection could not be applied

### Requirement: Thinking decision visibility
Pi SHALL make the requested thinking level and its selection reason visible for diagnostics and later review.

#### Scenario: Thinking level selected
- **WHEN** Pi selects a thinking level for a routed prompt
- **THEN** Pi SHALL record the requested level and a concise reason in router metadata or task logs

#### Scenario: Effective thinking differs
- **WHEN** the effective thinking level differs from the router-requested level
- **THEN** Pi SHALL record both the requested and effective levels when the effective level is observable
