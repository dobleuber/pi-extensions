## Purpose

Define Jev work-profile decisions whenever routing is on while preserving explicit user control, deterministic execution constraints, and observable fallback behavior.

## ADDED Requirements

### Requirement: Routing uses Jev directly
The router SHALL use Jev for routed prompts without a separate activation mode or approval flag. Jev SHALL NOT control router enablement, native command handling, or authorization to execute a task.

#### Scenario: Router disabled
- **WHEN** an ordinary prompt is submitted while the router is off
- **THEN** no input decision request is made and the prompt passes through

#### Scenario: Router command received
- **WHEN** a router or native control command is received
- **THEN** deterministic command handling applies without asking Jev to interpret the command

### Requirement: Select only approved eligible profiles
The router SHALL provide Jev with approved profile keys and meaningful suitability criteria. Application policy SHALL map accepted keys to concrete provider/model identities and thinking levels, and enforce eligibility and spending constraints independently of Jev. Undefined or ineligible profiles SHALL NOT be dispatched.

#### Scenario: Approved profile selected
- **WHEN** Jev selects an eligible profile with sufficient certainty under the configured policy
- **THEN** the router resolves and verifies its application-owned model and thinking configuration before dispatch

#### Scenario: Terra selected
- **WHEN** Jev selects `terra` or a prompt begins with `Use Terra:` or `Usa Terra:` followed by task text
- **THEN** the router applies `openai-codex/gpt-5.6-terra` with medium reasoning, subject to model availability

#### Scenario: Unexpected selection
- **WHEN** Jev returns an unknown or ineligible key
- **THEN** the router rejects the selection and applies deterministic fallback rather than interpreting it as a model name

### Requirement: Task-based classification rubric
The catalog SHALL contain Luna Max (`gpt-5.6-luna`, max), Terra Medium (`gpt-5.6-terra`, medium), Vega (`gpt-6-astra`, low), and Astra Medium (`gpt-6-astra`, medium), all under `openai-codex`. Criteria SHALL describe tasks, not comparative model capability. Luna SHALL cover clearly scoped implementation, bug fixes, tests, documentation, reviews, bounded refactors, and moderately complex work with clear acceptance criteria; it SHALL NOT be restricted to trivial edits or advertised as a low-latency choice. Terra SHALL cover bounded integration decisions, multiple-hypothesis debugging, migrations, and design trade-offs. Vega SHALL cover focused difficult bugs and subtle localized changes with precise success conditions, without sustained exploration. Astra SHALL cover novel architecture, broad migrations, cross-subsystem debugging, and ambiguous end-to-end work requiring sustained planning and verification.

#### Scenario: Clearly specified multi-file implementation
- **WHEN** a task follows established patterns across several files with clear acceptance criteria
- **THEN** Luna remains a suitable choice; file count alone does not require escalation

#### Scenario: Versioned criteria
- **WHEN** the four-choice task rubric is supplied to Jev
- **THEN** diagnostics identify rubric v2 and catalog v2

### Requirement: Explicit profiles take precedence
An explicit leading profile directive SHALL override automatic recommendations only for the current prompt. `Use Default:` and its supported Spanish equivalent SHALL always force Luna, not request automatic selection. Other supported directives SHALL force their mapped profiles. A prompt without a directive SHALL use automatic selection regardless of earlier explicit choices; profile choices are never persisted as session or global preferences. Neither explicit nor automatic choices SHALL change Pi's global startup preference.

#### Scenario: Explicit profile conflicts with recommendation
- **WHEN** the current prompt contains a supported leading profile directive and Jev recommends another profile
- **THEN** the explicit profile remains authoritative for that prompt

#### Scenario: Default directive
- **WHEN** the current prompt starts with `Use Default:` followed by task text
- **THEN** Luna is selected regardless of Jev's recommendation

#### Scenario: Prompt after an explicit selection
- **WHEN** a prompt with no directive follows a prompt explicitly selecting Astra, Vega, Terra, or Luna
- **THEN** Jev selects for the new prompt without inheriting the earlier forced choice

#### Scenario: Automatic selection followed by another prompt
- **WHEN** Jev selects a profile without an explicit directive on the current prompt
- **THEN** that selection does not become a persistent explicit preference for later prompts

### Requirement: Bounded decisions and deterministic failure handling
Jev calls SHALL have bounded input, time limits, and cancellation. Timeout, invalid output, or insufficient certainty SHALL use a configured deterministic fallback respecting explicit preferences and eligibility constraints. If no permitted profile can be applied, the router SHALL stop dispatch visibly. Cancellation SHALL NOT trigger fallback dispatch of the cancelled prompt.

#### Scenario: Decision timeout
- **WHEN** Jev exceeds the decision deadline
- **THEN** the router uses the permitted deterministic fallback and records the reason

#### Scenario: Cancellation during decision
- **WHEN** the user cancels the prompt while awaiting Jev
- **THEN** the cancelled prompt is not dispatched

#### Scenario: Explicit profile cannot be applied
- **WHEN** the explicitly requested profile fails model application or effective-state verification
- **THEN** the router reports the failure and does not silently substitute another profile

### Requirement: Observable decisions and provider boundaries
The router SHALL expose the effective profile, explicit or automatic decision source, and fallback reasons. Using Jev while routing is on SHALL disclose that bounded prompt/context and response prose may be transmitted to TypeSafe, with credentials managed separately from prompt data. Diagnostics SHALL NOT expose credentials.

#### Scenario: Automatic decision succeeds
- **WHEN** a Jev recommendation is accepted
- **THEN** router details identify the effective profile and automatic selection source

#### Scenario: Credentials unavailable
- **WHEN** TypeSafe credentials are unavailable
- **THEN** the router records an actionable fallback reason without exposing credential values
