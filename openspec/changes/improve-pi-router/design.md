## Context

The current Roger work lives in `pi-extensions`, but this change targets Pi usage in general, not only Roger. Pi already exposes the extension hooks needed for a router-style workflow: `input` can transform user text before agent processing, `message_end` can replace finalized assistant messages, `pi.setThinkingLevel()` can apply `low`/`medium`/`high`, model selection can remain under Pi's normal `/model`, `--model`, and provider mechanisms, and RPC mode exposes `set_thinking_level` for embedded clients.

The user's preferred language is Spanish. The desired work model prompt language is English because coding agents and many model/provider combinations tend to perform better with precise English instructions. The local `gemma4` model served through llama.cpp is already part of the environment and should be used as the low-cost routing model for translation/classification. Stratus is part of the intended workflow, but is temporarily unavailable because credits are exhausted; the design must keep Stratus usable as a normal work-model target once credits return.

## Goals / Non-Goals

**Goals:**

- Let the user write normal Pi prompts in Spanish while the work model receives a concise English task prompt.
- Allow routing to be turned on or off globally, per session, and for a single prompt.
- Optionally show the translated English prompt before work-model dispatch so the user can approve, edit, bypass, or cancel.
- Translate final assistant answers back into Spanish for user comfort.
- Preserve original Spanish prompts, transformed English prompts, selected thinking levels, final English answers, and fallback reasons for traceability.
- Select `low`, `medium`, or `high` thinking per prompt to reduce unnecessary reasoning-token use while still giving complex tasks enough budget.
- Work across interactive Pi, print mode, and RPC-based integrations where Pi extension hooks or RPC commands are available.
- Keep Stratus compatible as a work-model provider/model; the router should not assume the work model is only Anthropic/OpenAI/local.
- Let Roger consume the same Pi-level routing behavior instead of maintaining a separate Roger-only language router.

**Non-Goals:**

- Do not replace Pi's provider/model registry or force every task onto Stratus.
- Do not translate source code, shell commands, file paths, error output, quoted literals, or generated artifact bodies when preserving them verbatim is more useful.
- Do not make `gemma4` the work model by default; it is the routing/translation/classification model unless the user explicitly selects it for work.
- Do not force preview before every prompt; preview is configurable because always reviewing translations would slow down routine work.
- Do not change Pi's core model APIs unless an extension/wrapper cannot satisfy the requirement.
- Do not implement full semantic project routing in this change; domain/session routing remains a separate concern.

## Decisions

### Decision: Implement the first version as a global Pi extension

Implement the router as a TypeScript Pi extension installed globally under `~/.pi/agent/extensions/pi-router/` or packaged for reuse. The extension can run in normal Pi sessions and does not require users to launch a separate wrapper for everyday use.

The extension will use:

- `input` to intercept normal user prompts, skip extension commands/slash commands, and transform Spanish text into an English work prompt.
- `ctx.ui.custom()` or a compact extension dialog to preview the translated prompt when review mode is enabled.
- `pi.setThinkingLevel()` to apply the selected thinking level before the agent turn starts.
- `message_end` to translate user-facing assistant text back to Spanish while preserving code blocks, paths, commands, and structured technical content.
- `pi.appendEntry()` or custom displayed metadata to record router decisions without polluting the model context.
- A custom message renderer, widget, or command to expose router details in an expandable/collapsible view similar in spirit to Pi's Ctrl+O tool-output inspection flow.
- `model_select` and `thinking_level_select` to show status/diagnostics when useful.

Alternatives considered:

- A shell wrapper around `pi`: simpler to prototype but incomplete for interactive follow-ups, model changes, and RPC sessions.
- Direct Pi core changes: more powerful but unnecessary until extension hooks prove insufficient.
- A Roger-only implementation: rejected because the requirement is Pi-wide.

### Decision: Support explicit router modes

The router should support at least three modes:

- `off`: no translation and no automatic thinking selection; Pi behaves like normal.
- `on`: translate/classify automatically and dispatch without interrupting routine work.
- `preview`: translate/classify, then show the English prompt and selected thinking level before dispatch.

Configuration should allow a default global mode and session-level override. Interactive users should also have commands or shortcuts to toggle routing and preview mode. Single prompts should support a bypass prefix or command so the user can intentionally send raw input.

Alternatives considered:

- Always-on routing: convenient but risky when the user wants exact prompt wording.
- Always-preview routing: safest but too slow for frequent small prompts.
- Only per-prompt routing: too much friction for the user's primary Spanish workflow.

