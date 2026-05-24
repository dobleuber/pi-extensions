## Why

Pi is primarily used by a Spanish-speaking user, while many work models and coding-agent prompts perform better when the actual task is written in clear English. The router should let the user continue thinking and writing naturally in Spanish, optimize the prompt and thinking budget for the selected work model, and return final answers in Spanish.

## What Changes

- Add a Pi-level prompt router that runs before normal work-model dispatch, not only inside Roger.
- Use the local `gemma4`/llama.cpp profile to translate Spanish user prompts into concise, precise English work prompts.
- Preserve the original Spanish prompt for session traceability, logs, retries, and user-facing context.
- Send the translated English prompt to the configured work model, including Stratus when credits are available and selected in the workflow.
- Add prompt-aware thinking-level selection with `low`, `medium`, and `high` profiles based on task complexity, ambiguity, risk, and expected tool use.
- Apply the selected thinking level through Pi's supported interfaces when possible, such as `--thinking`, model `:<thinking>` shorthand, or RPC `set_thinking_level`.
- Translate the final assistant answer back into Spanish before showing it to the user, while keeping detailed technical artifacts/logs available in their original form when useful.
- Add controls to turn the router on or off globally, per session, or for a single prompt.
- Add an optional review mode that shows the translated English prompt before it is sent to the work model, allowing the user to approve, edit, bypass, or cancel dispatch.
- Add an inspectable router details view for final answers, similar in spirit to Pi's expandable/collapsible output controls, so the user can see the Spanish final answer, original English answer, translated prompt, and routing metadata when needed.
- Add safe fallback behavior when local translation, thinking classification, final-answer translation, or preview UI is unavailable, so Pi can either proceed transparently or explain the degraded mode instead of silently dropping the task.

## Capabilities

### New Capabilities

- `pi-prompt-language-router`: Pi-wide Spanish-to-English prompt normalization before dispatch and English-to-Spanish final-answer translation after completion, with original prompt/result traceability.
- `pi-thinking-level-router`: Prompt-aware selection and application of `low`, `medium`, or `high` thinking profiles for better token use across simple, medium, and complex tasks.
- `pi-router-model-policy`: Configurable router/work-model policy that keeps local `gemma4` available for routing, supports Stratus as a normal work-model target once credits are available, and exposes router enable/disable plus preview/inspection controls.

### Modified Capabilities

- `roger-context-routing`: Roger should consume the Pi-level router when dispatching through pi-agent rather than owning Spanish-English prompt translation itself.
- `roger-agent-execution`: Roger-dispatched tasks should preserve Spanish UX while allowing the underlying Pi work prompt, thinking level, and final response translation to be handled by the general Pi router.

## Impact

- Affected Pi integration points: CLI prompt entry, print mode, RPC prompt dispatch, model/thinking selection, session logging, and any extension or wrapper used to install the router into the general Pi workflow.
- Affected Roger code: Roger should delegate prompt language routing and thinking selection to the Pi-level mechanism where possible, while preserving current voice/manual UX.
- Affected tests: router policy tests, translation fallback tests, thinking-level classification/application tests, RPC/CLI dispatch tests, Stratus-selection compatibility tests, and final-response Spanish translation tests.
- Affected docs/config: Pi setup documentation for enabling the router, configuring local `gemma4`, selecting Stratus as a work model, and explaining when original English technical output is preserved.
- External systems: local llama.cpp/`gemma4` availability for routing/translation, Stratus availability/credits for work-model dispatch, and Pi model support for configurable thinking levels.
