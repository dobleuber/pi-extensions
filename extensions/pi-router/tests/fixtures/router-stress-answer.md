# Router Stress Test

This paragraph contains **bold**, *italic*, ~~strikethrough~~, an [external link](https://example.com), inline code such as `completeWithPiRouterModel`, and the path `extensions/pi-router/src/final-answer.ts`.

> Preserve this quotation exactly:
>
> “The router must translate prose but never alter commands, paths, identifiers, placeholders, or code.”

## Checklist

- [x] Spanish → English prompt routing
- [x] English → Spanish final-answer translation
- [ ] Modify `settings.json`
- [ ] Change `openai-codex/gpt-5.6-luna`
- [x] Preserve `§P0§` and `__PI_ROUTER_INLINE_0__`

## Comparison

| Model | Reasoning | Input cost | Output cost | Status |
|---|---:|---:|---:|---|
| `gpt-5.6-luna` | `none` | `$0.20/M` | `$1.20/M` | ✅ active |
| `gpt-5.4-mini` | `minimal` | `$0.75/M` | `$4.50/M` | archived |

### Shell

```bash
cd /home/dobleuber/Projects/personal/pi-extensions
npm test
node --import tsx ./scripts/check-router.ts --model openai-codex/gpt-5.6-luna
printf 'Pi Router: café, niño, acción\n'
```

### TypeScript

```ts
type RouterResult = {
  provider: "openai-codex";
  model: "gpt-5.6-luna";
  reasoningEffort: "none";
  degradedReason?: string;
};

const result: RouterResult = {
  provider: "openai-codex",
  model: "gpt-5.6-luna",
  reasoningEffort: "none",
};

console.log(`${result.provider}/${result.model}`);
```

### JSON

```json
{
  "router": {
    "enabled": true,
    "provider": "openai-codex",
    "model": "gpt-5.6-luna",
    "reasoningEffort": "none"
  },
  "preserve": [
    "extensions/pi-router",
    "completeWithPiRouterModel",
    "__PI_ROUTER_PRESERVED_BLOCK_0__",
    "§P0§"
  ]
}
```

### YAML

```yaml
router:
  state: on
  model: openai-codex/gpt-5.6-luna
  reasoning: none
  fallback: passthrough-with-warning
```

### Diff

```diff
- model: gpt-5.4-mini
- reasoningEffort: minimal
+ model: gpt-5.6-luna
+ reasoningEffort: none
```

### Log output

```text
2026-09-05T18:34:58.123Z INFO  router initialized
2026-09-05T18:34:58.456Z DEBUG model=openai-codex/gpt-5.6-luna reasoning=none
2026-09-05T18:34:59.001Z WARN  untranslated output; showing original
2026-09-05T18:34:59.002Z ERROR fallback=passthrough-with-warning
```

### Structured data

```xml
<router provider="openai-codex" model="gpt-5.6-luna">
  <status>ready</status>
  <reasoning>none</reasoning>
</router>
```

```sql
SELECT provider, model, reasoning_effort
FROM router_runs
WHERE model = 'gpt-5.6-luna'
ORDER BY created_at DESC;
```

### Regex and math

```regex
/^Use (Astra|Default):\s+.+$/i
```

\[
\text{cost}_{1000} =
\frac{T_\text{input}}{10^6} \cdot 0.20 +
\frac{T_\text{output}}{10^6} \cdot 1.20
\]

## International text

Español: **La traducción conserva rutas y comandos.**  
Français: `réponse prête`  
Deutsch: `Änderungen gespeichert`  
Português: `ação concluída`  
日本語: `ルーター準備完了`  
中文: `翻译完成`  
العربية: `تمت الترجمة`  
Emoji: ✅ 🚀 🧪 ⚠️

Final invariant: preserve `extensions/pi-router`, `gpt-5.6-luna`, `reasoningEffort`, `npm test`, code fences, JSON structure, and every placeholder exactly.