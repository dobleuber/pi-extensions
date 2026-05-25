## Context

Roger must keep local/offline speech while delegating model work through pi-agent. The current spoken-output naturalization work exposed a boundary problem: Roger can prepare TTS text by calling the local llama.cpp OpenAI endpoint directly. That duplicates model routing logic, behaves differently from pi-agent/pi-router, and violates the intended architecture that Roger dispatches work through pi-agent.

The correct boundary is for Roger to request a Roger-aware response from pi-agent/pi-router. pi-router can then produce the normal task answer plus a Spanish speech script using the same model/provider routing that pi already controls. Roger remains responsible for local STT/TTS, overlay, preview, and task lifecycle UX; pi-router owns model-backed transformation of task output into a structured response.

## Goals / Non-Goals

**Goals:**

- Add a Roger request metadata contract that asks pi-router for TTS-ready speech output.
- Return structured response fields: `display_text`, `speech_text`, `speech_language`, and `speech_source`.
- Ensure model-backed speech naturalization runs through pi-agent/pi-router, including offline `llama-cpp`/`gemma4` provider routing.
- Preserve canonical visual output in Roger while Kokoro receives `speech_text`.
- Remove Roger-side direct llama.cpp naturalization and fragile language-detection fixes.
- Keep compatibility with existing plain text pi-agent responses.

**Non-Goals:**

- Do not make Kokoro or Roger call cloud TTS/STT.
- Do not require every pi-agent consumer to handle Roger speech metadata.
- Do not change the semantics of normal non-Roger pi-agent tasks.
- Do not force pi-router to translate code, paths, commands, or exact artifacts in `display_text`.
- Do not solve concurrent interruption listening in this change.

## Decisions

### Decision: Structured response contract

pi-router will return a structured Roger response when Roger asks for speech metadata. The minimal shape is:

```json
{
  "display_text": "canonical visible result",
  "speech_text": "Spanish TTS-ready result",
  "speech_language": "es",
  "speech_source": "pi-router"
}
```

Roger will show `display_text` and speak `speech_text`. Existing text-only responses remain supported by treating the plain text as `display_text` and falling back safely for speech.

Alternative considered: encode both fields in Markdown. Rejected because it would leak speech metadata into user-visible text and is brittle to parse.

### Decision: Roger marks requests explicitly

Roger will send request metadata such as `source: "roger"` and `speech.enabled: true` when TTS speech is desired. This keeps pi-router behavior opt-in and avoids changing normal terminal pi behavior.

Alternative considered: infer Roger by prompt wording. Rejected because prompts are user-controlled and unreliable.

### Decision: pi-router owns model-backed naturalization

The speech naturalization prompt and model call belong inside pi-router/pi-agent routing. Roger must not call llama.cpp directly for model-backed naturalization. In offline mode, pi-router uses the configured pi `llama-cpp` provider/model path; online mode can use the selected pi model policy.

Alternative considered: keep direct Roger HTTP calls and improve prompts. Rejected because it duplicates provider lifecycle, bypasses pi permissions/session controls, and already produced behavior mismatches.

### Decision: Roger fallback is minimal

If `speech_text` is absent, malformed, or unavailable, Roger may use minimal deterministic cleanup for local formatting hazards or skip speech, but it must not implement a second model-backed translator or language classifier. Failure to prepare speech must not change the task result.

Alternative considered: add anti-English validation in Roger. Rejected because it blocks valid Anglicisms and solves the wrong layer.

### Decision: Logs record both surfaces

Task logs will record both `display_text` and `speech_text` when present. Normal rendering remains canonical by default, and detailed JSONL can be inspected to debug what reached Kokoro.

## Risks / Trade-offs

- **pi-router response shape breaks legacy clients** → Make structured speech metadata opt-in and keep plain-text compatibility.
- **speech_text missing or delayed** → Roger degrades to visible output plus no speech/minimal fallback without failing the task.
- **model produces poor speech text** → Fix prompt/router behavior in pi-router, not Roger language heuristics; log speech metadata for debugging.
- **extra model work adds latency** → Only request speech metadata when Roger TTS is enabled, and keep speech prompt concise.
- **offline naturalization depends on llama.cpp availability** → Use existing pi fallback/preflight behavior and report degradation visibly.

## Migration Plan

1. Define Roger request metadata and structured response types.
2. Extend pi-router to produce `speech_text` for Roger requests using the selected pi provider/model path.
3. Update Roger pi RPC dispatch to request speech metadata when TTS is enabled.
4. Update Roger result handling to consume `display_text`/`speech_text` and remove direct llama.cpp naturalizer usage.
5. Keep plain text response compatibility and minimal deterministic fallback for missing speech metadata.
6. Add task log fields and tests showing Kokoro receives `speech_text`, not `display_text`.
7. Remove/revert temporary Roger-side anti-English validation hacks introduced while investigating the boundary bug.

## Open Questions

- Exact pi RPC envelope field names: `metadata`, `context`, or a router-specific field may depend on pi RPC extension support.
- Whether pi-router should produce speech metadata in the same turn as the task answer or as a post-processing step before final response emission.
- Whether `speech_text` should include additional metadata such as `speech_style`, `speech_warnings`, or `speech_version` in the first implementation.
