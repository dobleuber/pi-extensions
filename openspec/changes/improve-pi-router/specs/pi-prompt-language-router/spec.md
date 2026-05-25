## ADDED Requirements

### Requirement: Spanish prompt normalization
Pi SHALL allow a Spanish user prompt to be transformed into a concise English work prompt before the selected work model receives it.

#### Scenario: Spanish prompt transformed before dispatch
- **WHEN** the user submits a normal Spanish prompt to Pi
- **THEN** Pi SHALL produce an English work prompt for the selected work model before agent execution begins

#### Scenario: English prompt remains usable
- **WHEN** the user submits a prompt that is already in English
- **THEN** Pi SHALL either pass it through unchanged or normalize it without changing its task intent

#### Scenario: Mixed technical prompt preserves exact tokens
- **WHEN** the user prompt contains file paths, commands, code identifiers, quoted strings, or error messages
- **THEN** Pi SHALL preserve those exact technical tokens in the English work prompt

### Requirement: Context-aware faithful translation
Pi SHALL use conversation context only to resolve references in the current prompt while keeping the translated work prompt faithful to the user's latest message.

#### Scenario: Referenced prior subject resolved
- **WHEN** the user submits a prompt containing a contextual reference such as "eso", "lo anterior", or "la opción 2" and recent conversation context resolves the reference clearly
- **THEN** Pi SHALL use that context to produce an English work prompt with the reference resolved

#### Scenario: Context does not add new requirements
- **WHEN** Pi uses conversation context while translating the current prompt
- **THEN** Pi SHALL NOT add requirements, constraints, or tasks that are not stated by the current prompt or clearly referenced from context

#### Scenario: Ambiguous reference remains unresolved
- **WHEN** the current prompt contains a contextual reference that cannot be resolved confidently
- **THEN** Pi SHALL record the unresolved reference and SHALL avoid inventing a specific intent in the English work prompt

#### Scenario: Context usage recorded
- **WHEN** Pi uses conversation context to translate a prompt
- **THEN** Pi SHALL record whether context was used and which references were resolved or left unresolved in router metadata

### Requirement: Original prompt traceability
Pi SHALL preserve the original user prompt alongside the transformed work prompt for audit, logs, and debugging.

#### Scenario: Routed prompt recorded
- **WHEN** Pi transforms a Spanish prompt into English
- **THEN** Pi SHALL record both the original Spanish prompt and the English work prompt in router metadata or logs

#### Scenario: Retry uses preserved intent
- **WHEN** a routed task is retried or inspected later
- **THEN** Pi SHALL make the original Spanish intent available without requiring the user to reconstruct it

### Requirement: Pre-dispatch router details toggle
Pi SHALL provide an on-demand details toggle that can show the translated English prompt before it is sent to the selected work model.

#### Scenario: Router details created before dispatch
- **WHEN** routing is enabled and Pi translates a normal Spanish prompt
- **THEN** Pi SHALL create a compact router details entry containing the original Spanish prompt, translated English prompt, selected thinking level, and target work model before work-model dispatch

#### Scenario: User expands details before dispatch
- **WHEN** a pre-dispatch router details entry exists and the user expands it through the configured UI control or command
- **THEN** Pi SHALL show the translated English prompt and routing metadata before or during work-model dispatch without requiring a separate preview mode

#### Scenario: Details collapsed by default
- **WHEN** routing is enabled for a normal prompt
- **THEN** Pi SHALL keep router details collapsed by default so routine work is not interrupted

#### Scenario: Details shortcut configurable
- **WHEN** the router details shortcut is configured
- **THEN** Pi SHALL use that shortcut to expand or collapse router details and SHALL avoid silently overriding an existing Pi keybinding without configuration

### Requirement: Final answer Spanish translation
Pi SHALL translate the final user-facing assistant answer back into Spanish when the work model responds in English.

#### Scenario: English final answer translated
- **WHEN** the selected work model completes with an English final answer
- **THEN** Pi SHALL show a Spanish final answer to the user by default

#### Scenario: Technical content preserved in translation
- **WHEN** the final answer contains code blocks, commands, file paths, identifiers, or exact error output
- **THEN** Pi SHALL preserve that technical content while translating surrounding explanatory text into Spanish

#### Scenario: Original answer retained
- **WHEN** Pi translates a final answer into Spanish
- **THEN** Pi SHALL retain the original English answer in metadata, logs, or an inspectable detail view

### Requirement: Router details inspection
Pi SHALL provide an on-demand way to inspect prompt and response routing details without making the default answer noisy.

#### Scenario: Compact answer shown by default
- **WHEN** a routed task completes successfully
- **THEN** Pi SHALL show the Spanish final answer by default without always expanding all routing details inline

#### Scenario: User expands router details
- **WHEN** the user requests expanded routing details through the configured UI control or command
- **THEN** Pi SHALL show the original Spanish prompt, translated English prompt, selected thinking level, work model, original English answer, Spanish answer, and fallback events when available

#### Scenario: Non-interactive details recorded
- **WHEN** Pi runs in print or RPC mode and an interactive details view is unavailable
- **THEN** Pi SHALL record router details in metadata, logs, or structured output that the caller can inspect

### Requirement: Language router fallback
Pi SHALL degrade visibly when prompt or answer translation cannot be completed.

#### Scenario: Router model unavailable before dispatch
- **WHEN** the local router model is unavailable before prompt translation
- **THEN** Pi SHALL either pass the original prompt through unchanged with a visible warning or stop with a clear router-unavailable message according to configuration

#### Scenario: Final translation unavailable
- **WHEN** the work model completes but final-answer translation fails
- **THEN** Pi SHALL show the original work-model answer and a visible note that Spanish translation failed

#### Scenario: Translation timeout
- **WHEN** the router model does not respond within the configured timeout
- **THEN** Pi SHALL apply the configured fallback behavior and SHALL NOT hang the user interaction indefinitely

### Requirement: Command and template safety
Pi SHALL avoid translating inputs where raw syntax has command semantics unless a safe post-expansion path is explicitly supported.

#### Scenario: Slash command submitted
- **WHEN** the user submits a Pi slash command
- **THEN** Pi SHALL NOT translate the command name or command arguments before Pi command dispatch

#### Scenario: Prompt template submitted
- **WHEN** the user submits a prompt template invocation
- **THEN** Pi SHALL preserve the template invocation semantics and SHALL NOT corrupt template expansion through translation
