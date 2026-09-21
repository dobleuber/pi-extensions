## Purpose

Define honest, reproducible offline verification and bounded optional smoke checks for the personal router. Expanded comparative evaluation and quantitative release gates are out of scope at the user's request.

## ADDED Requirements

### Requirement: Independently labeled offline cases
Offline fixtures SHALL cover approved profile keys, explicit overrides, language decisions, and failure paths. Expected choices SHALL be independent of classifier outputs. Fixtures SHALL reflect rubric v2, including substantive clearly scoped Luna tasks and Terra integration tasks.

#### Scenario: Multiple acceptable profiles
- **WHEN** more than one profile is suitable for a fixture
- **THEN** the reference may record an acceptable set instead of inventing a unique ground truth

### Requirement: No runtime evaluation gate
Routing SHALL NOT require quantitative release approval, an evaluation-only mode, or a Jev activation flag. `/router on` SHALL use Jev directly. Offline scores and live smoke checks SHALL NOT be represented as proof of downstream coding quality.

#### Scenario: Router enabled
- **WHEN** the user enables the router
- **THEN** Jev decisions are used without a separate evaluation approval requirement

### Requirement: Bound optional live checks
Live checks SHALL be explicitly requested, bounded, and use synthetic or approved data. Reports SHALL distinguish decision-only latency from end-to-end latency and distinguish measured usage from estimated cost. Private transcripts SHALL NOT be uploaded merely because they are locally accessible.

#### Scenario: Small smoke sample
- **WHEN** a small set of live classifier calls succeeds
- **THEN** the report describes only the observed behavior and does not claim representative quality or latency guarantees

### Requirement: Preserve deterministic failure handling
Offline tests SHALL verify timeouts, malformed choices, unavailable profiles, explicit overrides, cancellation, state bounds, and queued-turn isolation. Credentials SHALL remain excluded from state and diagnostics.

#### Scenario: Invalid decision
- **WHEN** Jev returns an invalid selection
- **THEN** tests verify Luna fallback and retained generative translation without dispatching an unapproved model
