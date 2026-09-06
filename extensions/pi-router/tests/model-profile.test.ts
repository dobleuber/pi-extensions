import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
	ASTRA_HIGH_PROFILE,
	DEFAULT_MODEL_PROFILE,
	applyModelProfileDirective,
	createDefaultModelProfileState,
	parseModelProfilePrompt,
} from "../src/model-profile.ts";

describe("router model profile policy", () => {
	it("defines Luna Max as the default profile and Astra High as the only alternate", () => {
		assert.deepEqual(DEFAULT_MODEL_PROFILE, {
			id: "luna-max",
			label: "Luna Max",
			provider: "openai-codex",
			model: "gpt-5.6-luna",
			thinkingLevel: "max",
		});
		assert.deepEqual(ASTRA_HIGH_PROFILE, {
			id: "astra-high",
			label: "Astra High",
			provider: "openai-codex",
			model: "gpt-6-astra",
			thinkingLevel: "high",
		});
	});

	it("starts with Luna Max from the default source", () => {
		assert.deepEqual(createDefaultModelProfileState(), {
			...DEFAULT_MODEL_PROFILE,
			source: "default",
		});
	});

	it("parses the strict English Astra phrase and removes only its control text", () => {
		assert.deepEqual(parseModelProfilePrompt("  Use Astra: fix the router"), {
			prompt: "fix the router",
			profile: "astra-high",
			source: "prompt",
		});
	});

	it("parses the strict Spanish Astra phrase case-insensitively", () => {
		assert.deepEqual(parseModelProfilePrompt("uSa AsTrA: arregla el router"), {
			prompt: "arregla el router",
			profile: "astra-high",
			source: "prompt",
		});
	});

	it("parses English and Spanish default reset phrases", () => {
		assert.deepEqual(parseModelProfilePrompt("Use Default: continue"), {
			prompt: "continue",
			profile: "luna-max",
			source: "default",
		});
		assert.deepEqual(parseModelProfilePrompt("Usa el modelo predeterminado: continúa"), {
			prompt: "continúa",
			profile: "luna-max",
			source: "default",
		});
	});

	it("does not select a profile for body mentions, unsupported phrases, or legacy thinking syntax", () => {
		for (const prompt of [
			"Please mention Use Astra: only as an example",
			"Use Astra without the delimiter",
			"Use Astra:",
			"Use Astra:   ",
			"Use Luna Max: use the normal profile",
			"@thinking:max fix the router",
			"```\nUse Astra: do not select this\n```",
		]) {
			assert.deepEqual(parseModelProfilePrompt(prompt), { prompt });
		}
	});

	it("changes the session state only for a recognized directive", () => {
		const initial = createDefaultModelProfileState();
		const selected = parseModelProfilePrompt("Use Astra: investigate");
		const reset = parseModelProfilePrompt("Use Default: investigate");

		assert.deepEqual(applyModelProfileDirective(initial, selected), {
			...ASTRA_HIGH_PROFILE,
			source: "prompt",
		});
		assert.deepEqual(applyModelProfileDirective({ ...ASTRA_HIGH_PROFILE, source: "prompt" }, reset), {
			...DEFAULT_MODEL_PROFILE,
			source: "default",
		});
		assert.deepEqual(applyModelProfileDirective(initial, { prompt: "ordinary task" }), initial);
	});
});
