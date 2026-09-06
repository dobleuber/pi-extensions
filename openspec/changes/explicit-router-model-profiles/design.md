## Context

See `proposal.md` for the motivation and `specs/pi-router-model-profiles/spec.md` for the behavioral contract.

The tracked `extensions/pi-router` implementation currently has two separate concerns: the remote `openai-codex/gpt-5.4-mini` router that translates/classifies prompts, and a read-only view of the selected work model. Its input guard passes slash commands through to Pi, and its router configuration has no session work-profile state. The locally installed adaptive router contains a more advanced work-model switching path, but it is materially ahead of tracked `master`; the tracked repository remains the implementation source of truth for this change.

Pi already owns provider authentication, model catalogs, model-specific thinking-level mappings, and native `/model` and `/thinking` controls. The OpenAI Codex profiles needed here are all under the existing `openai-codex` provider. The router must use those existing runtime facilities rather than implement a second provider client or model-availability system.

## Goals / Non-Goals

**Goals:**

- Make router-controlled work-model selection deterministic and session-scoped.
- Apply the default `Luna Max` profile and the explicit `Astra High` profile reliably before dispatch.
- Use remote `openai-codex/gpt-5.6-luna` with reasoning disabled (`none`) as a separate prompt translation/classification component.
- Provide strict English and Spanish leading phrases, including a default/reset phrase.
- Make router ownership of `/model` and `/thinking` explicit while routing is enabled.
- Make requested versus effective profiles visible and testable.
- Document the complete user-facing contract and migration from the removed `@thinking` syntax.

**Non-Goals:**

- Automatic model escalation based on complexity, risk, keywords, task failure, or retry count.
- Replacing the remote router model with Astra.
- Adding a new provider, authentication flow, pricing service, or user-facing availability configuration.
- Persisting the selected profile as a global Pi startup preference.
- Treating arbitrary mentions of model names as selection commands.
- Preserving `@thinking` as a compatibility alias.

## Decisions

### 1. Keep one authoritative session profile

The extension will maintain a router-owned profile state for the active Pi session. The state contains the canonical profile name, provider/model identity, thinking level, and source (`default` or `prompt`). It is initialized to `Luna Max` when router control begins for a session and is held in session state rather than the existing global router on/off state file. A profile transition is recorded as a Pi custom session entry so the same session can recover it after resume/reload; the entry includes the session ID so a new or forked session cannot inherit the parent's selection. The only explicit profile transition is `Use Astra:`/`Usa Astra:`; `Use Default:`/`Usa el modelo predeterminado:` returns to Luna Max.

The profile state is authoritative only while the router is on. A strict model phrase updates the profile before the current prompt is dispatched, so that prompt and all later router-controlled prompts use the same profile. A prompt without a phrase leaves the profile unchanged. `Use Default:` clears the explicit source and replaces the profile with the configured default.

Turning routing off hands model/thinking control back to Pi but does not rewrite the router-owned profile. Turning it on again reapplies the last router profile in that session, or the default if no router profile has been selected. Native changes made while routing is off therefore do not silently become router policy.

This is preferred over writing the profile to the existing file-backed router state because that file is global to the installation and currently stores only the on/off preference. It is also preferred over recalculating a profile on every prompt because recalculation would reintroduce hidden model changes.

```text
session start / router on
          │
          ▼
      Luna Max
          │
   ┌──────┴──────┐
   │             │
model phrase   no phrase
   │             │
update profile  keep profile
   │             │
   └──────┬──────┘
          ▼
   apply profile, dispatch
```

### 2. Use a fixed two-profile catalog and a strict leading parser

A small profile catalog will map the two supported profiles to canonical provider/model/thinking combinations. The catalog is the only source used by the parser and application layer, which prevents spelling variants from becoming separate policies.

The parser will examine only the latest raw user prompt, before router translation and before conversation context is added. It will accept a case-insensitive phrase at the first non-whitespace position, require the exact supported control phrase and colon, and remove the recognized control phrase before the task is sent to the remote router and work model. Text elsewhere—including quoted text, fenced code, and context summaries—will not be parsed.

The supported mappings are:

| Profile | Selection phrase | Canonical provider/model | Thinking |
|---|---|---|---|
| Luna Max | default/reset phrases | `openai-codex/gpt-5.6-luna` | `max` |
| Astra High | `Use Astra:` / `Usa Astra:` | `openai-codex/gpt-6-astra` | `high` |

`Use Default:` and `Usa el modelo predeterminado:` map to the configured default profile rather than hard-coding a second reset implementation. English phrases begin with `Use`; Spanish phrases begin with `Usa`. No other model or thinking-level selection phrase is supported.

A supported phrase represents a complete fixed model/effort choice. There will be no separate prompt-level `@thinking` parser, and the router’s advisory thinking level will not mutate the selected profile. This is preferred over accepting arbitrary natural-language mentions because a phrase such as “do not use Astra” or a quoted example must not unexpectedly change the session model.

### 3. Apply profiles through Pi’s model runtime, not direct HTTP

The work-model application path will resolve the canonical provider/model through Pi’s existing model registry and apply the model and thinking level through the Pi runtime. The adapter will perform these operations in this order:

1. Resolve the requested canonical profile.
2. Resolve the provider/model through Pi’s registry.
3. Apply the model to the Pi session.
4. Apply the profile’s thinking level.
5. Read back the effective provider/model and thinking level.
6. Dispatch only after the effective state matches the requested profile.

