# Pi Router Model Profiles

## ADDED Requirements

### Requirement: Router-controlled sessions have a deterministic default profile

The router SHALL maintain a model profile for each router-controlled Pi session. When a router-controlled session has no previously selected profile, the router SHALL use the `Luna Max` profile: `openai-codex/gpt-5.6-luna` with `max` thinking. This default SHALL NOT change Pi's global startup model or thinking preference.

#### Scenario: New router-controlled session uses Luna Max

- **WHEN** routing is enabled for a session that has no router-selected profile
- **THEN** the work request SHALL use `openai-codex/gpt-5.6-luna` with `max` thinking
- **AND** the router status/details SHALL identify the active profile as `Luna Max` with source `default`

#### Scenario: Prompt without a model phrase preserves the session profile

- **WHEN** routing is enabled and a prompt does not begin with a supported model phrase
- **THEN** the router SHALL preserve the session's active model profile
- **AND** task complexity, keywords, and router advisories SHALL NOT change that profile

### Requirement: The router SHALL recognize strict English and Spanish model phrases

While routing is enabled, the router SHALL recognize a model-selection phrase only when it is the first non-whitespace content of the latest user prompt, exactly matches `Use Astra:` or `Usa Astra:` (case-insensitively), and is followed by the task text. The router SHALL also recognize the strict reset phrases `Use Default:` and `Usa el modelo predeterminado:`. The router SHALL remove a recognized control phrase from the dispatched task text while retaining the selection in session state and routing details.

The English forms SHALL begin with `Use`; the Spanish forms SHALL begin with `Usa`. No other model name or thinking-level variant SHALL be a supported selection phrase. Model names SHALL be recognized only as complete supported phrases, not as arbitrary model mentions.

#### Scenario: English strict phrase selects Astra

- **WHEN** the latest prompt begins with `Use Astra: ` followed by a task
- **THEN** the router SHALL select the `Astra High` profile for the session
- **AND** the dispatched task text SHALL exclude the leading selection phrase

#### Scenario: Spanish strict phrase selects Astra

- **WHEN** the latest prompt begins with `Usa Astra: ` followed by a task
- **THEN** the router SHALL select the `Astra High` profile for the session
- **AND** the dispatched task text SHALL exclude the leading selection phrase

#### Scenario: Model mention outside the leading phrase is not a selection

- **WHEN** `Astra` appears in the body, quoted text, fenced code, or conversation context rather than in the leading phrase
- **THEN** the router SHALL NOT change the active profile
- **AND** the text SHALL remain part of the task or context according to normal routing behavior

### Requirement: Supported profiles SHALL map to fixed model and thinking combinations

The router SHALL support only these profiles:

| Profile | Selection phrase | Provider/model | Thinking |
|---|---|---|---|
| Luna Max | Default/reset phrases | `openai-codex/gpt-5.6-luna` | `max` |
| Astra High | `Use Astra:` / `Usa Astra:` | `openai-codex/gpt-6-astra` | `high` |

The user-facing profile syntax SHALL NOT expose a phrase for selecting a model-specific thinking level. Luna Max SHALL always use `max`, and Astra SHALL always use `high`.

#### Scenario: Astra uses the fixed high-effort profile

- **WHEN** the user selects `Use Astra:` or `Usa Astra:`
- **THEN** the router SHALL use `openai-codex/gpt-6-astra` with `high`
- **AND** it SHALL NOT raise or lower the thinking level based on task complexity, keywords, or router advisories

### Requirement: Explicit profile selection SHALL persist for the session

A supported model phrase SHALL apply to the current dispatch and SHALL remain the active router profile for later prompts in the same Pi session until another supported profile or the default/reset phrase is selected. A profile selection SHALL NOT be persisted as a global Pi startup setting.

#### Scenario: Explicit Astra selection carries to later prompts

- **WHEN** the user selects `Use Astra:` for one prompt
- **AND** the next prompt contains no model phrase
- **THEN** the next prompt SHALL use `Astra High`

#### Scenario: The default phrase replaces the previous explicit profile

- **WHEN** the active profile is `Astra High`
- **AND** the user begins a later prompt with `Use Default:`
- **THEN** the current and subsequent router-controlled prompts SHALL use `Luna Max`

### Requirement: The default keyword SHALL reset the active profile

The router SHALL support only `Use Default:` and `Usa el modelo predeterminado:` as strict leading reset phrases. A reset SHALL select the configured default profile, which is currently `Luna Max`, for the current dispatch and subsequent prompts in the session. A reset SHALL clear the explicit profile source and SHALL NOT change Pi's global startup setting.

#### Scenario: Default phrase returns from an explicit profile

