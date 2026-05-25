## Context

The current Roger work lives in `pi-extensions`, but this change targets Pi usage in general, not only Roger. Pi already exposes the extension hooks needed for a router-style workflow: `input` can transform user text before agent processing, `message_end` can replace finalized assistant messages, `pi.setThinkingLevel()` can apply `low`/`medium`/`high`, model selection can remain under Pi's normal `/model`, `--model`, and provider mechanisms, and RPC mode exposes `set_thinking_level` for embedded clients.

The user's preferred language is Spanish. The desired work model prompt language is English because coding agents and many model/provider combinations tend to perform better with precise English instructions. The local `gemma4` model served through llama.cpp is already part of the environment and should be used as the low-cost routing model for translation/classification. Stratus is part of the intended workflow, but is temporarily unavailable because credits are exhausted; the design must keep Stratus usable as a normal work-model target once credits return.

## Goals / Non-Goals

**Goals:**

- Let the user write normal Pi prompts in Spanish while the work model receives a concise English task prompt.
- Use concise conversation context to resolve references like “eso”, “lo anterior”, or “opción 2” without adding new requirements to the translated prompt.
- Allow routing to be turned on or off globally, per session, and for a single prompt.
- Provide an on-demand router details toggle that can show the translated English prompt before work-model dispatch and show routing/final-answer details after completion.
- Translate final assistant answers back into Spanish for user comfort.
- Preserve original Spanish prompts, transformed English prompts, selected thinking levels, final English answers, and fallback reasons for traceability.
- Select `low`, `medium`, or `high` thinking per prompt to reduce unnecessary reasoning-token use while still giving complex tasks enough budget.
- Work across interactive Pi, print mode, and RPC-based integrations where Pi extension hooks or RPC commands are available.
- Keep Stratus compatible as a work-model provider/model; the router should not assume the work model is only Anthropic/OpenAI/local.
- Let Roger consume the same Pi-level routing behavior instead of maintaining a separate Roger-only language router.

**Non-Goals:**

- Do not replace Pi's provider/model registry or force every task onto Stratus.
- Do not translate source code, shell commands, file paths, error output, quoted literals, or generated artifact bodies when preserving them verbatim is more useful.
- Do not use conversation summary to reinterpret the user's latest prompt or add requirements that are not stated or clearly referenced.
- Do not make `gemma4` the work model by default; it is the routing/translation/classification model unless the user explicitly selects it for work.
- Do not introduce a separate `preview` router mode; inspection is a UI toggle layered on top of normal enabled routing.
- Do not change Pi's core model APIs unless an extension/wrapper cannot satisfy the requirement.
- Do not implement full semantic project routing in this change; domain/session routing remains a separate concern.

## Decisions

### Decision: Implement the first version as a global Pi extension

Implement the router as a TypeScript Pi extension installed globally under `~/.pi/agent/extensions/pi-router/` or packaged for reuse. The extension can run in normal Pi sessions and does not require users to launch a separate wrapper for everyday use.

The extension will use:

- `input` to intercept normal user prompts, skip extension commands/slash commands, and transform Spanish text into an English work prompt.
- A compact router details surface that is collapsed by default and can be expanded with a shortcut/command to show the translated prompt before dispatch and final routing details after completion.
- `pi.setThinkingLevel()` to apply the selected thinking level before the agent turn starts.
- `message_end` to translate user-facing assistant text back to Spanish while preserving code blocks, paths, commands, and structured technical content.
- `pi.appendEntry()` or custom displayed metadata to record router decisions without polluting the model context.
- A custom message renderer, widget, or command to expose router details in an expandable/collapsible view similar in spirit to Pi's Ctrl+O tool-output and Ctrl+T thinking-block inspection flows.
- `model_select` and `thinking_level_select` to show status/diagnostics when useful.

Alternatives considered:

- A shell wrapper around `pi`: simpler to prototype but incomplete for interactive follow-ups, model changes, and RPC sessions.
- Direct Pi core changes: more powerful but unnecessary until extension hooks prove insufficient.
- A Roger-only implementation: rejected because the requirement is Pi-wide.

### Decision: Support explicit router enable/disable controls

The router should support enabled and disabled states rather than a separate preview mode:

- `off`: no translation and no automatic thinking selection; Pi behaves like normal.
- `on`: translate/classify automatically and dispatch through the selected work model.

Configuration should allow a default global state and session-level override. Interactive users should also have commands or shortcuts to toggle routing on/off. Single prompts should support a bypass prefix or command so the user can intentionally send raw input without changing the session default.

