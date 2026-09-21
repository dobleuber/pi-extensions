## Context and scope

The personal Pi Router uses Jev directly whenever routing is on. Git is the rollback mechanism; there is no legacy persistent-profile branch, activation flag, evaluation-only mode, or runtime approval gate. `/router off` and per-prompt bypass remain deterministic controls.

## Decisions

### Typed adapter and independent translation

Use the pinned TypeSafe SDK through an injectable transport. One input request classifies profile, input translation need, and source language. A separate response request determines whether final-answer translation is needed. Jev does not generate translations. The existing generative translators, protected-text handling, final-message filtering, and Roger speech behavior remain.

### Catalog and task rubric v2

All profiles use the `openai-codex` provider:

| Key | Model | Thinking | Cost tier | Task suitability |
| --- | --- | --- | --- | --- |
| luna | gpt-5.6-luna | max | 1 | Clearly scoped implementation, bugs, tests, documentation, reviews, bounded refactors, and moderately complex work with clear acceptance criteria, including multiple files. |
| terra | gpt-5.6-terra | medium | 2 | Bounded integration decisions, multiple-hypothesis debugging, dependency/API migrations, and subsystem design trade-offs. |
| vega | gpt-6-astra | low | 2 | Focused difficult bugs, subtle localized correctness changes, and constrained investigations with precise success conditions. |
| astra | gpt-6-astra | medium | 3 | Novel architecture, broad migrations, cross-subsystem debugging, and ambiguous end-to-end workflows requiring sustained planning and verification. |

Criteria describe tasks rather than comparative model capability. Luna is not restricted to trivial edits and makes no latency claim: this application uses max reasoning. Terra uses the documented default medium effort. Tier labels are deterministic spending policy, not measured task costs or latency rankings. Rubric and catalog revisions are v2.

Official references: https://developers.openai.com/api/docs/models/gpt-5.6-luna, https://developers.openai.com/api/docs/models/gpt-5.6-terra, https://developers.openai.com/api/docs/models/gpt-6-astra, https://developers.openai.com/api/docs/guides/reasoning. Task boundaries are application policy, not vendor benchmark claims.

### Precedence and application

Leading `Use Default:` forces Luna; `Use Terra:`, `Use Vega:`, and `Use Astra:` force their mapped profiles, with Spanish equivalents. Overrides apply only to the current prompt. Unqualified prompts use accepted Jev selection or Luna fallback. No profile choice is persisted as a preference. Registry/model/thinking application must succeed before dispatch; explicit application failure stops dispatch rather than substituting a model.

Queued profile application occurs at the receiving-turn boundary, once per turn. Active tool continuations keep their originating model. Failed deferred application aborts the receiving turn. Session starts discard pending markers and reset the default profile.

### Bounds and fallback

Use `jev-1.13.0`, a 1000 ms deadline, a 12000-character serialized state bound, no interactive retries, and cancellation propagation. Reject malformed choices and distributions; validate against exactly the offered cost-capped candidates. Default acceptance is 0.70 for profiles and 0.85 for translation bypass. Low-confidence selections retain Luna/generative translation. These thresholds are policy, not proof of task success.

Credentials come from `TYPESAFE_API_KEY` and are excluded from state and redacted from diagnostics. Jev fallback reasons remain in details; successful conservative fallback is not labeled a router outage. Actual failed dispatch or translation remains visible.

## Verification and deployment

Offline tests cover four-choice normalization, Terra directives/mapping, cost filtering, fallback, cancellation, credential redaction, translation gates, and lifecycle isolation. Optional live smoke checks require explicit authorization and synthetic or approved data. Expanded downstream/comparative evaluation and release thresholds were removed from scope by the user. No production-quality claim follows from offline fixture scores.

Local deployment is the existing symlink from `~/.pi/agent/extensions/pi-router` to this package. Restart/reload Pi to load changed code. No remote publication is needed.
