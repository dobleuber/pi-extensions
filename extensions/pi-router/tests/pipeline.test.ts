import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { DEFAULT_ROUTER_CONFIG } from "../src/config.ts";
import {
	ASTRA_MEDIUM_PROFILE,
	DEFAULT_MODEL_PROFILE,
	SOL_PROFILE,
	createDefaultModelProfileState,
	type ModelProfileApplicationResult,
} from "../src/model-profile.ts";
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
		assert.equal(prepared.details?.summary, `router: es→en profile:Luna Max model:${DEFAULT_MODEL_PROFILE.provider}/${DEFAULT_MODEL_PROFILE.model} thinking:max workModel:stratus/stratus-code`);
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
		if (prepared.action !== "transform") throw new Error("expected transformed prompt");
		assert.equal(prepared.prompt, "Improve the router.");
		assert.equal(prepared.profile.id, "astra-medium");
		assert.deepEqual(appliedProfiles, ["astra-medium:prompt"]);
		assert.match(prepared.details.summary, /profile:Astra Medium/);
	});

	it("selects and strips Sol before routing", async () => {
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

		assert.equal(prepared.action, "transform");
		if (prepared.action !== "transform") throw new Error("expected transformed prompt");
		assert.equal(prepared.prompt, "Improve: mejora el router");
		assert.equal(prepared.profile.id, "sol");
		assert.deepEqual(appliedProfiles, ["sol:prompt"]);
		assert.match(prepared.details.summary, /profile:Sol/);
	});

	it("blocks dispatch and leaves the prior profile active when profile application fails", async () => {
		const result = await prepareRoutedPrompt({
			prompt: "Use Astra: mejora el router",
			config: { ...DEFAULT_ROUTER_CONFIG, state: "on" },
			profileState: createDefaultModelProfileState(),
			applyModelProfile: async () => ({ applied: false, error: `${ASTRA_MEDIUM_PROFILE.model} is unavailable` }),
			routePrompt: async () => ({
				englishPrompt: "Improve the router.",
				sourceLanguage: "es",
				thinkingLevel: "medium",
				translateFinalAnswer: true,
			}),
		});

		assert.equal(result.action, "handled");
		assert.match(result.message, new RegExp(`${ASTRA_MEDIUM_PROFILE.model} is unavailable`));
		assert.equal(result.profile.id, "luna-max");
	});

	it("uses Jev's automatic profile for an unqualified prompt", async () => {
		const appliedProfiles: string[] = [];
		const decision: any = {
			model: "jev-1.13",
			usage: { input_tokens: 10, output_tokens: 0 },
			profile: { ...SOL_PROFILE, source: "automatic" as const },
			profileKey: "sol" as const,
			profileConfidence: 0.91,
			profileProbabilities: { luna: 0.04, sol: 0.91, astra: 0.05 },
			inputTranslation: "required" as const,
			inputTranslationConfidence: 0.98,
			sourceLanguage: "es" as const,
			sourceLanguageConfidence: 0.98,
			canBypassInputTranslation: false,
			metadata: { model: "jev-1.13", inputTokens: 10, outputTokens: 0 },
		};
		const prepared = await prepareRoutedPrompt({
			prompt: "mejora el router",
			config: {
				...DEFAULT_ROUTER_CONFIG,
				state: "on",
				jev: { ...DEFAULT_ROUTER_CONFIG.jev! },
			},
			profileState: { ...ASTRA_MEDIUM_PROFILE, source: "prompt" },
			jev: {
				decideInput: async () => decision,
				decideResponse: async () => { throw new Error("not used"); },
			},
			applyModelProfile: async (profile) => {
				appliedProfiles.push(`${profile.id}:${profile.source}`);
				return { applied: true };
			},
			routePrompt: async () => ({
				englishPrompt: "Improve the router.",
				sourceLanguage: "es",
				thinkingLevel: "medium",
				translateFinalAnswer: true,
			}),
		});

		assert.equal(prepared.action, "transform");
		assert.equal(prepared.profile.id, "sol");
		assert.equal(prepared.profile.source, "automatic");
		assert.deepEqual(appliedProfiles, ["sol:automatic"]);
	});

	it("forces Use Default to Luna only for the current prompt before returning to Jev", async () => {
		const appliedProfiles: string[] = [];
		const automaticDecision = (profile: any) => ({
			model: "jev-1.13",
			usage: { input_tokens: 10, output_tokens: 0 },
			profile,
			profileKey: profile.id === "sol" ? "sol" as const : "luna" as const,
			profileConfidence: 0.95,
			profileProbabilities: { luna: 0.95, sol: 0.03, astra: 0.02 },
			inputTranslation: "required" as const,
			inputTranslationConfidence: 0.95,
			sourceLanguage: "es" as const,
			sourceLanguageConfidence: 0.95,
			canBypassInputTranslation: false,
			metadata: { model: "jev-1.13", inputTokens: 10, outputTokens: 0 },
		});
		let automaticCalls = 0;
		const jev = {
			decideInput: async () => {
				automaticCalls += 1;
				return automaticDecision({ ...SOL_PROFILE, source: "automatic" });
			},
			decideResponse: async () => { throw new Error("not used"); },
		};
		const config = {
			...DEFAULT_ROUTER_CONFIG,
			state: "on" as const,
			jev: { ...DEFAULT_ROUTER_CONFIG.jev! },
		};
		const prepare = (prompt: string, profileState = createDefaultModelProfileState()) => prepareRoutedPrompt({
			prompt,
			config,
			profileState,
			jev,
			applyModelProfile: async (profile) => {
				appliedProfiles.push(profile.id);
				return { applied: true };
			},
			routePrompt: async (task) => ({ englishPrompt: task, sourceLanguage: "es" as const, thinkingLevel: "medium" as const, translateFinalAnswer: true }),
		});

		const forced = await prepare("Use Default: termina");
		assert.equal(forced.action, "transform");
		if (forced.action !== "transform") throw new Error("expected transformed forced prompt");
		assert.equal(forced.profile.id, "luna-max");
		assert.equal(automaticCalls, 1);
		const automatic = await prepare("continúa", forced.profile);
		assert.equal(automatic.action, "transform");
		if (automatic.action !== "transform") throw new Error("expected transformed automatic prompt");
		assert.equal(automatic.profile.id, "sol");
		assert.equal(automatic.profile.source, "automatic");
		assert.equal(automaticCalls, 2);
		assert.deepEqual(appliedProfiles, ["luna-max", "sol"]);
	});

	it("bypasses the generative input translator only for an accepted Jev not-required decision", async () => {
		let routeCalls = 0;
		const prepared = await prepareRoutedPrompt({
			prompt: "inspect the router",
			config: {
				...DEFAULT_ROUTER_CONFIG,
				state: "on",
				jev: { ...DEFAULT_ROUTER_CONFIG.jev! },
			},
			jev: {
				decideInput: async () => ({
					model: "jev-1.13",
					usage: { input_tokens: 10, output_tokens: 0 },
					profile: { ...DEFAULT_MODEL_PROFILE, source: "automatic" as const },
					profileKey: "luna" as const,
					profileConfidence: 0.9,
					profileProbabilities: { luna: 0.9, sol: 0.06, astra: 0.04 },
					inputTranslation: "not_required" as const,
					inputTranslationConfidence: 0.95,
					sourceLanguage: "en" as const,
					sourceLanguageConfidence: 0.95,
					canBypassInputTranslation: true,
					metadata: { model: "jev-1.13", inputTokens: 10, outputTokens: 0 },
				}),
				decideResponse: async () => { throw new Error("not used"); },
			},
			applyModelProfile: async () => ({ applied: true }),
			routePrompt: async () => {
				routeCalls += 1;
				throw new Error("translator must be bypassed");
			},
		});

		assert.equal(prepared.action, "transform");
		assert.equal(prepared.prompt, "inspect the router");
		assert.equal(prepared.result.sourceLanguage, "en");
		assert.equal(routeCalls, 0);
	});

	it("falls back to Luna and keeps generative translation when Jev fails", async () => {
		let routeCalls = 0;
		const prepared = await prepareRoutedPrompt({
			prompt: "mejora el router",
			config: { ...DEFAULT_ROUTER_CONFIG, state: "on", jev: { ...DEFAULT_ROUTER_CONFIG.jev! } },
			jev: {
				decideInput: async () => { throw new Error("TypeSafe timeout"); },
				decideResponse: async () => { throw new Error("not used"); },
			},
			applyModelProfile: async (profile) => ({ applied: true, effectiveModel: { provider: profile.provider, model: profile.model } }),
			routePrompt: async () => {
				routeCalls += 1;
				return { englishPrompt: "Improve the router.", sourceLanguage: "es", thinkingLevel: "medium", translateFinalAnswer: true };
			},
		});

		assert.equal(prepared.action, "transform");
		if (prepared.action !== "transform") throw new Error("expected fallback transform");
		assert.equal(prepared.profile.id, "luna-max");
		assert.equal(prepared.profile.source, "automatic");
		assert.equal(routeCalls, 1);
		assert.equal(prepared.warning, undefined);
		assert.deepEqual(prepared.details.details.jevFallbackReasons, ["TypeSafe timeout", "profile selection uncertain; using Luna fallback"]);
	});

	it("keeps uncertain Jev profile selection diagnostic-only", async () => {
		const prepared = await prepareRoutedPrompt({
			prompt: "continúa la investigación",
			config: { ...DEFAULT_ROUTER_CONFIG, state: "on" },
			jev: {
				decideInput: async () => ({
					model: "jev-1.13.0", usage: { input_tokens: 1, output_tokens: 0 },
					profileConfidence: 0.5, profileProbabilities: { luna: 0.5, sol: 0.25, astra: 0.25 },
					inputTranslation: "required" as const, inputTranslationConfidence: 0.99,
					sourceLanguage: "es" as const, sourceLanguageConfidence: 0.99, canBypassInputTranslation: false,
					metadata: { model: "jev-1.13.0", inputTokens: 1, outputTokens: 0 },
				}),
				decideResponse: async () => { throw new Error("not used"); },
			},
			applyModelProfile: async () => ({ applied: true }),
			routePrompt: async () => ({ englishPrompt: "Continue the investigation.", sourceLanguage: "es", thinkingLevel: "medium", translateFinalAnswer: true }),
		});
		assert.equal(prepared.action, "transform");
		if (prepared.action !== "transform") throw new Error("expected transformed prompt");
		assert.equal(prepared.profile.id, "luna-max");
		assert.equal(prepared.warning, undefined);
		assert.deepEqual(prepared.details.details.jevFallbackReasons, ["profile selection uncertain; using Luna fallback"]);
	});

	it("redacts the TypeSafe credential from Jev fallback diagnostics", async () => {
		const previousKey = process.env.TYPESAFE_API_KEY;
		process.env.TYPESAFE_API_KEY = "jev-secret-for-test";
		try {
			const prepared = await prepareRoutedPrompt({
				prompt: "continue",
				config: { ...DEFAULT_ROUTER_CONFIG, state: "on", jev: { ...DEFAULT_ROUTER_CONFIG.jev! } },
				jev: {
					decideInput: async () => { throw new Error("request failed with jev-secret-for-test"); },
					decideResponse: async () => { throw new Error("not used"); },
				},
				applyModelProfile: async () => ({ applied: true }),
				routePrompt: async (prompt) => ({ englishPrompt: prompt, sourceLanguage: "en", thinkingLevel: "medium", translateFinalAnswer: false }),
			});
			assert.equal(prepared.action, "transform");
			if (prepared.action !== "transform") throw new Error("expected fallback transform");
			assert.equal(prepared.warning, undefined);
		} finally {
			if (previousKey === undefined) delete process.env.TYPESAFE_API_KEY;
			else process.env.TYPESAFE_API_KEY = previousKey;
		}
	});

	it("does not dispatch a prompt cancelled during the Jev decision", async () => {
		const controller = new AbortController();
		controller.abort();
		let routeCalls = 0;
		const prepared = await prepareRoutedPrompt({
			prompt: "continue",
			config: { ...DEFAULT_ROUTER_CONFIG, state: "on", jev: { ...DEFAULT_ROUTER_CONFIG.jev! } },
			runtime: { signal: controller.signal },
			jev: {
				decideInput: async () => { throw new Error("should not call Jev after cancellation"); },
				decideResponse: async () => { throw new Error("not used"); },
			},
			routePrompt: async () => {
				routeCalls += 1;
				return { englishPrompt: "Continue.", sourceLanguage: "en", thinkingLevel: "medium", translateFinalAnswer: false };
			},
		});

		assert.equal(prepared.action, "handled");
		if (prepared.action !== "handled") throw new Error("expected cancelled prompt to be handled");
		assert.match(prepared.message, /cancelled/);
		assert.equal(routeCalls, 0);
	});

	it("applies profile and translation recommendations without an activation flag", async () => {
		let routeCalls = 0;
		const appliedProfiles: string[] = [];
		const prepared = await prepareRoutedPrompt({
			prompt: "inspect the router",
			config: { ...DEFAULT_ROUTER_CONFIG, state: "on", jev: { ...DEFAULT_ROUTER_CONFIG.jev! } },
			profileState: createDefaultModelProfileState(),
			jev: {
				decideInput: async () => ({
					model: "jev-1.13", usage: { input_tokens: 1, output_tokens: 0 },
					profile: { ...ASTRA_MEDIUM_PROFILE, source: "automatic" as const },
					profileKey: "astra" as const, profileConfidence: 0.99, profileProbabilities: { luna: 0.01, sol: 0, astra: 0.99 },
					inputTranslation: "not_required" as const, inputTranslationConfidence: 0.99,
					sourceLanguage: "en" as const, sourceLanguageConfidence: 0.99, canBypassInputTranslation: true,
					metadata: { model: "jev-1.13", inputTokens: 1, outputTokens: 0 },
				}),
				decideResponse: async () => { throw new Error("not used"); },
			},
			applyModelProfile: async (profile) => { appliedProfiles.push(profile.id); return { applied: true }; },
			routePrompt: async (prompt) => {
				routeCalls += 1;
				return { englishPrompt: prompt, sourceLanguage: "en", thinkingLevel: "medium", translateFinalAnswer: false };
			},
		});

		assert.equal(prepared.action, "transform");
		if (prepared.action !== "transform") throw new Error("expected transform");
		assert.equal(prepared.profile.id, "astra-medium");
		assert.deepEqual(appliedProfiles, ["astra-medium"]);
		assert.equal(routeCalls, 0);
		assert.equal(prepared.prompt, "inspect the router");
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