If any step fails, the request will stop before dispatch, retain the prior session profile, and show the requested profile plus the failure reason. No direct OAuth/token handling will be added. This provider-aware path is required for `openai-codex` because Luna and Astra use Pi’s Codex Responses integration rather than the tracked router’s local OpenAI-compatible HTTP endpoint. Before dispatch, the existing provider registry must expose `gpt-6-astra`; if it does not, the explicit Astra request fails visibly rather than creating a second availability system.

The prompt router and final-answer translator both use the remote `openai-codex/gpt-5.6-luna` model with `reasoningEffort: "none"`, following the approved cost/latency comparison. This is independent of the Luna Max work profile, which uses the same model with `max` thinking. Each call resolves that model with the host Pi model registry, obtains current credentials with `getApiKeyAndHeaders()`, and invokes the host-compatible `complete()` adapter. The extension does not construct provider URLs, read OAuth tokens, or configure a local HTTP endpoint. Selecting Astra changes only the work-model execution path; it does not change the remote model used to translate/classify prompts or translate final answers.

### 4. Gate native model controls at the input boundary

The input handler will recognize `/model` and `/thinking` as control commands before the general router bypass check. When routing is on, it will consume those commands, notify the user that routing must be turned off, and leave the router profile unchanged. The `/router` command itself must remain available so the user can turn routing off. Other Pi commands continue through the existing command path.

When routing is off, the handler will return control to Pi unchanged, so `/model` and `/thinking` retain native Pi behavior. Native changes made in this mode will not update the router-owned profile; re-enabling routing reclaims model/thinking control by reapplying the session profile.

This explicit gate is necessary because the tracked input guard currently passes slash commands through and does not by itself enforce router ownership.

### 5. Keep model selection separate from prompt transformation

The input pipeline will have a distinct selection stage before translation:

```text
raw input
  │
  ├─ router/off and native-command guards
  ├─ strict profile extraction and session-state update
  ├─ remote gpt-5.6-luna translation/classification (reasoning: none)
  ├─ profile application and effective-state verification
  └─ work-model dispatch
```

The extracted phrase and profile source will be passed as metadata, not as task content. The existing translation result may still provide language and workflow information for display, but it cannot select a different model. This separation prevents a more capable work model from becoming an accidental replacement for the cheap control-plane router.

### 6. Make the effective profile visible

Status and router-detail entries will display the profile label, canonical provider/model, thinking level, and source. During application, requested and effective identities will be retained separately so a mismatch cannot be hidden by a generic fallback message. Profile changes and reset operations will be visible before dispatch, while task text shown to the work model will not contain the control phrase.

The documentation will use the same profile catalog as the runtime contract. The README will include a profile table, English/Spanish examples, session lifetime, router-on/off behavior, reset semantics, failure behavior, removal of `@thinking`, and the distinction between Pi-native controls and router phrases.

### 7. Reconcile tracked and installed implementations without importing unrelated behavior

Implementation work will first establish the tracked `extensions/pi-router` path as the source of truth. The installed adaptive implementation will be used only as a reference for provider-aware model resolution, effective-model verification, and diagnostic fields. Unrelated installed behavior—such as additional compaction handling, speech changes, or broader adaptive execution modes—will not be copied into this change.

This avoids maintaining two conflicting model policies and keeps the change focused on explicit session profiles.

## Risks / Trade-offs

- **[Pi runtime APIs differ between the tracked extension’s peer version and the installed adaptive copy] →** Isolate model application behind a small runtime adapter, inject it in tests, and fail visibly when required model or thinking APIs are unavailable.
- **[The active Pi model can diverge while routing is off] →** Keep a separate router-owned session profile, reapply it when routing resumes, and display requested versus effective identity.
- **[Strict phrases could still be mistaken for task content] →** Require leading position, complete allowlisted profile names, and a colon; parse only the latest raw prompt and test quoted/code/context cases.
- **[Astra has materially higher token rates than Luna] →** Make Luna Max the only implicit default, require an explicit `Use Astra:`/`Usa Astra:` phrase, avoid automatic escalation, and document the cost distinction.
- **[Removing `@thinking` may surprise users who discover the undocumented syntax later] →** Remove the parser and document the replacement profile phrases and Pi-native controls clearly; do not silently map the old prefix to Astra.
- **[Blocking `/model` and `/thinking` while routing is on can make the session feel locked] →** Keep `/router off` available, show an actionable notice, and document the ownership boundary prominently.
- **[The installed extension and tracked source can drift again] →** Add tests and documentation only to the tracked implementation, and make source reconciliation an explicit implementation task.

## Migration Plan

1. Implement the two-profile catalog and session state with Luna Max as the initial default.
2. Add strict English/Spanish extraction for `Use Astra:`/`Usa Astra:` and the default/reset phrases, phrase removal, profile application, effective-state verification, and router-on command gating.
3. Remove the `@thinking` parsing path and any implicit model switching based on router heuristics.
4. Ensure `gpt-6-astra` is resolvable through Pi’s existing provider registry without adding a separate availability system.
5. Extend status/details and update the router README with the complete two-profile and control contract.
6. Run the existing suite plus new parser, session, command-gating, model-application, failure, and documentation-oriented tests.
7. Deploy without changing the global Pi startup model or the existing router on/off state file. Existing sessions without a recorded router profile begin using Luna Max; recorded selections are restored only for the same session, and users can select Astra explicitly.

Rollback is safe because the new profile is session-scoped and does not introduce a persistent settings migration. Reverting the extension restores the previous router behavior; users can also disable routing and use native Pi controls while diagnosing a rollout.
