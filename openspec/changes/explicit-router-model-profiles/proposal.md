## Why

The router’s current adaptive model policy changes work models indirectly from task heuristics, but it makes model choice difficult to predict and cost control opaque. The router should instead use a cheap, stable routing layer with an explicit, session-scoped two-profile policy: Luna Max by default, with Astra High selected only when the user asks for it.

## What Changes

- Replace automatic work-model upgrades and downgrades with a deterministic two-profile policy.
- Start each router-controlled session with `gpt-5.6-luna` at `max` thinking as the default `Luna Max` profile.
- Recognize only these strict leading phrases, in English or Spanish, before translating or dispatching the task:
  - `Use Astra: ...` / `Usa Astra: ...`, selecting the fixed `Astra High` profile
  - `Use Default: ...` / `Usa el modelo predeterminado: ...`, selecting the configured default `Luna Max` profile and clearing the explicit session override.
- Apply an explicit profile to the current dispatch and retain it for subsequent prompts in the same session; new sessions begin with the default profile. Do not change Pi’s global startup default.
- Make an explicit profile authoritative: task complexity, router advisories, and keyword heuristics must not replace it with another model. A complex task without `Use Astra:` remains on the active profile.
- Report a visible error if an explicitly requested profile cannot be applied; do not silently substitute another model.
- Keep Pi’s native `/model` and `/thinking` controls available only while the router is off. While the router is on, the router-controlled profile is authoritative.
- Remove the undocumented `@thinking:<level>` syntax and the implicit model-selection behavior formerly attached to it or to unstructured model mentions.
- Use the remote `openai-codex/gpt-5.6-luna` model with reasoning disabled (`none`) for prompt translation/classification and final-answer translation; model profiles select the work model and its thinking level, not the router’s own model or reasoning setting.
- Ensure model phrases are recognized only at the strict leading position of the latest user prompt, never in quoted text, code, conversation context, or translated output.
- Update router status/details, tests, README documentation, and migration guidance so the two supported phrases, fixed thinking levels, precedence, session lifetime, reset behavior, errors, and router-on/off control boundary are fully documented.

## Capabilities

### New Capabilities

- `pi-router-model-profiles`: Session-scoped explicit Luna Max/Astra High profile selection, English/Spanish strict phrases, default/reset behavior, precedence, and failure handling.

### Modified Capabilities

<!-- No existing pi-router capability specification exists under openspec/specs/. -->

## Impact

- Affects the `extensions/pi-router` model-selection policy, input parsing, session state, Pi model/thinking control handling, status/details metadata, tests, and README documentation.
- Requires provider-aware resolution of the existing OpenAI Codex model identities and fixed thinking-level mappings for Luna Max and Astra High, while adding no new provider or user-facing availability system.
- Changes the behavior of router-controlled sessions and removes the undocumented `@thinking` interface.
- The tracked router implementation and the locally installed adaptive router currently differ; implementation must reconcile the intended source of truth rather than maintain two independent policies.
