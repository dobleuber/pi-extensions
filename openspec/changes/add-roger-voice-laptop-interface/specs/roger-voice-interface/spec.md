## ADDED Requirements

### Requirement: Wake word activation
Roger SHALL continuously listen for the local wake phrase “Hola Roger” using a local wake-word mechanism before capturing a user instruction.

#### Scenario: Wake phrase detected
- **WHEN** the user says “Hola Roger” near the laptop microphone
- **THEN** Roger SHALL enter instruction capture mode

#### Scenario: Wake phrase not detected
- **WHEN** ambient speech or noise does not match “Hola Roger” above the configured threshold
- **THEN** Roger SHALL remain in wake-word listening mode and SHALL NOT dispatch any instruction to pi-agent

### Requirement: Wake architecture evaluation
Roger SHALL support evaluating NanoWakeWord GRU, LSTM, and TCN architectures before selecting the default “Hola Roger” wake backend.

#### Scenario: Wake phrase configured
- **WHEN** NanoWakeWord training is configured for the wake-word spike
- **THEN** Roger SHALL use `hola roger` as the target phrase

#### Scenario: Wake negatives configured
- **WHEN** NanoWakeWord training data is generated
- **THEN** Roger SHALL include automatic adversarial negatives, phoneme adversarial negatives, and manual nearby negatives for phrases that should not activate Roger

#### Scenario: Wake engine benchmark executed
- **WHEN** the wake-word spike is run
- **THEN** Roger SHALL measure or record false positives, false negatives, activation latency, idle CPU, memory usage, and custom model training effort for NanoWakeWord GRU, LSTM, and TCN

#### Scenario: Wake engine selected
- **WHEN** the wake-word benchmark identifies a candidate that reliably detects “Hola Roger” within acceptable resource usage
- **THEN** Roger SHALL make that engine configurable as the default wake-word backend

#### Scenario: NanoWakeWord candidates fail
- **WHEN** NanoWakeWord GRU, LSTM, and TCN all fail to meet wake-word reliability or resource targets
- **THEN** Roger MAY evaluate openWakeWord or a temporary trigger as a fallback without expanding the first NanoWakeWord spike scope

### Requirement: Local instruction capture
After wake activation, Roger SHALL capture a single spoken instruction locally and stop capture when voice activity detection identifies the end of speech.

#### Scenario: User finishes speaking instruction
- **WHEN** Roger is in instruction capture mode and the user stops speaking for the configured silence interval
- **THEN** Roger SHALL stop recording and SHALL pass the captured audio to local speech-to-text

#### Scenario: No instruction after wake
- **WHEN** Roger enters instruction capture mode but no speech is detected within the configured timeout
- **THEN** Roger SHALL return to wake-word listening mode without dispatching a task

### Requirement: VAD backend evaluation
Roger SHALL support evaluating at least Silero VAD and WebRTC VAD for instruction capture.

#### Scenario: VAD benchmark executed
- **WHEN** the VAD spike is run
- **THEN** Roger SHALL compare endpoint detection accuracy, silence cutoff behavior, latency, CPU usage, and robustness to laptop background noise

#### Scenario: VAD backend selected
- **WHEN** a VAD backend provides acceptable endpoint detection for spoken instructions
- **THEN** Roger SHALL make that backend configurable for instruction capture

### Requirement: Local speech transcription
Roger SHALL transcribe captured instructions using a local speech-to-text backend that can operate without internet connectivity.

#### Scenario: Instruction transcribed successfully
- **WHEN** captured audio contains intelligible speech
- **THEN** Roger SHALL produce a text transcription without using a cloud STT service

#### Scenario: Transcription fails or is low confidence
- **WHEN** the local STT backend cannot produce a usable transcription
- **THEN** Roger SHALL report the failure locally and return to wake-word listening mode without dispatching a task

### Requirement: STT backend evaluation
Roger SHALL support evaluating at least faster-whisper and whisper.cpp before selecting the default local speech-to-text backend.

#### Scenario: STT benchmark executed
- **WHEN** the STT spike is run with Spanish spoken instructions
- **THEN** Roger SHALL compare transcription accuracy, latency, CPU/GPU usage, installation complexity, and offline behavior for each candidate backend

#### Scenario: STT backend selected
- **WHEN** a local STT backend provides acceptable Spanish accuracy and latency
- **THEN** Roger SHALL make that backend configurable as the default transcription backend

### Requirement: Transcription preview before dispatch
Roger SHALL show the recognized instruction to the user before dispatching it to pi-agent.

#### Scenario: Preview shown
- **WHEN** Roger has a transcription ready for dispatch
- **THEN** Roger SHALL display the transcription in a visible preview surface

#### Scenario: User cancels preview
- **WHEN** the transcription preview is visible and the user cancels or rejects it
- **THEN** Roger SHALL discard the instruction and return to wake-word listening mode

#### Scenario: User accepts or does not cancel preview
- **WHEN** the transcription preview is visible and the user accepts it or the configured preview timeout elapses without cancellation
- **THEN** Roger SHALL dispatch the transcribed instruction to the router

### Requirement: Local spoken response
Roger SHALL produce spoken responses using a local text-to-speech backend that can operate without internet connectivity.

#### Scenario: Task response available
- **WHEN** pi-agent produces a final response or status summary for a dispatched task
- **THEN** Roger SHALL speak a concise response through local TTS

#### Scenario: TTS unavailable
- **WHEN** the local TTS backend is unavailable or fails
- **THEN** Roger SHALL keep the textual response visible and SHALL NOT block task completion

### Requirement: TTS backend evaluation
Roger SHALL support evaluating at least Kokoro and Piper before selecting the default local text-to-speech backend.

#### Scenario: TTS benchmark executed
- **WHEN** the TTS spike is run with Spanish Roger responses
- **THEN** Roger SHALL compare voice quality, latency, CPU/GPU usage, package maintenance status, licensing, and offline behavior for each candidate backend

#### Scenario: TTS backend selected
- **WHEN** a local TTS backend provides acceptable Spanish quality and latency
- **THEN** Roger SHALL make that backend configurable as the default spoken-response backend

### Requirement: Speech backend adapters
Roger SHALL isolate wake-word, VAD, STT, and TTS engines behind backend adapters.

#### Scenario: Backend changed by configuration
- **WHEN** the configured backend for wake-word, VAD, STT, or TTS is changed
- **THEN** Roger SHALL use the new backend without requiring changes to routing or pi-agent execution logic

### Requirement: Return to listening after one instruction
For the MVP, Roger SHALL handle one instruction per wake activation and then return to wake-word listening.

#### Scenario: Task dispatch cycle completes
- **WHEN** Roger has dispatched one instruction and handled the resulting final response or error
- **THEN** Roger SHALL return to wake-word listening mode
