import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { DEFAULT_ROUTER_CONFIG } from "../src/config.ts";
import { createDefaultModelProfileState, type ModelProfileApplicationResult } from "../src/model-profile.ts";
import { prepareRoutedPrompt } from "../src/pipeline.ts";

describe("routed prompt pipeline", () => {
	it("creates collapsed router details before returning transformed work prompt", async () => {
		const prepared = await prepareRoutedPrompt({
			prompt: "mejora el router",
			config: { ...DEFAULT_ROUTER_CONFIG, state: "on" },
			workModel: { provider: "stratus", model: "stratus-code" },
			routePrompt: async () => ({
				englishPrompt: "Improve the router.",
				sourceLanguage: "es",
				thinkingLevel: "medium",
				translateFinalAnswer: true,
				usedConversationContext: false,
				resolvedReferences: [],
				unresolvedReferences: [],
			}),
		});

		assert.equal(prepared.action, "transform");
		assert.equal(prepared.prompt, "Improve the router.");
		assert.equal(prepared.details?.phase, "pre-dispatch");
		assert.equal(prepared.details?.expanded, false);
		assert.equal(prepared.details?.summary, "router: es→en profile:Luna Max model:openai-codex/gpt-5.6-luna thinking:max workModel:stratus/stratus-code");
	});

	it("warns and dispatches the original prompt when the router model is unavailable", async () => {
		const result = await prepareRoutedPrompt({
			prompt: "Dame el estado actual del router",
			config: { ...DEFAULT_ROUTER_CONFIG, state: "on" },
			routePrompt: async (prompt) => ({
				englishPrompt: prompt,
				sourceLanguage: "unknown",
				thinkingLevel: "medium",
				translateFinalAnswer: false,
				degradedReason: "router model unavailable: timeout",
			}),
		});

		assert.equal(result.action, "transform");
		assert.equal(result.prompt, "Dame el estado actual del router");
		assert.match(result.warning!, /translation unavailable; dispatching original prompt/);
	});

	it("blocks dispatch when strict router fallback mode sees an unavailable router model", async () => {
		const result = await prepareRoutedPrompt({
			prompt: "Dame el estado actual del router",
			config: {
				...DEFAULT_ROUTER_CONFIG,
				state: "on",
				routerModel: { ...DEFAULT_ROUTER_CONFIG.routerModel, fallbackMode: "error" },
			},
			routePrompt: async (prompt) => ({
				englishPrompt: prompt,
				sourceLanguage: "unknown",
				thinkingLevel: "medium",
				translateFinalAnswer: false,
				degradedReason: "router model unavailable: timeout",
			}),
		});

		assert.equal(result.action, "handled");
		assert.match(result.message, /router model unavailable: timeout/);
	});

	it("selects and strips a leading profile directive before routing", async () => {
		const appliedProfiles: string[] = [];
		let routedPrompt = "";
		const prepared = await prepareRoutedPrompt({
			prompt: "Use Astra: mejora el router",
			config: { ...DEFAULT_ROUTER_CONFIG, state: "on" },
			profileState: createDefaultModelProfileState(),
			applyModelProfile: async (profile) => {
				appliedProfiles.push(`${profile.id}:${profile.source}`);
				return { applied: true } satisfies ModelProfileApplicationResult;
			},
			routePrompt: async (prompt) => {
				routedPrompt = prompt;
				return {
					englishPrompt: "Improve the router.",
					sourceLanguage: "es",
					thinkingLevel: "medium",
					translateFinalAnswer: true,
				};
			},
		});

		assert.equal(routedPrompt, "mejora el router");
		assert.equal(prepared.action, "transform");
		assert.equal(prepared.prompt, "Improve the router.");
		assert.equal(prepared.profile.id, "astra-medium");
		assert.deepEqual(appliedProfiles, ["astra-medium:prompt"]);
		assert.match(prepared.details.summary, /profile:Astra Medium/);
	});

	it("selects and strips the Sol alias for Astra Low before routing", async () => {
		const appliedProfiles: string[] = [];
		const prepared = await prepareRoutedPrompt({
			prompt: "Use Sol: mejora el router",
			config: { ...DEFAULT_ROUTER_CONFIG, state: "on" },
			profileState: createDefaultModelProfileState(),
			applyModelProfile: async (profile) => {
				appliedProfiles.push(`${profile.id}:${profile.source}`);
				return { applied: true } satisfies ModelProfileApplicationResult;
			},
			routePrompt: async (prompt) => ({
				englishPrompt: `Improve: ${prompt}`,
				sourceLanguage: "es",
				thinkingLevel: "medium",
				translateFinalAnswer: true,
			}),
		});

		assert.equal(prepared.prompt, "Improve: mejora el router");
		assert.equal(prepared.profile.id, "astra-low");
		assert.deepEqual(appliedProfiles, ["astra-low:prompt"]);
		assert.match(prepared.details.summary, /profile:Sol/);
	});

	it("blocks dispatch and leaves the prior profile active when profile application fails", async () => {
		const result = await prepareRoutedPrompt({
			prompt: "Use Astra: mejora el router",
			config: { ...DEFAULT_ROUTER_CONFIG, state: "on" },
			profileState: createDefaultModelProfileState(),
			applyModelProfile: async () => ({ applied: false, error: "gpt-6-astra is unavailable" }),
			routePrompt: async () => ({
				englishPrompt: "Improve the router.",
				sourceLanguage: "es",
				thinkingLevel: "medium",
				translateFinalAnswer: true,
			}),
		});

		assert.equal(result.action, "handled");
		assert.match(result.message, /gpt-6-astra is unavailable/);
		assert.equal(result.profile.id, "luna-max");
	});

	it("passes through when router is off or bypass prefix is used", async () => {
		const off = await prepareRoutedPrompt({
			prompt: "mejora el router",
			config: DEFAULT_ROUTER_CONFIG,
			routePrompt: async () => { throw new Error("should not route"); },
		});
		const bypass = await prepareRoutedPrompt({
			prompt: "@router:off mejora el router",
			config: { ...DEFAULT_ROUTER_CONFIG, state: "on" },
			routePrompt: async () => { throw new Error("should not route"); },
		});

		assert.deepEqual(off, { action: "continue", prompt: "mejora el router" });
		assert.deepEqual(bypass, { action: "continue", prompt: "mejora el router", bypassed: true });
	});
});
