## Why

Roger will provide a voice-first interface for operating the laptop through pi-agent, enabling hands-free execution of real system and project tasks while keeping speech recognition and speech synthesis local. This solves the gap between terminal-capable agents and day-to-day laptop control: the user wants to speak tasks naturally and have pi execute them with the same permissions and context it has in the terminal.

## What Changes

- Add an always-listening local wake-word flow for the phrase “Hola Roger”.
- Add local voice capture, voice activity detection, speech-to-text, transcription preview, and local text-to-speech output.
- Add benchmarkable, configurable speech backends so wake word, VAD, STT, and TTS tools can be selected empirically rather than hard-coded.
- Add a Roger orchestrator that classifies intent, selects the correct context/session, detects online/offline state, and dispatches work to pi-agent.
- Add separate pi-agent sessions for different laptop contexts, starting with `system` and `current-project`.
- Use the default pi model when online and switch to Ollama only when offline.
- Allow Roger-dispatched pi sessions to perform real tasks with the same permissions as pi in the terminal, including installing software, running commands, editing files, and executing tests.
- Add visible logs/status so spoken responses can stay concise while detailed output remains inspectable.

## Capabilities

### New Capabilities

- `roger-voice-interface`: Always-on local wake word, local instruction capture, transcription preview, and local spoken response.
- `roger-context-routing`: Intent/context classification, session selection, online/offline model selection, and ambiguity handling.
- `roger-agent-execution`: Dispatch to pi-agent sessions with terminal-equivalent permissions, task lifecycle reporting, logs, and response summarization.

### Modified Capabilities

None.

## Impact

- New daemon/orchestrator process for Roger.
- Local audio dependencies for wake word detection, VAD, STT, and TTS, with initial candidates including NanoWakeWord GRU/LSTM/TCN for wake word, Silero/WebRTC VAD, faster-whisper/whisper.cpp, and Kokoro/Piper.
- pi-agent integration through RPC initially, with SDK integration as a future option if tighter lifecycle control is needed.
- Ollama provider configuration for offline fallback.
- Session storage and context registry for `system`, `current-project`, and later domains such as projects, communications, and media generation.
- User-facing terminal/desktop preview for transcribed instructions and task status.
