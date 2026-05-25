## 1. Speech Naturalization Core

- [x] 1.1 Add a `SpeechScript`/naturalization data model that keeps canonical display text separate from TTS speech text.
- [x] 1.2 Add deterministic fallback cleanup for Markdown emphasis, bullets/headings, links, repeated punctuation, and symbol-only formatting.
- [x] 1.3 Add deterministic cleanup for common time formats such as `10:30 am` into natural Spanish speech.
- [x] 1.4 Add a configurable anglicism pronunciation dictionary for terms such as `GitHub`, `pull request`, `README`, `API`, `JSON`, `Docker`, `commit`, `branch`, and `fork`.
- [x] 1.5 Add tests proving preview/overlay/CLI/log display text stays canonical while TTS text uses pronunciation rewrites.

## 2. Local Gemma Naturalizer

- [x] 2.1 Add a local llama.cpp/Gemma speech naturalizer client with bounded timeout, maximum input size, and clear error reporting.
- [x] 2.2 Add prompt instructions that request concise Spanish speech scripts while preserving meaning and avoiding code/path/command corruption.
- [x] 2.3 Validate naturalizer output and fall back when it is empty, malformed, too long, or rejected by safety heuristics.
- [x] 2.4 Add config flags for enabling/disabling Gemma naturalization, timeout, model/provider/base URL, and fallback behavior.
- [x] 2.5 Add tests for successful Gemma naturalization, server unavailable, timeout, invalid output, and deterministic fallback.

## 3. Speaker and Call-Site Integration

- [x] 3.1 Update `summarize_for_speech` or introduce a dedicated speech-preparation service used by task, manual loop, voice loop, daemon, `say`, and failure/clarification paths.
- [x] 3.2 Update `SafeSpeaker`/speaker call sites to pass canonical display text and generated speech text separately when available.
- [x] 3.3 Ensure `--no-tts` skips naturalization as well as synthesis/playback.
- [x] 3.4 Add degradation warnings for naturalization failures without changing task completion status.
- [x] 3.5 Add tests for completed task, failed task, clarification, goodbye/status, and typed `roger say` flows.

## 4. Kokoro Prosody Controls

- [x] 4.1 Extend TTS config with supported Kokoro controls: speed, split pattern, and voice/voice-blend value.
- [x] 4.2 Pass speed and split pattern to `KPipeline.__call__`.
- [x] 4.3 Preserve existing local voice asset resolution behavior and support comma-separated voice blends when assets are available.
- [x] 4.4 Add health/docs output that reports supported Kokoro controls without claiming unsupported emotion/style APIs.
- [x] 4.5 Add tests for speed, split pattern, single voice, voice blend, and missing voice reporting.

## 5. Task Log and Visibility

- [x] 5.1 Extend task log events/details to store canonical display text, speech text, naturalizer source, style profile, and degradation reason.
- [x] 5.2 Keep normal task log rendering canonical by default and expose speech-script details only in structured metadata or detailed inspection.
- [x] 5.3 Ensure overlay and CLI continue showing exact written output, not phonetic pronunciation spellings.
- [x] 5.4 Add tests for task log metadata and visible rendering behavior.

## 6. Documentation and Verification

- [x] 6.1 Update README/setup docs with the display-text vs speech-text contract and examples such as `**10:30 am**`, `GitHub`, and `README`.
- [x] 6.2 Document Kokoro supported controls and explain that explicit emotion/tone controls are not available in the installed API.
- [x] 6.3 Document local Gemma naturalization prerequisites, fallback behavior, and troubleshooting commands.
- [x] 6.4 Run the full unit suite, focused TTS/naturalization tests, offline Roger smoke test, and OpenSpec strict validation.
