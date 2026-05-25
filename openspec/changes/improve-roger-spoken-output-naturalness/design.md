## Context

Roger currently sends the same string to all user-facing surfaces: overlay, CLI, task log, and Kokoro TTS. That works for plain prose but fails for Markdown, code-like output, abbreviations, timestamps, and English technical terms. Kokoro's Spanish pipeline reads many of those tokens literally or with Spanish grapheme-to-phoneme rules, for example `**10:30 am**` as “asterisco asterisco diez treinta a eme” and `GitHub` as “jit ub”.

Kokoro 0.9.4 on this system exposes `voice`, `speed`, `split_pattern`, language-specific pipelines, and voice loading/blending. It does not expose a direct emotion/style API, and its Spanish pipeline does not interpret SSML or `<lang>` tags. The practical control surface is therefore: prepare better text before synthesis, choose voice assets, adjust speed, split text well, and optionally blend voices when multiple compatible voices are installed.

## Goals / Non-Goals

**Goals:**

- Preserve exact written output for preview, overlay, CLI, logs, retry context, and debugging.
- Generate a separate TTS-only speech script that is natural to hear in Spanish.
- Use local `gemma4` through llama.cpp as the preferred speech naturalizer.
- Provide deterministic fallback cleanup for common cases when the local model is unavailable or too slow.
- Improve pronunciation of common anglicisms and technical terms without changing visual spelling.
- Expose Kokoro controls that are actually supported locally: voice, voice blends, speed, and sentence/chunk splitting.
- Keep spoken output best-effort: naturalization or TTS failures must not change task success/failure status.

**Non-Goals:**

- Do not change the text shown in the overlay, CLI, preview, or visible logs to phonetic spellings.
- Do not translate or rewrite source code, shell commands, file paths, exact errors, or generated artifacts in the canonical result.
- Do not claim Kokoro supports emotions/styles if the installed API does not expose them.
- Do not introduce cloud TTS or cloud naturalization.
- Do not route task execution through Gemma; Gemma is only a speech-script helper for this change.

## Decisions

### Decision: Separate display text from speech text

Roger will treat visible output and TTS input as different representations. The display text remains canonical. A new speech-script step receives the display text plus a purpose such as completion, failure, clarification, goodbye, or status, and returns TTS-ready Spanish.

Alternatives considered:

- Rewrite the final response before display: rejected because it would corrupt Markdown, commands, paths, and retry/debug context.
- Teach Kokoro to ignore Markdown directly: not available through the current Kokoro API.

### Decision: Use a local speech naturalizer with deterministic fallback

The preferred naturalizer will call the local llama.cpp `gemma4` endpoint with a bounded timeout and instructions to produce only a short Spanish speech script. If unavailable, Roger falls back to deterministic cleanup for Markdown stripping, punctuation cleanup, common time formats, and a small anglicism pronunciation dictionary.

Alternatives considered:

- Rules only: fast and reliable, but insufficient for varied task summaries and natural Spanish phrasing.
- Gemma only: better phrasing, but local model availability and latency must not block speech.

### Decision: Preserve anglicisms visually and pronounce them only in speech script

Technical terms such as `GitHub`, `pull request`, `README`, `API`, `JSON`, and `Docker` stay unchanged in visible output. The speech script may render them as pronunciation aids such as “guit jab”, “pul ricuest”, “ridmi”, “ei pi ai”, “yéison”, and “dóker” when that sounds better through Kokoro's Spanish pipeline.

Alternatives considered:

- Use Kokoro's English pipeline for English terms: technically possible, but it requires additional English voices, segment-level synthesis, and audio stitching; it risks jarring voice changes. This can be explored later.
- SSML language tags: tested conceptually against Kokoro's pipeline behavior and rejected because tags are read literally.

### Decision: Expose prosody as supported Kokoro controls, not fake emotions

Roger will add config for `speech.tts.speed`, optional `speech.tts.split_pattern`, and voice/voice-blend values. Named profiles such as `neutral`, `brief`, `warm`, or `urgent` may map to naturalizer instructions and speed changes, but the implementation must label them as Roger speech profiles rather than Kokoro emotions.

Alternatives considered:

- Add an `emotion` config field: rejected because it implies direct Kokoro support that is not present.
- Ignore prosody: simpler, but speed and phrasing are useful for a voice assistant.

### Decision: Record naturalization metadata without making logs noisy

Task logs can store original display text, speech text, naturalizer source (`gemma` or `fallback`), and degradation reasons. CLI and overlay should normally show only canonical text plus any warnings; detailed speech script can be available in structured logs for debugging.

Alternatives considered:

- Always show speech text: rejected because phonetic spellings look wrong and can confuse the user.
- Never record speech text: makes pronunciation bugs hard to debug.

## Risks / Trade-offs

- **Gemma rewrites meaning** → Keep prompts strict, cap length, preserve display text, and fall back to deterministic rules on malformed output.
- **Naturalization adds latency** → Use short bounded timeouts, deterministic fallback, and possibly skip Gemma for very short/simple strings.
- **Phonetic anglicism spellings are subjective** → Start with a small configurable dictionary and tests for common developer terms.
- **Speech script may leak into UI** → Use separate data fields and tests that overlay/CLI keep canonical text.
- **Kokoro voice/prosody support is limited** → Document only supported controls and avoid unsupported emotion claims.

## Migration Plan

1. Add a speech-script abstraction and deterministic fallback cleaner behind existing `summarize_for_speech`/speaker call sites.
2. Add optional local Gemma naturalizer with bounded timeout and clear degradation behavior.
3. Update TTS call sites so overlay/CLI/log text remains canonical while TTS receives speech text.
4. Extend Kokoro adapter/config for supported speed, split pattern, and voice/blend controls.
5. Record speech naturalization metadata in task logs when available.
6. Update docs with examples and troubleshooting guidance.
7. Rollback by disabling Gemma naturalization and using deterministic cleanup or existing concise summary behavior.

## Open Questions

- What exact anglicism pronunciation dictionary should be the default for this user? Initial candidates include GitHub, pull request, README, API, JSON, Docker, commit, branch, fork, login, token, and repo.
- Should Gemma naturalization run for every spoken message or only for task/failure summaries longer than a small threshold?
- Should additional Kokoro voices be downloaded locally to enable better voice blends, or should the first implementation stay with `ef_dora` only?
