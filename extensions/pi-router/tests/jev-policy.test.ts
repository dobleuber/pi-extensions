import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
	JEV_PROFILE_CRITERIA_VERSION,
	JEV_PROFILE_CATALOG_VERSION,
	JEV_PROFILE_CANDIDATES,
	eligibleJevProfileCandidates,
	profileForJevKey,
	selectJevProfile,
} from "../src/jev-policy.ts";
import { ASTRA_MEDIUM_PROFILE, SOL_PROFILE } from "../src/model-profile.ts";

describe("Jev profile policy", () => {
	it("uses a versioned rubric with only currently approved profiles", () => {
		assert.equal(JEV_PROFILE_CRITERIA_VERSION, "jev-router-profile-rubric-v3");
		assert.equal(JEV_PROFILE_CATALOG_VERSION, "jev-router-profile-catalog-v4");
		assert.deepEqual(JEV_PROFILE_CANDIDATES.map((candidate) => candidate.key), ["luna", "sol", "astra"]);
		assert.doesNotMatch(JEV_PROFILE_CANDIDATES[0].description, /latency|fast|responsive/i);
		for (const candidate of JEV_PROFILE_CANDIDATES) {
			assert.ok(candidate.description.length >= 40);
		}
	});

	it("maps Jev keys to automatic profile states", () => {
		assert.equal(profileForJevKey("luna")?.id, "luna-max");
		assert.deepEqual(profileForJevKey("sol"), { ...SOL_PROFILE, source: "automatic" });
		assert.deepEqual(profileForJevKey("astra"), { ...ASTRA_MEDIUM_PROFILE, source: "automatic" });
		assert.equal(profileForJevKey("luna")?.source, "automatic");
		assert.equal(profileForJevKey("terra"), undefined);
		assert.equal(profileForJevKey("toString"), undefined);
	});

	it("accepts only approved keys and returns the mapped profile", () => {
		assert.deepEqual(selectJevProfile("sol"), profileForJevKey("sol"));
		assert.equal(selectJevProfile("terra"), undefined);
		assert.equal(selectJevProfile(ASTRA_MEDIUM_PROFILE.model), undefined);
		assert.equal(selectJevProfile(""), undefined);
		assert.deepEqual(eligibleJevProfileCandidates(["luna", "terra"]).map((candidate) => candidate.key), ["luna"]);
		assert.deepEqual(eligibleJevProfileCandidates(undefined, 1).map((candidate) => candidate.key), ["luna"]);
		assert.deepEqual(eligibleJevProfileCandidates([]), []);
		assert.equal(selectJevProfile("astra", undefined, 2), undefined);
	});
});
