## 1. Speech Naturalization Core

- [ ] 1.1 Add a `SpeechScript`/naturalization data model that keeps canonical display text separate from TTS speech text.
- [ ] 1.2 Add deterministic fallback cleanup for Markdown emphasis, bullets/headings, links, repeated punctuation, and symbol-only formatting.
- [ ] 1.3 Add deterministic cleanup for common time formats such as `10:30 am` into natural Spanish speech.
- [ ] 1.4 Add a configurable anglicism pronunciation dictionary for terms such as `GitHub`, `pull request`, `README`, `API`, `JSON`, `Docker`, `commit`, `branch`, and `fork`.
- [ ] 1.5 Add tests proving preview/overlay/CLI/log display text stays canonical while TTS text uses pronunciation rewrites.

## 2. Local Gemma Naturalizer

- [ ] 2.1 Add a local llama.cpp/Gemma speech naturalizer client with bounded timeout, maximum input size, and clear error reporting.
- [ ] 2.2 Add prompt instructions that request concise Spanish speech scripts while preserving meaning and avoiding code/path/command corruption.
- [ ] 2.3 Validate naturalizer output and fall back when it is empty, malformed, too long, or rejected by safety heuristics.
- [ ] 2.4 Add config flags for enabling/disabling Gemma naturalization, timeout, model/provider/base URL, and fallback behavior.
- [ ] 2.5 Add tests for successful Gemma naturalization, server unavailable, timeout, invalid output, and deterministic fallback.

## 3. Speaker and Call-Site Integration

- [ ] 3.1 Update `summarize_for_speech` or introduce a dedicated speech-preparation service used by task, manual loop, voice loop, daemon, `say`, and failure/clarification paths.
- [ ] 3.2 Update `SafeSpeaker`/speaker call sites to pass canonical display text and generated speech text separately when available.
- [ ] 3.3 Ensure `--no-tts` skips naturalization as well as synthesis/playback.
- [ ] 3.4 Add degradation warnings for naturalization failures without changing task completion status.
- [ ] 3.5 Add tests for completed task, failed task, clarification, goodbye/status, and typed `roger say` flows.

## 4. Kokoro Prosody Controls

- [ ] 4.1 Extend TTS config with supported Kokoro controls: speed, split pattern, and voice/voice-blend value.
- [ ] 4.2 Pass speed and split pattern to `KPipeline.__call__`.
- [ ] 4.3 Preserve existing local voice asset resolution behavior and support comma-separated voice blends when assets are available.
- [ ] 4.4 Add health/docs output that reports supported Kokoro controls without claiming unsupported emotion/style APIs.
- [ ] 4.5 Add tests for speed, split pattern, single voice, voice blend, and missing voice reporting.

## 5. Task Log and Visibility

- [ ] 5.1 Extend task log events/details to store canonical display text, speech text, naturalizer source, style profile, and degradation reason.
- [ ] 5.2 Keep normal task log rendering canonical by default and expose speech-script details only in structured metadata or detailed inspection.
- [ ] 5.3 Ensure overlay and CLI continue showing exact written output, not phonetic pronunciation spellings.
- [ ] 5.4 Add tests for task log metadata and visible rendering behavior.

## 6. Documentation and Verification

- [ ] 6.1 Update README/setup docs with the display-text vs speech-text contract and examples such as `**10:30 am**`, `GitHub`, and `README`.
- [ ] 6.2 Document Kokoro supported controls and explain that explicit emotion/tone controls are not available in the installed API.
- [ ] 6.3 Document local Gemma naturalization prerequisites, fallback behavior, and troubleshooting commands.
- [ ] 6.4 Run the full unit suite, focused TTS/naturalization tests, offline Roger smoke test, and OpenSpec strict validation.
