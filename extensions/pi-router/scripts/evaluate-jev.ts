import { JEV_EVALUATION_MANIFEST_VERSION, scoreJevEvaluation } from "../src/jev-evaluation.ts";
import { JEV_PROFILE_EVALUATION_CASES } from "../tests/fixtures/jev-profile-cases.ts";

const predictions = Object.fromEntries(JEV_PROFILE_EVALUATION_CASES.map((evaluationCase) => [evaluationCase.id, {
	profile: evaluationCase.acceptableProfiles[0],
	inputTranslation: evaluationCase.expectedInputTranslation,
	responseTranslation: evaluationCase.expectedResponseTranslation,
}]));

console.log(JSON.stringify({
	manifest: JEV_EVALUATION_MANIFEST_VERSION,
	mode: "offline-fixtures-only",
	calibrationCases: JEV_PROFILE_EVALUATION_CASES.filter((item) => item.split === "calibration").length,
	heldOutCases: JEV_PROFILE_EVALUATION_CASES.filter((item) => item.split === "held-out").length,
	summary: scoreJevEvaluation(JEV_PROFILE_EVALUATION_CASES, predictions),
	releaseGate: { approved: false, thresholdsApproved: false },
}, null, 2));