- **WHEN** the active session profile is `Astra High`
- **AND** the prompt begins with `Use Default: ` followed by a task
- **THEN** the current task SHALL use `Luna Max`
- **AND** subsequent prompts without a model phrase SHALL continue using `Luna Max`
- **AND** routing details SHALL identify the source as `default`

#### Scenario: Spanish default phrase resets the profile

- **WHEN** the prompt begins with `Usa el modelo predeterminado: ` followed by a task
- **THEN** the router SHALL reset the active profile to the configured default
- **AND** the reset phrase SHALL be removed from the dispatched task text

### Requirement: Explicit model selection SHALL be authoritative

When `Use Astra:` or `Usa Astra:` is present, the router SHALL use the requested profile regardless of task complexity, risk classification, keywords, model advisories, or previous automatic policy decisions. The router SHALL NOT automatically promote or demote a session between Luna Max and Astra High profiles.

#### Scenario: A difficult task without a phrase does not auto-select Astra

- **WHEN** a prompt describes a difficult, exhaustive, architectural, or stuck task
- **AND** it contains no supported model phrase
- **THEN** the router SHALL preserve the active session profile
- **AND** it SHALL NOT automatically select Astra High

#### Scenario: Router advisory cannot override an explicit Astra profile

- **WHEN** the user selects `Use Astra:`
- **AND** the router classifies the task as requiring another profile
- **THEN** the work request SHALL still use `Astra High` with `high` thinking

### Requirement: Pi native model controls SHALL be gated by router state

While routing is enabled, the router SHALL own model and thinking selection. Pi's native `/model` and `/thinking` controls SHALL NOT change the active work profile or thinking level, and the user SHALL receive a clear notice that routing must be turned off to use those controls. While routing is disabled, `/model` and `/thinking` SHALL retain their normal Pi behavior.

#### Scenario: Native model control is unavailable while routing is on

- **WHEN** routing is enabled and the user invokes `/model` or `/thinking`
- **THEN** the native selection SHALL NOT be applied
- **AND** the user SHALL be told to turn routing off before using the command

#### Scenario: Native controls work while routing is off

- **WHEN** routing is disabled and the user invokes `/model` or `/thinking`
- **THEN** Pi SHALL handle the command using its normal session behavior
- **AND** the router SHALL NOT intercept or transform the command

### Requirement: The undocumented thinking prefix SHALL no longer control routing

The router SHALL NOT interpret `@thinking:<level>` as a model or thinking control. The removed prefix SHALL NOT change the active profile, thinking level, or session state. Model and thinking choices SHALL be expressed through the documented model-profile phrases or Pi's native controls when routing is off.

#### Scenario: Legacy thinking prefix does not select Astra

- **WHEN** a prompt begins with `@thinking:max` while routing is enabled
- **THEN** the router SHALL NOT select Astra High or any other profile because of that prefix
- **AND** the prefix SHALL NOT alter the session's active thinking level

### Requirement: Explicit profile failures SHALL be visible and non-silent

If the requested provider/model/thinking combination cannot be applied, the router SHALL report the requested profile and failure reason to the user before dispatch. It SHALL NOT silently substitute Luna Max, Astra High, another thinking level, or the previously active profile for that explicitly requested dispatch. The failed request SHALL NOT replace the previously active session profile.

#### Scenario: Requested profile cannot be applied

- **WHEN** the user selects a profile that Pi cannot apply exactly
- **THEN** the router SHALL show a visible error naming the requested profile and failure reason
- **AND** it SHALL NOT dispatch the task under a different profile
- **AND** the previous session profile SHALL remain active for a later retry

### Requirement: Router and work-model responsibilities SHALL remain separate

The remote `openai-codex/gpt-5.6-luna` model with reasoning disabled (`none`) SHALL translate/classify prompts and prepare routing metadata, and SHALL translate English final answers to Spanish when requested. A selected model profile SHALL apply to task execution only and SHALL NOT replace the remote router model or its reasoning setting.

#### Scenario: Work profile selection does not change the router model

- **WHEN** the user selects `Use Astra:`
- **THEN** task execution SHALL use `openai-codex/gpt-6-astra` with `high`
- **AND** prompt routing and final-answer translation SHALL continue using `openai-codex/gpt-5.6-luna` with reasoning disabled (`none`)

### Requirement: Active profile and selection source SHALL be inspectable

Router status and details SHALL expose the active profile, its provider/model identity, thinking level, and source (`default` or `prompt`). Details SHALL distinguish the requested profile from the effective profile when an application failure occurs.

#### Scenario: Details show an explicit Spanish Astra selection

- **WHEN** the user begins a prompt with `Usa Astra:`
- **THEN** router details SHALL show `Astra High`, `openai-codex/gpt-6-astra`, `high`, and source `prompt`

#### Scenario: Details show the default after reset

- **WHEN** the user invokes `Use Default:`
- **THEN** router details SHALL show `Luna Max` and source `default`
