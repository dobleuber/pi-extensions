import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
	JEV_PROFILE_CRITERIA_VERSION,
	JEV_PROFILE_CATALOG_VERSION,
	JEV_PROFILE_CANDIDATES,
	eligibleJevProfileCandidates,
	profileForJevKey,
	selectJevProfile,
	type JevProfileKey,
} from "../src/jev-policy.ts";
import { JEV_PROFILE_EVALUATION_CASES } from "./fixtures/jev-profile-cases.ts";

describe("Jev profile policy", () => {
	it("uses a versioned rubric with only currently approved profiles", () => {
		assert.equal(JEV_PROFILE_CRITERIA_VERSION, "jev-router-profile-rubric-v2");
		assert.equal(JEV_PROFILE_CATALOG_VERSION, "jev-router-profile-catalog-v2");
		assert.deepEqual(JEV_PROFILE_CANDIDATES.map((candidate) => candidate.key), ["luna", "terra", "vega", "astra"]);
		assert.doesNotMatch(JEV_PROFILE_CANDIDATES[0].description, /latency|fast|responsive/i);
		for (const candidate of JEV_PROFILE_CANDIDATES) {
			assert.ok(candidate.description.length >= 40);
		}
	});

	it("maps Jev keys to automatic profile states", () => {
		assert.equal(profileForJevKey("luna")?.id, "luna-max");
		assert.equal(profileForJevKey("vega")?.id, "astra-low");
		assert.equal(profileForJevKey("astra")?.id, "astra-medium");
		assert.equal(profileForJevKey("luna")?.source, "automatic");
		assert.equal(profileForJevKey("terra")?.id, "terra-medium");
		assert.equal(profileForJevKey("terra")?.model, "gpt-5.6-terra");
		assert.equal(profileForJevKey("terra")?.thinkingLevel, "medium");
		assert.equal(profileForJevKey("toString"), undefined);
	});

	it("accepts only approved keys and returns the mapped profile", () => {
		assert.deepEqual(selectJevProfile("vega"), profileForJevKey("vega"));
		assert.equal(selectJevProfile("gpt-6-astra"), undefined);
		assert.equal(selectJevProfile(""), undefined);
		assert.deepEqual(eligibleJevProfileCandidates(["luna", "terra"]).map((candidate) => candidate.key), ["luna", "terra"]);
		assert.deepEqual(eligibleJevProfileCandidates(undefined, 1).map((candidate) => candidate.key), ["luna"]);
		assert.deepEqual(eligibleJevProfileCandidates([]), []);
		assert.equal(selectJevProfile("astra", undefined, 2), undefined);
	});

	it("contains independently labeled cases across language and task categories", () => {
		const categories = new Set(JEV_PROFILE_EVALUATION_CASES.map((item) => item.category));
		assert.ok(categories.has("routine"));
		assert.ok(categories.has("debugging"));
		assert.ok(categories.has("architecture"));
		assert.ok(categories.has("multilingual"));
		for (const item of JEV_PROFILE_EVALUATION_CASES) {
			assert.ok(item.prompt.length > 10);
			assert.ok(item.acceptableProfiles.length > 0);
			assert.ok(item.language === "en" || item.language === "es" || item.language === "mixed");
		}
	});

	it("keeps the evaluation labels independent from the Jev output", () => {
		const keys = new Set<JevProfileKey>(JEV_PROFILE_CANDIDATES.map((candidate) => candidate.key));
		for (const item of JEV_PROFILE_EVALUATION_CASES) {
			for (const profile of item.acceptableProfiles) assert.ok(keys.has(profile));
		}
	});
});
