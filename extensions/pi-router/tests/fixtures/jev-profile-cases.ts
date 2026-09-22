export type JevProfileEvaluationCategory = "routine" | "debugging" | "architecture" | "multilingual" | "agentic";
export type JevProfileEvaluationLanguage = "en" | "es" | "mixed";
export type JevProfileEvaluationProfile = "luna" | "sol" | "astra";
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
		id: "agentic-spanish-payment-migration",
		split: "calibration",
		category: "agentic",
		language: "es",
		prompt: "Migra la integración de pagos a la nueva API: inspecciona el SDK y los contratos, implementa idempotencia y reintentos, ejecuta pruebas de fallos y corrige los problemas hasta verificar el flujo completo.",
		acceptableProfiles: ["sol"],
		expectedInputTranslation: "required",
		expectedResponseTranslation: "required",
	},
	{
		id: "debugging-flaky-lifecycle",
		split: "calibration",
		category: "debugging",
		language: "en",
		prompt: "Debug an intermittent queued-turn race: reproduce it under load, trace lifecycle events across tools, compare competing causes, implement a fix, and repeatedly run concurrency regressions until verified.",
		acceptableProfiles: ["sol"],
		expectedInputTranslation: "not_required",
		expectedResponseTranslation: "not_required",
	},
	{
		id: "architecture-provider-boundary",
		split: "held-out",
		category: "architecture",
		language: "en",
		prompt: "Design a novel provider-neutral execution architecture under conflicting tenant-isolation, cross-region recovery, and irreversible-tool requirements. Existing designs cannot satisfy all constraints; resolve ambiguous failure semantics, compare fundamentally different architectures, and justify the security and consistency trade-offs before implementation.",
		acceptableProfiles: ["astra"],
		expectedInputTranslation: "not_required",
		expectedResponseTranslation: "not_required",
	},
	{
		id: "heldout-mixed-code-debugging",
		split: "held-out",
		category: "debugging",
		language: "mixed",
		prompt: "Investiga el fallo intermitente de `ModelProfileState`: inspect traces, reproduce the failure, implement the fix, and run the full regression suite. Conserva las interfaces públicas y explica la causa raíz.",
		acceptableProfiles: ["sol"],
		expectedInputTranslation: "required",
		expectedResponseTranslation: "required",
	},
]);
