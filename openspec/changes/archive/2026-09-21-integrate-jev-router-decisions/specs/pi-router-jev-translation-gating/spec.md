## Purpose

Avoid unnecessary generative translation on incoming prompts and outgoing responses while preserving target-language policy, user intent, and protected technical content.

## ADDED Requirements

### Requirement: Combine input decisions
When the router is on for a routed prompt, the router SHALL evaluate profile suitability and input translation necessity in the same input-side Jev request rather than independent requests. Explicit-profile precedence SHALL still apply.

#### Scenario: Input needs both decisions
- **WHEN** a routed prompt requires automatic profile selection and a translation check
- **THEN** one input-side Jev request evaluates both questions

### Requirement: Gate English prompt translation
The router SHALL bypass generative input translation only when the decision policy accepts that the task instructions need no English translation. Bypass SHALL preserve the task text after deterministic control-prefix removal. Spanish or mixed-language instructions requiring translation SHALL use the existing generative translator. Quoted examples and technical content SHALL NOT alone determine the language of the task instructions.

#### Scenario: English instructions with Spanish evidence
- **WHEN** English task instructions contain a quoted Spanish example that must remain literal
- **THEN** the quote alone does not require translating the English instructions or altering the quoted example

#### Scenario: Spanish instructions with English code
- **WHEN** Spanish task instructions contain English identifiers or code
- **THEN** the instructions are translated while protected technical content remains unchanged

#### Scenario: Technical-only prompt
- **WHEN** the prompt contains only code, commands, or logs and no prose requiring translation
- **THEN** an accepted bypass decision forwards the task text unchanged

#### Scenario: Ambiguous contextual instruction
- **WHEN** bounded context is insufficient to decide whether a follow-up can safely bypass prompt transformation
- **THEN** the router retains the existing generative path rather than inventing intent or assuming translation is unnecessary

### Requirement: Preserve independent response-language policy
The requirement for Spanish response output SHALL be determined independently from whether input translation was bypassed. Jev's input decision SHALL NOT disable Spanish output required by the existing user or Roger response policy.

#### Scenario: Input bypass with Spanish output required
- **WHEN** an English prompt bypasses translation but the response policy requires Spanish
- **THEN** the generated final response remains eligible for a Spanish translation check

### Requirement: Evaluate final response separately
When Spanish output is required, the router SHALL evaluate the generated final response prose in a separate response-side Jev decision. Accepted already-Spanish or language-neutral output SHALL bypass generative translation. Responses containing non-Spanish prose, including mixed-language responses, SHALL retain the generative Spanish translation path. Jev SHALL NOT generate the translated response.

#### Scenario: Already-Spanish response
- **WHEN** final response prose is already Spanish and the bypass policy accepts the decision
- **THEN** the original response is retained without a generative translation call

#### Scenario: Mixed-language response
- **WHEN** a final response contains both Spanish and English prose
- **THEN** existing Spanish is preserved and non-Spanish prose is passed through the existing translation path

#### Scenario: Spanish prose with English technical content
- **WHEN** a Spanish response contains English code, commands, identifiers, or preserved logs
- **THEN** protected technical content alone does not require translating the response

### Requirement: Preserve lifecycle and content boundaries
Response gating SHALL apply only to the intended final response, not commentary or tool-call content. It SHALL preserve protected content, formatting safeguards, queued-turn association, and Roger display/speech behavior. Input and response decisions SHALL remain associated with their originating turn.

#### Scenario: Tool continuation or commentary
- **WHEN** an assistant message is commentary or contains a tool call rather than the final answer
- **THEN** it is not treated as a final-response translation-gating target

#### Scenario: Roger response bypasses translation
- **WHEN** a Roger response is already Spanish and generative translation is bypassed
- **THEN** the required display/speech response contract remains intact

### Requirement: Conservative gating failures
Invalid, incomplete, low-certainty, oversized, or timed-out decisions SHALL NOT authorize translation bypass. The router SHALL retain the corresponding existing generative path and its failure handling. A decision based on a partial response SHALL NOT justify bypassing translation for unexamined prose. Cancellation SHALL stop further work for the cancelled operation.

#### Scenario: Response check fails
- **WHEN** Jev cannot provide an acceptable response translation decision
- **THEN** the existing Spanish translator is used and the fallback reason is recorded

#### Scenario: Response exceeds decision bounds
- **WHEN** the full response prose cannot be evaluated within the configured bounds
- **THEN** the router does not infer that the unexamined remainder needs no translation

### Requirement: Translation decisions are observable
Router details SHALL record whether input and response translation were performed or bypassed and whether fallback was used, without conflating the two directions.

#### Scenario: Different decisions in each direction
- **WHEN** input translation is bypassed but response translation is performed
- **THEN** details display the two outcomes separately