Prompt/response inspection is handled by a separate router details toggle, not by changing the router mode.

Alternatives considered:

- Always-on routing with no bypass: convenient but risky when the user wants exact prompt wording.
- A separate preview mode: rejected because the desired UX is closer to Pi's existing expand/collapse controls than to a persistent mode.
- Only per-prompt routing: too much friction for the user's primary Spanish workflow.

### Decision: Use local `gemma4` as the router model through llama.cpp

The router should call the local llama.cpp OpenAI-compatible endpoint for translation and classification. `gemma4` will produce a structured router result containing:

- detected input language,
- English work prompt,
- selected thinking level,
- short reason for the level,
- whether final response translation should be applied,
- whether conversation context was used,
- resolved references and unresolved ambiguities,
- warnings or fallback hints.

The router call must be bounded by a timeout and a maximum input size. The request may include a concise conversation summary or recent-session context, but router instructions must state that this context is only for reference resolution. If context cannot resolve a reference safely, the router should report an unresolved reference rather than inventing intent. If local `gemma4` is unavailable, the router should either pass the original prompt through unchanged with a visible warning or ask the user to disable/repair the router, depending on configuration.

Alternatives considered:

- Use the selected work model for translation: wastes Stratus/cloud tokens and can degrade the work prompt before the real task starts.
- Use static string translation rules: too brittle for natural Spanish prompts.
- Require the user to write English manually: rejected because it defeats the purpose.

### Decision: Keep the work-model policy separate from router translation

The router should not automatically replace the user's selected Pi model. It should transform the prompt and thinking level, then dispatch to whatever work model Pi is already configured to use. Stratus support is therefore a compatibility requirement, not a hard dependency: when the user selects a Stratus model/provider and has credits, the translated English prompt should go to Stratus like any other selected work model.

A config option may later define preferred work profiles, for example `default`, `stratus`, or `local`, but the first design keeps model choice explicit through existing Pi mechanisms (`/model`, `--model`, presets, or provider config).

Alternatives considered:

- Always prefer Stratus when available: good for workflow consistency but surprising while credits and provider availability are variable.
- Always prefer the current Pi default: safest and matches existing behavior; selected as the baseline.

### Decision: Route thinking levels with deterministic policy plus model-assisted classification

The router should combine simple deterministic rules with the local classifier output. Deterministic rules protect obvious cases:

- `low`: greetings, short explanations, simple shell/file queries, translation-only requests, status checks.
- `medium`: normal coding edits, documentation updates, small debugging tasks, routine OpenSpec artifact creation.
- `high`: multi-file refactors, architecture/design decisions, ambiguous bug investigations, risky/destructive tasks, security-sensitive changes, performance work, or tasks that explicitly ask for deep reasoning.

`gemma4` can recommend a level, but the deterministic policy should clamp or override it when safety or cost rules are obvious. If the active model does not support the selected level, Pi's own clamping behavior is acceptable, but the router should record the requested and effective levels when possible.

Alternatives considered:

- Always `medium`: simple but leaves token savings on the table.
- Let the user manually cycle thinking every time: works today but is slow and easy to forget.
- Always `high`: maximizes quality for hard tasks but wastes tokens on simple prompts.

### Decision: Provide an on-demand router details inspection surface

When routing is enabled and the router finishes translation/classification, Pi should create a compact router details entry before sending the work prompt to the selected model. The entry is collapsed by default and can be expanded with a shortcut or command to show the original Spanish prompt, translated English work prompt, selected thinking level, and target work model. This is an inspection toggle, not an approval mode.

After completion, the same details surface should remain available and include the original Spanish prompt, translated English prompt, selected/requested/effective thinking levels, work model/provider, original English answer, Spanish answer, and fallback events. The default view should remain the Spanish final answer, with details available on demand.

`Ctrl+R` is a candidate shortcut for router details, but Pi currently uses `Ctrl+R` for session rename. `Ctrl+T` is already used for thinking/tree toggles, and `Ctrl+Shift+R` is used by the files extension. The implementation should keep the shortcut configurable, use `Ctrl+Alt+R` by default, or intentionally rebind conflicting shortcuts in the user's configuration if another binding is preferred.

Alternatives considered:

- Print all routing details inline every time: transparent but noisy.
- Hide details only in log files: too hard to inspect during interactive use.
- Require a preview/approval mode for all prompts: safe but slow and rejected in favor of a normal expand/collapse inspection control.

