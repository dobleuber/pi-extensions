# Live Jev smoke verification

Model: `jev-1.13.0`. Transport: installed TypeSafe SDK through the real router adapter. Default 1000 ms deadline; sequential calls; synthetic text only. Automatic routing remains disabled. This is a small smoke sample, not a held-out release evaluation.

| Case | Expected translation | Actual | Duration ms | Input/output tokens |
|---|---|---|---:|---:|
| English README typo instruction | not_required | not_required | 749 | 680/132 |
| Spanish README instruction | required | required | 188 | 682/131 |
| Mixed English/Spanish instruction | required | required | 202 | 682/131 |
| Spanish final answer | not_required | not_required | 203 | 398/47 |
| English final answer | required | required | 189 | 397/46 |
| Mixed final answer | required | uncertain | 226 | 401/47 |

All six requests completed within the default deadline. Five exact label matches; one conservative uncertainty that retains generative translation (not a translation bypass). All three input cases selected Luna. Total usage: 3240 input tokens, 534 output tokens. Decision-only nearest-rank p50: 202 ms; p95: 749 ms. These are not complete-path latency measurements. Dollar cost was not calculated without verified pricing.

Remaining release evidence: representative profile selection and downstream outcomes, adversarial evaluation, independent threshold calibration, baseline comparison, retained translation costs, complete-path latency, and explicit approval. No release thresholds or activation flags were changed.

Lifecycle review reproduced a second queued profile being applied at message_start after turn_start had already applied the receiving profile. The fix marks the receiving-turn profile boundary as handled and prevents a failed boundary from consuming another queued marker.
