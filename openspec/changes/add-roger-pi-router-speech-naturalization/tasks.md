## 1. Contract and Data Model

- [ ] 1.1 Define Roger speech request metadata fields for pi-agent/pi-router dispatch (`source = "roger"`, speech enabled, target language/style as needed).
- [ ] 1.2 Define structured Roger response model with `display_text`, `speech_text`, `speech_language`, and `speech_source`.
- [ ] 1.3 Add parser/normalizer that preserves backward compatibility with legacy plain text pi-agent responses.
- [ ] 1.4 Add unit tests for structured response parsing and plain text fallback.

## 2. pi-router Speech Naturalization

- [ ] 2.1 Extend pi-router to detect Roger speech request metadata without changing non-Roger requests.
- [ ] 2.2 Add pi-router speech naturalization prompt that produces concise Spanish TTS-ready prose while preserving technical Anglicisms, paths, commands, and code identifiers.
- [ ] 2.3 Ensure pi-router uses pi-agent's selected provider/model routing for speech naturalization, including offline `llama-cpp`/`gemma4`.
- [ ] 2.4 Add pi-router tests for English canonical output producing Spanish `speech_text`.
- [ ] 2.5 Add pi-router tests for technical terms such as `README`, `GitHub`, paths, commands, and code identifiers.

## 3. Roger Dispatch Integration

- [ ] 3.1 Update Roger pi RPC dispatch to include Roger speech request metadata only when TTS is enabled.
- [ ] 3.2 Ensure `--no-tts` dispatches do not require speech metadata.
- [ ] 3.3 Update task result handling so Roger displays `display_text` and speaks `speech_text` when structured metadata is present.
- [ ] 3.4 Add CLI/voice/manual loop tests proving Kokoro receives `speech_text`, not canonical `display_text`.

## 4. Remove Incorrect Direct Naturalization Path

- [ ] 4.1 Remove or disable Roger's direct llama.cpp `/v1/chat/completions` naturalizer as the model-backed speech path.
- [ ] 4.2 Remove Roger-side anti-English validation heuristics introduced as a temporary boundary workaround.
- [ ] 4.3 Keep only minimal deterministic local cleanup for non-model formatting fallback when pi-router speech metadata is absent.
- [ ] 4.4 Add tests proving Roger does not call llama.cpp directly for speech naturalization.

## 5. Logging and Degradation

- [ ] 5.1 Record structured speech metadata in task logs when pi-router provides it.
- [ ] 5.2 Keep normal visible log rendering canonical by default.
- [ ] 5.3 Degrade safely when `speech_text` is missing or unusable without changing task completion status.
- [ ] 5.4 Add tests for missing speech metadata, invalid speech metadata, and JSONL speech debugging fields.

## 6. Documentation and Verification

- [ ] 6.1 Update README/setup docs with the Roger ↔ pi-router speech contract.
- [ ] 6.2 Document that model-backed speech naturalization goes through pi-agent/pi-router, not direct Roger llama.cpp calls.
- [ ] 6.3 Run pi-router tests, Roger unit tests, OpenSpec strict validation, and a typed Roger smoke test demonstrating visible `display_text` with spoken/logged `speech_text`.
