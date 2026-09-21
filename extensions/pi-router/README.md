# Pi Router Extension

Pi Router uses the remote `openai-codex/gpt-5.6-luna` model with reasoning disabled (`reasoningEffort: "none"`) for both Spanish→English prompt routing and English→Spanish final-answer translation. Calls resolve the model and current OAuth/API headers through the host Pi model registry, so the extension owns no endpoint URL, token, or local model configuration. Authenticate the `openai-codex` provider in Pi before enabling routing.

Jev selects an application-mapped work-model profile for each prompt; explicit leading directives override that selection.

Final-answer translation masks technical content before processing prose, including mixed-language answers. The translator returns structured language metadata alongside the Spanish text; unchanged Spanish or language-neutral labels are valid, while unchanged English is reported as a fallback. Already-Spanish prose is checked by the translator rather than bypassed using a whole-answer word heuristic. Language classification remains model-based, so structurally valid output is not a guarantee of semantic accuracy. Generated mask IDs avoid literal placeholder IDs already present in the text, and restoration does not recursively expand inserted content.

Residual-English checks use Unicode words and run only on translated prose, not preserved logs or code. Ordinary Markdown tables are translated with their inline code protected. Repairs operate on bounded affected sections and use the same strict JSON contract as initial translation. If a section or repair fails, its warning remains visible without discarding successful sections or smaller retries; a validated partial translation is retained rather than replaced by a failed repair. Artificial chunk boundaries preserve whitespace and do not split protected placeholders.

## Work-model profiles

| Profile | Provider/model | Thinking | Tasks Jev assigns to this profile |
| --- | --- | --- | --- |
| **Luna Max** (default) | `openai-codex/gpt-5.6-luna` | `max` | Clearly scoped implementation, bug fixes, tests, documentation, reviews, bounded refactors, and moderately complex work with clear acceptance criteria—even across multiple files. Not limited to trivial changes; no low-latency claim. |
| **Terra Medium** | `openai-codex/gpt-5.6-terra` | `medium` | Bounded integration decisions, multiple-hypothesis debugging, dependency/API migrations, and subsystem design trade-offs. |
| **Vega** (Astra Low) | `openai-codex/gpt-6-astra` | `low` | Focused difficult bugs, subtle localized correctness changes, and constrained investigation with precise success conditions rather than sustained exploration. |
| **Astra Medium** | `openai-codex/gpt-6-astra` | `medium` | Novel architecture, broad migrations, cross-subsystem debugging, and ambiguous end-to-end workflows requiring sustained planning and verification. |

Luna Max is selected when router control starts for a session. Use a supported phrase at the beginning of a prompt to select a profile for that prompt only:

```text
Use Astra: inspect the failing test
Usa Astra: inspecciona el test que falla
Use Vega: use the lower-effort Astra profile
Usa Vega: usa el perfil Astra de menor esfuerzo
Use Default: continue with the normal-cost model
Usa el modelo predeterminado: continúa con el modelo normal
```

Controls are strict, case-insensitive, and must be the first non-whitespace content. The colon is required and task text must follow it. The recognized control is removed before the task reaches the router and work model. Mentions in normal text, quotes, fenced code, or conversation context do not select a profile.

Work-model thinking is fixed by the selected profile: Luna Max uses `max`, Astra Medium uses `medium`, and Vega uses `low` with the Astra model. Router and translation calls use Luna with reasoning disabled independently of these work-profile settings. Jev classifies task requirements using a versioned rubric; the application maps its approved profile key to a fixed model and thinking level. The old undocumented `@thinking:<level>` syntax is removed and is not a compatibility alias.

Profiles are per-prompt, not sticky session preferences. New, resumed, and forked sessions start at Luna Max; unqualified routed prompts use Jev selection. `Use Default:` forces Luna only for its prompt. Native model changes while routing is off do not become router policy.

## Command boundary and failures

While routing is **on**, Pi Router owns work-model selection. `/model` and `/thinking` are consumed with a notice directing you to use `/router off` first. `/router off` remains available. While routing is **off**, `/model` and `/thinking` are passed to Pi unchanged.

Before dispatch, Pi Router resolves the exact provider/model through Pi's existing registry, applies the fixed thinking level, and verifies the effective state. If the requested model or thinking level cannot be applied, the request is stopped visibly with the requested profile and reason. It is never silently replaced with another profile, and the previous session profile remains available for retry. The configured registry must expose `openai-codex/gpt-6-astra` for Astra requests.

Router status and expandable details show the active profile, canonical provider/model, thinking level, source (`default` or `prompt`), and requested/effective failure information. The translation/classification router remains separate from the selected work profile.

Astra can be selected by Jev or an explicit directive and is substantially more expensive than Luna in the configured model metadata (approximately `$10/$50` versus `$0.20/$1.20` per million input/output tokens). Check current provider pricing before use.

Model and task assignments are application policy categories, not OpenAI benchmarks. Model references: [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna), [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra), and [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra). Terra uses the documented default medium reasoning; Luna retains max.

## Jev decisions

`/router on` uses Jev (`jev-1.13.0`) directly for per-prompt profile selection and independent input/response translation decisions. There is no separate Jev mode, activation flag, or approval gate. `/router off` disables prompt routing.

`maxProfileCostTier` is an application-owned deterministic filter: Luna is tier 1, Terra and Vega tier 2, and Astra tier 3. `Use Default:` forces Luna for the current prompt; other supported directives force their mapped profile for that prompt. The next unqualified prompt returns to Jev selection. Profile choices are not persisted or restored from session entries and do not change global model preferences.

While routing is on, bounded task/context state and the masked final-response prose may be sent to TypeSafe's `/v1/systemone`. Set `TYPESAFE_API_KEY` in the process environment; it is resolved by the SDK and is never included in Jev state or router details. Jev requests use an explicit model, disabled retries, size bounds, cancellation, and a deadline. A timeout, invalid/uncertain answer, missing credential, or unavailable model keeps the existing generative translator and falls back to Luna; an explicit profile application failure stops dispatch instead of substituting another profile. Use `/router off` to stop routing. Revert the code in Git to restore an earlier implementation.

## Install during development

Load directly while developing:

```bash
pi -e ./extensions/pi-router/src/index.ts
```

For persistent local use, copy or symlink this package into an auto-discovered Pi extension location such as:

```text
~/.pi/agent/extensions/pi-router/
```

Pi reads the installable entrypoint from `package.json`:

```json
{
  "pi": {
    "extensions": ["./src/index.ts"]
  }
}
```

## Tests

```bash
npm install
npm test
```
