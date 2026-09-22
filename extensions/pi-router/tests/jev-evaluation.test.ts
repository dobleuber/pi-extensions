import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { JEV_EVALUATION_MANIFEST, JEV_EVALUATION_MANIFEST_VERSION, scoreJevEvaluation } from "../src/jev-evaluation.ts";
import { JEV_PROFILE_EVALUATION_CASES } from "./fixtures/jev-profile-cases.ts";

describe("Jev evaluation manifest", () => {
	it("separates calibration and held-out evidence and starts unapproved", () => {
		assert.equal(JEV_EVALUATION_MANIFEST_VERSION, "jev-router-evaluation-v1");
		assert.notEqual(JEV_EVALUATION_MANIFEST.calibrationDataset, JEV_EVALUATION_MANIFEST.heldOutDataset);
		assert.equal(JEV_PROFILE_EVALUATION_CASES.filter((item) => item.split === "calibration").length, 3);
		assert.equal(JEV_PROFILE_EVALUATION_CASES.filter((item) => item.split === "held-out").length, 2);
		assert.ok(JEV_EVALUATION_MANIFEST.metrics.includes("inputTranslationFalseNegatives"));
		assert.ok(JEV_EVALUATION_MANIFEST.metrics.includes("responseTranslationFalseNegatives"));
		assert.equal(JEV_EVALUATION_MANIFEST.releaseGate.approved, false);
		assert.equal(JEV_EVALUATION_MANIFEST.releaseGate.thresholds.p95CompletePathMsMax, null);
	});

	it("penalizes Astra escalation for demanding tasks labeled for Sol", () => {
		const cases = JEV_PROFILE_EVALUATION_CASES.filter((item) => item.category === "debugging" || item.category === "agentic");
		assert.ok(cases.length > 0);
		const predict = (profile: "sol" | "astra") => Object.fromEntries(cases.map((item) => [item.id, {
			profile,
			inputTranslation: item.expectedInputTranslation,
			responseTranslation: item.expectedResponseTranslation,
		}]));
		assert.equal(scoreJevEvaluation(cases, predict("sol")).profileAgreement, 1);
		assert.equal(scoreJevEvaluation(cases, predict("astra")).profileAgreement, 0);
	});

	it("scores profile and translation outcomes independently", () => {
		const summary = scoreJevEvaluation(JEV_PROFILE_EVALUATION_CASES, {
			"routine-readme-edit": { profile: "luna", inputTranslation: "not_required", responseTranslation: "not_required" },
			"agentic-spanish-payment-migration": { profile: "sol", inputTranslation: "required", responseTranslation: "required" },
			"debugging-flaky-lifecycle": { profile: "sol", inputTranslation: "not_required", responseTranslation: "not_required" },
			"architecture-provider-boundary": { profile: "astra", inputTranslation: "not_required", responseTranslation: "not_required" },
			"heldout-mixed-code-debugging": { profile: "sol", inputTranslation: "not_required", responseTranslation: "required" },
		});
		assert.equal(summary.count, 5);
		assert.equal(summary.profileAgreement, 1);
		assert.equal(summary.inputTranslationFalseNegatives, 1);
		assert.equal(summary.responseTranslationFalseNegatives, 0);
	});
});
