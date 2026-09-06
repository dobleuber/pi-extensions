# Pi Router Extension

Pi Router uses the remote `openai-codex/gpt-5.6-luna` model with reasoning disabled (`reasoningEffort: "none"`) for both Spanish→English prompt routing and English→Spanish final-answer translation. Calls resolve the model and current OAuth/API headers through the host Pi model registry, so the extension owns no endpoint URL, token, or local model configuration. Authenticate the `openai-codex` provider in Pi before enabling routing.

The resulting task is sent to a deterministic, session-scoped work-model profile.

Final-answer translation masks technical content before processing prose, including mixed-language answers. The translator returns structured language metadata alongside the Spanish text; unchanged Spanish or language-neutral labels are valid, while unchanged English is reported as a fallback. Already-Spanish prose is checked by the translator rather than bypassed using a whole-answer word heuristic. Language classification remains model-based, so structurally valid output is not a guarantee of semantic accuracy. Generated mask IDs avoid literal placeholder IDs already present in the text, and restoration does not recursively expand inserted content.

Residual-English checks use Unicode words and run only on translated prose, not preserved logs or code. Ordinary Markdown tables are translated with their inline code protected. Repairs operate on bounded affected sections and use the same strict JSON contract as initial translation. If a section or repair fails, its warning remains visible without discarding successful sections or smaller retries; a validated partial translation is retained rather than replaced by a failed repair. Artificial chunk boundaries preserve whitespace and do not split protected placeholders.

## Work-model profiles

| Profile | Supported control | Provider/model | Thinking |
| --- | --- | --- | --- |
| **Luna Max** (default) | `Use Default:` / `Usa el modelo predeterminado:` | `openai-codex/gpt-5.6-luna` | `max` |
| **Astra High** | `Use Astra:` / `Usa Astra:` | `openai-codex/gpt-6-astra` | `high` |

Luna Max is selected when router control starts for a session. Use a supported phrase at the beginning of a prompt to select a profile for that prompt and subsequent routed prompts:

```text
Use Astra: inspect the failing test
Usa Astra: inspecciona el test que falla
Use Default: continue with the normal-cost model
Usa el modelo predeterminado: continúa con el modelo normal
```

Controls are strict, case-insensitive, and must be the first non-whitespace content. The colon is required and task text must follow it. The recognized control is removed before the task reaches the router and work model. Mentions in normal text, quotes, fenced code, or conversation context do not select a profile.

There are no separate user-selectable thinking levels for work-model profiles. The Luna Max work profile always uses `max`; Astra High always uses `high`. Router and translation calls use Luna with reasoning disabled independently of these work-profile settings. Task complexity, keywords, risk, router classifications, and model advisories never promote or demote the profile. The old undocumented `@thinking:<level>` syntax is removed and is not a compatibility alias.

Profile state belongs to the active Pi session. It survives `/router off` followed by `/router on` and is restored when that same session is resumed, but is not written to Pi's global startup model or thinking preference. New and forked sessions start at Luna Max. `Use Default:` resets the session profile and clears the explicit selection source. Native model changes made while routing is off do not become router policy; routing reapplies its session profile when enabled again.

## Command boundary and failures

While routing is **on**, Pi Router owns work-model selection. `/model` and `/thinking` are consumed with a notice directing you to use `/router off` first. `/router off` remains available. While routing is **off**, `/model` and `/thinking` are passed to Pi unchanged.

Before dispatch, Pi Router resolves the exact provider/model through Pi's existing registry, applies the fixed thinking level, and verifies the effective state. If the requested model or thinking level cannot be applied, the request is stopped visibly with the requested profile and reason. It is never silently replaced with another profile, and the previous session profile remains available for retry. The configured registry must expose `openai-codex/gpt-6-astra` for Astra requests.

Router status and expandable details show the active profile, canonical provider/model, thinking level, source (`default` or `prompt`), and requested/effective failure information. The translation/classification router remains separate from the selected work profile.

Astra is opt-in because it is substantially more expensive than Luna in the configured model metadata (approximately `$10/$50` versus `$0.20/$1.20` per million input/output tokens). Check current provider pricing before use.

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
