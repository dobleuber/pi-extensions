## Why

Roger currently speaks the same text it shows in the overlay/CLI. That text often contains Markdown, symbols, timestamps, code-ish formatting, or abbreviations that local TTS reads literally, producing unnatural speech such as “asterisco asterisco diez treinta a eme”.

Roger needs a separate speech-rendering step that turns task results into natural Spanish speech while preserving the original exact text visually and in logs.

## What Changes

- Add a spoken-output naturalization step before TTS that converts display text into a speech-friendly Spanish script; spoken prose must be Spanish except for technical anglicisms, product names, commands, paths, and code identifiers.
- Use the local `gemma4`/llama.cpp profile as the preferred naturalizer for completed task summaries, failure summaries, clarifications, and status messages.
- Add deterministic fallback cleanup for common formatting when Gemma/local naturalization is unavailable or times out.
- Preserve canonical written text in preview, overlay, CLI, visible logs, and retry context; only the text sent to TTS may use pronunciation rewrites.
- Store/display original written text and TTS speech text as separate fields when speech naturalization metadata is recorded.
- Normalize common speech-hostile patterns:
  - Markdown emphasis, bullets, headings, and links.
  - Times such as `**10:30 am**` into natural Spanish such as “diez y treinta de la mañana”.
  - Symbols and punctuation that should not be read literally.
  - Anglicisms and technical terms such as `GitHub`, `pull request`, `Docker`, `JSON`, `API`, and `README` into forms that Kokoro’s Spanish pipeline pronounces naturally.
  - Compact technical output into a concise spoken summary instead of reading raw code/logs verbatim.
- Add configurable speech style/prosody profiles for Roger responses.
- Investigate and expose Kokoro controls that are actually supported locally, including voice selection, voice blending, speed, and chunk/sentence splitting.
- Do not claim unsupported Kokoro emotion controls; if explicit emotions are not supported by the installed Kokoro API, approximate tone through prompt naturalization, punctuation, speed, and voice/blend configuration.

## Capabilities

### New Capabilities

- `roger-spoken-output-naturalization`: Defines how Roger converts visual task text into natural TTS-ready Spanish speech using Gemma when available and deterministic fallback cleanup otherwise.
- `roger-tts-prosody-profile`: Defines configurable local Kokoro voice/prosody controls such as voice, voice blend, speed, and response style profiles.

### Modified Capabilities

- `roger-resilient-spoken-output`: Spoken output remains best-effort, but TTS now receives naturalized speech text and visibly reports naturalization degradation separately from TTS synthesis/playback failures.
- `roger-task-progress-log`: Task logs should retain original visual text plus the speech script or naturalization metadata when speech is attempted.
- `roger-voice-interface`: Voice responses should use natural spoken summaries while overlay/CLI continue showing exact task output.

## Impact

- Affected code areas: `src/roger/summarization.py`, `src/roger/tts_speaker.py`, `src/roger/backends/tts_kokoro.py`, `src/roger/config.py`, CLI/voice/manual loop call sites, task logs, and docs.
- External systems: local llama.cpp `gemma4` endpoint for naturalization; Kokoro local TTS API for supported voice/speed controls.
- Tests needed: naturalization fallback tests, Gemma naturalizer timeout/failure tests, TTS call-site tests verifying spoken text differs from visual text, Kokoro voice/speed config tests, and docs/health output tests.
- No breaking change intended: `--no-tts` remains text-only, visual task output remains exact, and TTS degradation still does not change task completion status.
