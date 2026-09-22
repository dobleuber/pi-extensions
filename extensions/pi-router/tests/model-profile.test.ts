import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
	ASTRA_MEDIUM_PROFILE,
	DEFAULT_MODEL_PROFILE,
	SOL_PROFILE,
	applyModelProfileDirective,
	createDefaultModelProfileState,
	parseModelProfilePrompt,
} from "../src/model-profile.ts";

describe("router model profile policy", () => {
	it("selects Sol at xhigh", () => {
		assert.equal(SOL_PROFILE.thinkingLevel, "xhigh");
	});
	it("does not select the disabled Terra profile", () => {
		for (const prefix of ["Use Terra:", "Usa Terra:"]) {
			const prompt = `${prefix} implement the integration`;
			assert.deepEqual(parseModelProfilePrompt(prompt), { prompt });
		}
	});
	it("starts with Luna Max from the default source", () => {
		assert.deepEqual(createDefaultModelProfileState(), {
			...DEFAULT_MODEL_PROFILE,
			source: "default",
		});
	});

	it("parses supported directives case-insensitively and strips their control text", () => {
		const cases = [
			["  Use Astra: fix the router", { prompt: "fix the router", profile: "astra-medium", source: "prompt" }],
			["uSa AsTrA: arregla el router", { prompt: "arregla el router", profile: "astra-medium", source: "prompt" }],
			["  Use Sol: use the new profile", { prompt: "use the new profile", profile: "sol", source: "prompt" }],
			["uSa SoL: usa el perfil nuevo", { prompt: "usa el perfil nuevo", profile: "sol", source: "prompt" }],
			["Use Default: continue", { prompt: "continue", profile: "luna-max", source: "default" }],
			["Usa el modelo predeterminado: continúa", { prompt: "continúa", profile: "luna-max", source: "default" }],
		] as const;

		for (const [prompt, expected] of cases) assert.deepEqual(parseModelProfilePrompt(prompt), expected);
	});

	it("does not select a profile for body mentions, unsupported phrases, or legacy thinking syntax", () => {
		for (const prompt of [
			"Please mention Use Astra: only as an example",
			"Use Astra without the delimiter",
			"Use Astra:",
			"Use Astra:   ",
			"Use Sol without the delimiter",
			"Use Sol:",
			"Use Sol:   ",
			"Use Terra: use the disabled profile",
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
			...ASTRA_MEDIUM_PROFILE,
			source: "prompt",
		});
		assert.deepEqual(applyModelProfileDirective(initial, parseModelProfilePrompt("Use Sol: use the new profile")), {
			...SOL_PROFILE,
			source: "prompt",
		});
		assert.deepEqual(applyModelProfileDirective({ ...ASTRA_MEDIUM_PROFILE, source: "prompt" }, reset), {
			...DEFAULT_MODEL_PROFILE,
			source: "default",
		});
		assert.deepEqual(applyModelProfileDirective(initial, { prompt: "ordinary task" }), initial);
	});
});