### Decision: Use local `gemma4` as the router model through llama.cpp

The router should call the local llama.cpp OpenAI-compatible endpoint for translation and classification. `gemma4` will produce a structured router result containing:

- detected input language,
- English work prompt,
- selected thinking level,
- short reason for the level,
- whether final response translation should be applied,
- warnings or fallback hints.

The router call must be bounded by a timeout and a maximum input size. If local `gemma4` is unavailable, the router should either pass the original prompt through unchanged with a visible warning or ask the user to disable/repair the router, depending on configuration.

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

### Decision: Provide a prompt preview and router details inspection surface

When preview mode is enabled, the user should see the original Spanish prompt, translated English work prompt, selected thinking level, and target work model before dispatch. The preview should offer approve, edit translated prompt, send original/bypass, cancel, and optionally remember the choice for the session.

After completion, the default view should remain the Spanish final answer. The router should also expose an inspectable detail view with the original Spanish prompt, translated English prompt, selected/requested/effective thinking levels, work model/provider, original English answer, Spanish answer, and fallback events. This should feel similar to Pi's existing expandable/collapsible output behavior: compact by default, detailed on demand.

Alternatives considered:

- Print all routing details inline every time: transparent but noisy.
- Hide details only in log files: too hard to inspect during interactive use.
- Require preview for all prompts: safe but slow; selected as an optional mode instead.

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

- **Translation changes task intent** → Keep the original Spanish prompt in router metadata and include it in the transformed work prompt as reference; add tests with destructive, ambiguous, and code-sensitive prompts.
- **Slash commands and prompt templates break if translated too early** → Skip raw slash commands in the `input` hook and only route normal user prompts unless a later, safer post-expansion hook is proven reliable.
- **Final translation corrupts code or commands** → Use translator instructions that preserve fenced code, paths, identifiers, and quoted output; add fixtures for code-heavy responses.
- **Local `gemma4` latency makes Pi feel slower** → Bound router calls with timeouts, cache repeated translations when safe, and allow per-session or per-command bypass.
- **Preview mode slows down normal use** → Make preview optional and let the user toggle between `off`, `on`, and `preview` without editing config files.
- **Stratus unavailable or out of credits** → Keep model selection independent from the router; Stratus failure remains a provider/model availability issue, not a router failure.
- **Thinking classification chooses too low for hard tasks** → Conservative rules should prefer `medium` over `low` when uncertain and `high` for risky, multi-step, or ambiguous tasks.
- **Extension hooks may not cover every Pi entrypoint perfectly** → Start as an extension, document unsupported edge cases, and escalate to a Pi core change only if required.
- **Session history mixes Spanish and transformed English** → Store clear router metadata and display the Spanish-facing conversation while preserving transformed prompts for audit/debug.

## Migration Plan

1. Add the router as an opt-in global Pi extension with configuration disabled by default or enabled only for the user's environment.
2. Configure the local llama.cpp `gemma4` endpoint, timeout, source language (`es`), work language (`en`), response language (`es`), and default routing mode (`off`, `on`, or `preview`).
3. Add commands/status/diagnostic output showing whether routing is active, which model is used for routing, and the selected thinking level for each routed prompt.
4. Add preview and router-details inspection surfaces for interactive mode, plus log/metadata equivalents for print/RPC modes.
5. Verify normal interactive prompts, print mode prompts, and RPC prompts with the router enabled.
6. Verify that slash commands, prompt templates, file attachments, and OpenSpec workflows still pass through safely.
7. Add Stratus compatibility checks once credits are available: select a Stratus work model, confirm translated prompts dispatch correctly, and confirm provider failures are reported normally.
8. Update Roger to enable/use the Pi-level router rather than adding a Roger-only translation layer.
9. Rollback by disabling/removing the extension or setting router mode to `off`; Pi should then behave exactly as it did before the change.

## Open Questions

- Should the router be enabled globally by default for all Pi sessions, or only when a named profile/preset is active?
- What shortcut or command names should toggle `off`/`on`/`preview`, given Ctrl+O is already used by Pi for output expansion?
- Should slash-command prompt templates ever be translated after expansion, or should commands remain fully responsible for their own language?
- What exact Stratus provider/model IDs should be documented once credits are available?
- Should final-answer translation be displayed as the only assistant message, or should Pi show both Spanish translation and collapsible original English output?
- Should the router use only `low`, `medium`, and `high`, or allow `minimal`/`xhigh` when a model supports them and the policy has high confidence?
