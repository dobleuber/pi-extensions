import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { ASTRA_LOW_PROFILE, ASTRA_MEDIUM_PROFILE, applyModelProfileToRuntime, type ModelProfileRuntime } from "../src/model-profile.ts";

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
			getEffectiveModel: () => ({ provider: "openai-codex", model: "gpt-6-astra" }),
			getEffectiveThinkingLevel: () => "medium",
		};

		const result = await applyModelProfileToRuntime({ ...ASTRA_MEDIUM_PROFILE, source: "prompt" }, runtime);

		assert.deepEqual(result, {
			applied: true,
			effectiveModel: { provider: "openai-codex", model: "gpt-6-astra" },
			effectiveThinkingLevel: "medium",
		});
		assert.deepEqual(calls, [
			"resolve:openai-codex/gpt-6-astra",
			"model:gpt-6-astra",
			"thinking:medium",
		]);
	});

	it("applies the Sol profile with low thinking", async () => {
		let thinkingLevel = "";
		const result = await applyModelProfileToRuntime({ ...ASTRA_LOW_PROFILE, source: "prompt" }, {
			resolveModel: (provider, model) => ({ provider, id: model }),
			setModel: async () => true,
			setThinkingLevel: (level) => { thinkingLevel = level; },
			getEffectiveModel: () => ({ provider: "openai-codex", model: "gpt-6-astra" }),
			getEffectiveThinkingLevel: () => thinkingLevel,
		});

		assert.equal(result.applied, true);
		assert.equal(thinkingLevel, "low");
		assert.equal(result.effectiveThinkingLevel, "low");
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
		assert.match(result.error ?? "", /gpt-6-astra/);
		assert.equal(thinkingApplied, false);
	});

	it("stops before thinking when Pi rejects the model change", async () => {
		let thinkingApplied = false;
		const result = await applyModelProfileToRuntime({ ...ASTRA_MEDIUM_PROFILE, source: "prompt" }, {
			resolveModel: () => ({ provider: "openai-codex", id: "gpt-6-astra" }),
			setModel: async () => false,
			setThinkingLevel: () => { thinkingApplied = true; },
		});

		assert.equal(result.applied, false);
		assert.match(result.error ?? "", /setModel/);
		assert.equal(thinkingApplied, false);
	});
});
