## 1. Project Foundation

- [x] 1.1 Choose the implementation runtime and create the initial project structure for the Roger daemon/orchestrator.
- [x] 1.2 Add dependency and environment management for local audio, speech backends, pi RPC, tests, and benchmark scripts.
- [x] 1.3 Add configuration loading for speech backends, model paths, thresholds, session registry, and online/offline model settings.
- [x] 1.4 Add a basic CLI entrypoint that can run health checks and individual spikes without starting the full daemon.

## 2. Wake Word Spike

- [x] 2.1 Create NanoWakeWord training configuration for `target_phrase: "hola roger"` with fixed positives.
- [x] 2.2 Add automatic adversarial, phoneme adversarial, and manual nearby negatives for `hola roger`.
- [x] 2.3 Train or document reproducible training for NanoWakeWord GRU.
- [x] 2.4 Train or document reproducible training for NanoWakeWord LSTM.
- [x] 2.5 Train or document reproducible training for NanoWakeWord TCN.
- [x] 2.6 Build a benchmark harness that measures false positives, false negatives, activation latency, idle CPU, memory usage, and training effort for GRU, LSTM, and TCN.
- [ ] 2.7 Select the default wake architecture or record why a fallback trigger/openWakeWord baseline is required.

## 3. Speech Backend Spikes

- [x] 3.1 Implement a VAD benchmark comparing Silero VAD and WebRTC VAD for end-of-instruction detection.
- [x] 3.2 Select the default VAD backend and record thresholds for silence timeout and noise robustness.
- [x] 3.3 Implement an STT benchmark comparing faster-whisper and whisper.cpp on Spanish laptop-control instructions.
- [x] 3.4 Select the default STT backend and record model size, latency, accuracy, CPU/GPU usage, and install complexity.
- [x] 3.5 Implement a TTS benchmark comparing Kokoro and Piper for short Spanish Roger responses.
- [x] 3.6 Select the default TTS backend and record voice quality, latency, CPU/GPU usage, package status, licensing, and offline behavior.

## 4. Speech Backend Adapters

- [ ] 4.1 Define wake-word, VAD, STT, and TTS adapter interfaces.
- [ ] 4.2 Implement the selected wake-word adapter and a temporary manual trigger adapter for development.
- [ ] 4.3 Implement the selected VAD adapter.
- [ ] 4.4 Implement the selected STT adapter.
- [ ] 4.5 Implement the selected TTS adapter.
- [ ] 4.6 Add adapter-level tests or smoke checks for backend initialization, inference, failure handling, and configuration switching.

## 5. pi-agent Integration

- [ ] 5.1 Implement a JSONL RPC client for `pi --mode rpc` that can start pi, send prompts, read streamed events, and stop cleanly.
- [ ] 5.2 Implement session creation/reuse for separate `system` and `current-project` pi-agent contexts.
- [ ] 5.3 Implement online/default pi model selection and offline Ollama fallback selection.
- [ ] 5.4 Add smoke tests for prompt dispatch, streamed response capture, tool-event logging, task completion, and pi-agent failure reporting.

## 6. Router and Session Registry

- [ ] 6.1 Implement the initial context registry with `system` and `current-project` domains.
- [ ] 6.2 Implement rule-based routing for system tasks such as install, uninstall, update, kill app, and laptop-level management.
- [ ] 6.3 Implement rule-based routing for current-project tasks such as edit files, create demos, inspect code, and run tests.
- [ ] 6.4 Implement ambiguity handling that asks for clarification when the target domain or project cannot be resolved confidently.
- [ ] 6.5 Add routing tests for system, current-project, and ambiguous instructions.

## 7. Transcription Preview and Logs

- [ ] 7.1 Implement a visible transcription preview surface with accept, cancel, and timeout behavior.
- [ ] 7.2 Ensure cancelled previews are not dispatched to pi-agent.
- [ ] 7.3 Implement a task log surface that displays pi-agent text, tool events, command output, errors, and completion status.
- [ ] 7.4 Implement concise response summarization rules so long logs are not spoken by default.

## 8. MVP Manual Loop

- [ ] 8.1 Build a manual-trigger flow that accepts typed or simulated transcriptions and dispatches them through preview, router, pi-agent, log, and TTS.
- [ ] 8.2 Verify the manual loop for a `current-project` task.
- [ ] 8.3 Verify the manual loop for a `system` task that does not require destructive changes.
- [ ] 8.4 Verify failure handling when pi-agent is unavailable.

## 9. MVP Voice Loop

- [ ] 9.1 Connect wake detection to instruction capture.
- [ ] 9.2 Connect VAD-based instruction capture to local STT.
- [ ] 9.3 Connect STT output to transcription preview.
- [ ] 9.4 Connect accepted preview output to router and pi-agent dispatch.
- [ ] 9.5 Connect pi-agent final status to local TTS.
- [ ] 9.6 Ensure Roger handles one instruction per wake activation and returns to wake-word listening after completion or error.

## 10. Verification and Documentation

- [ ] 10.1 Document setup steps for local wake-word, VAD, STT, TTS, pi RPC, and Ollama fallback.
- [ ] 10.2 Document benchmark results and selected defaults.
- [ ] 10.3 Run OpenSpec validation for `add-roger-voice-laptop-interface`.
- [ ] 10.4 Run the project test/smoke suite and record the commands used.
- [ ] 10.5 Update the OpenSpec tasks as complete when implementation work is verified.