### Decision: Translate final user-facing answers, not all technical data

The final assistant answer should be shown in Spanish by default. Translation must preserve:

- code blocks,
- commands,
- file paths,
- identifiers,
- error messages where exact wording matters,
- generated artifact content if it is intentionally English.

The design should keep original English output available in metadata/logs when translation is applied, so the user or future debugging can inspect what the work model actually produced. If translation fails, Pi should show the English answer with a visible note rather than hiding the result.

Alternatives considered:

- Ask the work model to answer in Spanish directly: useful as a fallback, but the requirement assumes the work model responds in English and final translation is the router's responsibility.
- Translate every streamed delta live: better UX but more complex and expensive; batch translation of completed assistant messages is the first version.

### Decision: Roger delegates to the Pi-level router

Roger should not own a parallel Spanish-English translation policy. When Roger launches or communicates with Pi, it should enable the same router extension/profile and keep its existing Spanish voice/manual UX. Roger-specific routing remains responsible for voice capture, preview, session/domain choice, and TTS, while Pi handles prompt language, thinking level, work-model dispatch, and final answer translation.

Alternatives considered:

- Duplicate router logic in Python inside Roger: faster locally but creates drift between Roger and normal Pi usage.
- Disable routing for Roger: inconsistent user experience.

## Risks / Trade-offs

- **Translation changes task intent** → Keep the original Spanish prompt in router metadata, use conversation context only for reference resolution, and include tests with destructive, ambiguous, code-sensitive, and context-dependent prompts.
- **Slash commands and prompt templates break if translated too early** → Skip raw slash commands in the `input` hook and only route normal user prompts unless a later, safer post-expansion hook is proven reliable.
- **Final translation corrupts code or commands** → Use translator instructions that preserve fenced code, paths, identifiers, and quoted output; add fixtures for code-heavy responses.
- **Local `gemma4` latency makes Pi feel slower** → Bound router calls with timeouts, cache repeated translations when safe, and allow per-session or per-command bypass.
- **Router details surface slows down normal use** → Keep details collapsed by default, avoid an approval gate, and make expansion an explicit shortcut/command.
- **Stratus unavailable or out of credits** → Keep model selection independent from the router; Stratus failure remains a provider/model availability issue, not a router failure.
- **Thinking classification chooses too low for hard tasks** → Conservative rules should prefer `medium` over `low` when uncertain and `high` for risky, multi-step, or ambiguous tasks.
- **Extension hooks may not cover every Pi entrypoint perfectly** → Start as an extension, document unsupported edge cases, and escalate to a Pi core change only if required.
- **Session history mixes Spanish and transformed English** → Store clear router metadata and display the Spanish-facing conversation while preserving transformed prompts for audit/debug.

## Migration Plan

1. Add the router as an opt-in global Pi extension with configuration disabled by default or enabled only for the user's environment.
2. Configure the local llama.cpp `gemma4` endpoint, timeout, source language (`es`), work language (`en`), response language (`es`), and default routing state (`off` or `on`).
3. Add commands/status/diagnostic output showing whether routing is active, which model is used for routing, and the selected thinking level for each routed prompt.
4. Add the router-details inspection surface for interactive mode, plus log/metadata equivalents for print/RPC modes.
5. Verify normal interactive prompts, print mode prompts, and RPC prompts with the router enabled.
6. Verify that slash commands, prompt templates, file attachments, and OpenSpec workflows still pass through safely.
7. Add Stratus compatibility checks once credits are available: select a Stratus work model, confirm translated prompts dispatch correctly, and confirm provider failures are reported normally.
8. Update Roger to enable/use the Pi-level router rather than adding a Roger-only translation layer.
9. Rollback by disabling/removing the extension or setting router mode to `off`; Pi should then behave exactly as it did before the change.

## Open Questions

- Should the router be enabled globally by default for all Pi sessions, or only when a named profile/preset is active?
- Should router-details expansion use `Ctrl+R` despite its current conflict with Pi's session rename shortcut, or should it use a non-conflicting default such as `Ctrl+Shift+R` with configurable remapping?
- Should slash-command prompt templates ever be translated after expansion, or should commands remain fully responsible for their own language?
- What exact Stratus provider/model IDs should be documented once credits are available?
- Should final-answer translation be displayed as the only assistant message, or should Pi show both Spanish translation and collapsible original English output?
- Should the router use only `low`, `medium`, and `high`, or allow `minimal`/`xhigh` when a model supports them and the policy has high confidence?
