import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { ASTRA_MEDIUM_PROFILE, SOL_PROFILE, applyModelProfileToRuntime, type ModelProfileRuntime } from "../src/model-profile.ts";

describe("router model profile application", () => {
	it("resolves the profile through the registry and applies model and thinking atomically", async () => {
		const calls: string[] = [];
		const runtime: ModelProfileRuntime = {
			resolveModel: (provider, model) => {
				calls.push(`resolve:${provider}/${model}`);
				return { provider, id: model };
			},
			setModel: async (model) => {
				calls.push(`model:${(model as any).id}`);
				return true;
			},
			setThinkingLevel: (level) => { calls.push(`thinking:${level}`); },
			getEffectiveModel: () => ({ provider: ASTRA_MEDIUM_PROFILE.provider, model: ASTRA_MEDIUM_PROFILE.model }),
			getEffectiveThinkingLevel: () => "medium",
		};

		const result = await applyModelProfileToRuntime({ ...ASTRA_MEDIUM_PROFILE, source: "prompt" }, runtime);

		assert.deepEqual(result, {
			applied: true,
			effectiveModel: { provider: ASTRA_MEDIUM_PROFILE.provider, model: ASTRA_MEDIUM_PROFILE.model },
			effectiveThinkingLevel: "medium",
		});
		assert.deepEqual(calls, [
			`resolve:${ASTRA_MEDIUM_PROFILE.provider}/${ASTRA_MEDIUM_PROFILE.model}`,
			`model:${ASTRA_MEDIUM_PROFILE.model}`,
			"thinking:medium",
		]);
	});

	it("applies the Sol profile with xhigh thinking", async () => {
		let thinkingLevel = "";
		const result = await applyModelProfileToRuntime({ ...SOL_PROFILE, source: "prompt" }, {
			resolveModel: (provider, model) => ({ provider, id: model }),
			setModel: async () => true,
			setThinkingLevel: (level) => { thinkingLevel = level; },
			getEffectiveModel: () => ({ provider: SOL_PROFILE.provider, model: SOL_PROFILE.model }),
			getEffectiveThinkingLevel: () => thinkingLevel,
		});

		assert.equal(result.applied, true);
		assert.equal(thinkingLevel, "xhigh");
		assert.equal(result.effectiveThinkingLevel, "xhigh");
	});

	it("rejects a registry result whose identity does not match the requested profile", async () => {
		let modelApplied = false;
		const result = await applyModelProfileToRuntime({ ...ASTRA_MEDIUM_PROFILE, source: "prompt" }, {
			resolveModel: () => ({ provider: "openai-codex", id: "another-model" }),
			setModel: async () => { modelApplied = true; return true; },
			setThinkingLevel: () => {},
		});

		assert.equal(result.applied, false);
		assert.match(result.error ?? "", /another-model/);
		assert.equal(modelApplied, false);
	});

	it("does not apply thinking when the requested model is unavailable", async () => {
		let thinkingApplied = false;
		const result = await applyModelProfileToRuntime({ ...ASTRA_MEDIUM_PROFILE, source: "prompt" }, {
			resolveModel: () => undefined,
			setModel: async () => true,
			setThinkingLevel: () => { thinkingApplied = true; },
		});

		assert.equal(result.applied, false);
		assert.match(result.error ?? "", new RegExp(ASTRA_MEDIUM_PROFILE.model));
		assert.equal(thinkingApplied, false);
	});

	it("stops before thinking when Pi rejects the model change", async () => {
		let thinkingApplied = false;
		const result = await applyModelProfileToRuntime({ ...ASTRA_MEDIUM_PROFILE, source: "prompt" }, {
			resolveModel: () => ({ provider: ASTRA_MEDIUM_PROFILE.provider, id: ASTRA_MEDIUM_PROFILE.model }),
			setModel: async () => false,
			setThinkingLevel: () => { thinkingApplied = true; },
		});

		assert.equal(result.applied, false);
		assert.match(result.error ?? "", /setModel/);
		assert.equal(thinkingApplied, false);
	});
});
