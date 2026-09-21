export type JevProfileEvaluationCategory = "routine" | "debugging" | "architecture" | "multilingual";
export type JevProfileEvaluationLanguage = "en" | "es" | "mixed";
export type JevProfileEvaluationProfile = "luna" | "terra" | "vega" | "astra";
export type JevTranslationLabel = "required" | "not_required";
export type JevEvaluationSplit = "calibration" | "held-out";

export interface JevProfileEvaluationCase {
	id: string;
	split: JevEvaluationSplit;
	category: JevProfileEvaluationCategory;
	language: JevProfileEvaluationLanguage;
	prompt: string;
	acceptableProfiles: readonly JevProfileEvaluationProfile[];
	expectedInputTranslation: JevTranslationLabel;
	expectedResponseTranslation: JevTranslationLabel;
}

/** Versioned human labels; Jev predictions are recorded separately. */
export const JEV_PROFILE_EVALUATION_CASES: readonly JevProfileEvaluationCase[] = Object.freeze([
	{
		id: "routine-readme-edit",
		split: "calibration",
		category: "routine",
		language: "en",
		prompt: "Implement pagination across the existing API handler, client, and UI following the documented cursor contract, and add regression tests for empty and final pages.",
		acceptableProfiles: ["luna"],
		expectedInputTranslation: "not_required",
		expectedResponseTranslation: "not_required",
	},
	{
		id: "routine-spanish-test-command",
		split: "calibration",
		category: "multilingual",
		language: "es",
		prompt: "Migra la integración de pagos a la nueva API y compara las estrategias de reintento dentro de este módulo.",
		acceptableProfiles: ["terra"],
		expectedInputTranslation: "required",
		expectedResponseTranslation: "required",
	},
	{
		id: "debugging-flaky-lifecycle",
		split: "calibration",
		category: "debugging",
		language: "en",
		prompt: "Trace the intermittent queued-turn race, identify the lifecycle boundary, and add a regression test.",
		acceptableProfiles: ["vega", "astra"],
		expectedInputTranslation: "not_required",
		expectedResponseTranslation: "not_required",
	},
	{
		id: "architecture-provider-boundary",
		split: "held-out",
		category: "architecture",
		language: "en",
		prompt: "Design a provider-neutral model selection boundary with cancellation, telemetry, and deterministic fallback semantics.",
		acceptableProfiles: ["astra"],
		expectedInputTranslation: "not_required",
		expectedResponseTranslation: "not_required",
	},
	{
		id: "mixed-code-explanation",
		split: "held-out",
		category: "multilingual",
		language: "mixed",
		prompt: "Explica por qué falla este test y conserva exactamente `ModelProfileState` y el código adjunto.",
		acceptableProfiles: ["vega", "astra"],
		expectedInputTranslation: "required",
		expectedResponseTranslation: "required",
	},
]);
