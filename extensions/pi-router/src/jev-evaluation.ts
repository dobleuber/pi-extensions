export const JEV_EVALUATION_MANIFEST_VERSION = "jev-router-evaluation-v1" as const;

export type JevEvaluationTranslation = "required" | "not_required" | "uncertain";
export type JevEvaluationProfile = import("./jev-policy.ts").JevProfileKey;
export type JevEvaluationSplit = "calibration" | "held-out";

export interface JevEvaluationCase {
	readonly id: string;
	readonly split: JevEvaluationSplit;
	readonly acceptableProfiles: readonly JevEvaluationProfile[];
	readonly expectedInputTranslation: "required" | "not_required";
	readonly expectedResponseTranslation: "required" | "not_required";
}

export interface JevEvaluationPrediction {
	readonly profile?: JevEvaluationProfile;
	readonly inputTranslation: JevEvaluationTranslation;
	readonly responseTranslation: JevEvaluationTranslation;
}

export interface JevEvaluationRecord {
	readonly id: string;
	readonly split: JevEvaluationSplit;
	readonly profileAgreement: boolean;
	readonly inputTranslationFalseNegative: boolean;
	readonly responseTranslationFalseNegative: boolean;
	readonly unnecessaryInputTranslation: boolean;
	readonly unnecessaryResponseTranslation: boolean;
}

export interface JevEvaluationSummary {
	readonly count: number;
	readonly profileAgreement: number;
	readonly inputTranslationFalseNegatives: number;
	readonly responseTranslationFalseNegatives: number;
	readonly unnecessaryTranslations: number;
}

export const JEV_EVALUATION_MANIFEST = Object.freeze({
	calibrationDataset: "tests/fixtures/jev-profile-cases.ts:calibration",
	heldOutDataset: "tests/fixtures/jev-profile-cases.ts:held-out",
	metrics: Object.freeze([
		"profileAgreement",
		"unnecessaryExpensiveSelections",
		"inputTranslationFalseNegatives",
		"responseTranslationFalseNegatives",
		"unnecessaryTranslations",
		"avoidedGenerativeCalls",
		"fallbackFrequency",
		"latencyP50P95",
		"decisionPlusTranslationCost",
	] as const),
	releaseGate: Object.freeze({
		approved: false,
		thresholdsApproved: false,
		thresholds: Object.freeze({
			profileAgreementMin: null as number | null,
			inputTranslationFalseNegativesMax: null as number | null,
			responseTranslationFalseNegativesMax: null as number | null,
			unnecessaryTranslationsMax: null as number | null,
			p95CompletePathMsMax: null as number | null,
		}),
	}),
});

/**
 * Offline-only scorer. It consumes recorded typed predictions and never calls
 * Jev or a work-model provider, which keeps evaluation budgets separate from
 * interactive routing.
 */
export function scoreJevEvaluation(
	cases: readonly JevEvaluationCase[],
	predictions: Readonly<Record<string, JevEvaluationPrediction>>,
): JevEvaluationSummary {
	const records = cases.map((evaluationCase) => {
		const prediction = predictions[evaluationCase.id];
		const profileAgreement = Boolean(prediction?.profile && evaluationCase.acceptableProfiles.includes(prediction.profile));
		const inputTranslationFalseNegative = evaluationCase.expectedInputTranslation === "required"
			&& prediction?.inputTranslation === "not_required";
		const responseTranslationFalseNegative = evaluationCase.expectedResponseTranslation === "required"
			&& prediction?.responseTranslation === "not_required";
		const unnecessaryInputTranslation = evaluationCase.expectedInputTranslation === "not_required"
			&& prediction?.inputTranslation === "required";
		const unnecessaryResponseTranslation = evaluationCase.expectedResponseTranslation === "not_required"
			&& prediction?.responseTranslation === "required";
		return {
			id: evaluationCase.id,
			split: evaluationCase.split,
			profileAgreement,
			inputTranslationFalseNegative,
			responseTranslationFalseNegative,
			unnecessaryInputTranslation,
			unnecessaryResponseTranslation,
		};
	});
	const count = records.length;
	return {
		count,
		profileAgreement: count === 0 ? 0 : records.filter((record) => record.profileAgreement).length / count,
		inputTranslationFalseNegatives: records.filter((record) => record.inputTranslationFalseNegative).length,
		responseTranslationFalseNegatives: records.filter((record) => record.responseTranslationFalseNegative).length,
		unnecessaryTranslations: records.filter((record) => record.unnecessaryInputTranslation || record.unnecessaryResponseTranslation).length,
	};
}
