## Why

Jev offers an opportunity to automate work-model profile selection and avoid unnecessary generative translation calls using fast, typed decisions. Evaluate and integrate it as a decision layer in Pi Router while preserving the existing generative translators, explicit user control, and technical-content integrity.

## What Changes

- Use Jev directly whenever routing is on; remove the legacy persistent-profile path and separate Jev activation/approval flags.
- Evaluate work-profile suitability and prompt translation necessity together in one input-side Jev request. Select among approved profile keys such as Luna, Terra, Vega, and Astra, never free-form provider/model names. Application code continues to own concrete model identities, thinking levels, eligibility, and spending constraints.
- **BREAKING:** Explicit directives force a profile only for the current prompt: `Use Default:` always forces Luna; `Use Astra:`, `Use Vega:`, and other supported directives force their mapped profile. A subsequent prompt without a directive returns to automatic selection. Neither explicit nor automatic choices become persistent preferences; `/router off` remains available.
- Use task-based rubric v2 with Luna Max, Terra Medium (`openai-codex/gpt-5.6-terra`), Vega, and Astra Medium. Luna covers substantive clearly scoped work, not only trivial edits; its criteria contain no latency claim.
- Send the original prompt unchanged when its natural-language instructions do not require English translation; otherwise retain the existing generative prompt translator. Classify instructions separately from quoted examples, code, commands, and logs, without losing context-dependent intent.
- Evaluate outgoing response prose separately, after generation, to determine whether Spanish translation is necessary when Spanish output is required. Leave already-Spanish or language-neutral content unchanged; translate English or other non-Spanish prose through the existing generative translator, including mixed-language responses.
- Keep input translation necessity separate from the desired response language. Skipping input translation must not suppress required Spanish output. Preserve final-answer boundaries and existing Roger speech behavior.
- On Jev failure or insufficient certainty, retain the existing translation path and a deterministic profile fallback that respects explicit overrides and configured constraints. Keep router enablement, command handling, model application, and error policy deterministic.
- Expose selected profile, decision source, translation bypasses, and fallback reasons. Bound the context transmitted to TypeSafe and make the additional provider/authentication and data-sharing requirements explicit.
- Keep offline regression coverage and optional bounded live smoke checks. Expanded evaluations and quantitative release gates were removed from scope by the user. Confidence is not a correctness guarantee.

## Capabilities

### New Capabilities

- `pi-router-jev-profile-selection`: Typed per-prompt profile selection, approved candidates, explicit override precedence, deterministic fallback, and decision visibility.
- `pi-router-jev-translation-gating`: Input and response translation-necessity decisions, independent response-language policy, protected-content handling, and conservative fallback to existing translators.
- `pi-router-jev-evaluation`: Offline fixtures and honest reporting of optional bounded live checks, without a runtime release gate.

### Modified Capabilities

None under `openspec/specs/`. The existing explicit-profile contract lives in the unarchived `explicit-router-model-profiles` change; this change supersedes its persistent-profile/no-automatic-selection policy for the personal router.

## Impact

- Affects `extensions/pi-router/src/pipeline.ts`, profile policy/configuration, input and final-answer integration in `src/index.ts`, decision metadata/details, tests, and README documentation.
- Adds TypeSafe API access through an appropriate client/adapter, with credentials, bounded requests, cancellation, timeouts, and response validation. Jev's typed decision API is separate from the current Pi generative completion path.
- Retains `src/router-model.ts` and `src/final-answer.ts` as generative translation components, including existing preservation and repair safeguards.
- Adds external transmission of bounded prompt/context and response prose to TypeSafe; credential ownership and data-handling expectations must be settled in the design.
- Introduces an input decision call and, when Spanish output is required, a separate response decision call. Translation-heavy workloads may gain overhead; savings must be measured rather than assumed.
- Implementation and local-only deployment were authorized by the user. Git provides rollback; no remote publication or legacy compatibility branch is required.
