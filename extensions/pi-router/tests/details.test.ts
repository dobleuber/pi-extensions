import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { ASTRA_MEDIUM_PROFILE, DEFAULT_MODEL_PROFILE, createDefaultModelProfileState } from "../src/model-profile.ts";
import {
	createRouterDetailsEntry,
	extendRouterDetailsAfterCompletion,
	parseSinglePromptBypass,
	resolveDetailsShortcut,
	toggleRouterDetails,
} from "../src/details.ts";

describe("router details UX model", () => {
	it("creates compact collapsed pre-dispatch details", () => {
		const entry = createRouterDetailsEntry({
			originalPrompt: "mejora el router",
			transformedPrompt: "Improve the router.",
			sourceLanguage: "es",
			routerModel: "test-router",
			requestedThinkingLevel: "medium",
		}, { provider: "stratus", model: "stratus-code" });

		assert.equal(entry.phase, "pre-dispatch");
		assert.equal(entry.expanded, false);
		assert.equal(entry.summary, `router: es→en profile:Luna Max model:${DEFAULT_MODEL_PROFILE.provider}/${DEFAULT_MODEL_PROFILE.model} thinking:max workModel:stratus/stratus-code`);
		assert.equal(entry.details.profileSource, "default");
		assert.equal(entry.details.profileModel, `${DEFAULT_MODEL_PROFILE.provider}/${DEFAULT_MODEL_PROFILE.model}`);
		assert.equal(entry.details.transformedPrompt, "Improve the router.");
	});

	it("retains requested and effective profile diagnostics when application fails", () => {
		const entry = createRouterDetailsEntry({
			originalPrompt: "Use Astra: hola",
			transformedPrompt: "hola",
			sourceLanguage: "es",
			routerModel: "test-router",
			requestedThinkingLevel: "medium",
		}, undefined, createDefaultModelProfileState(), {
			requestedProfile: { ...ASTRA_MEDIUM_PROFILE, source: "prompt" },
			profileApplicationError: "model unavailable",
		});

		assert.equal(entry.details.profile, "Luna Max");
		assert.equal(entry.details.requestedProfile, "Astra Medium");
		assert.equal(entry.details.requestedProfileModel, `${ASTRA_MEDIUM_PROFILE.provider}/${ASTRA_MEDIUM_PROFILE.model}`);
		assert.equal(entry.details.requestedProfileThinkingLevel, "medium");
		assert.equal(entry.details.effectiveModel, undefined);
		assert.equal(entry.details.profileApplicationError, "model unavailable");
	});

	it("toggles details without changing routing enablement", () => {
		const entry = createRouterDetailsEntry({
			originalPrompt: "hola",
			transformedPrompt: "hello",
			sourceLanguage: "es",
			routerModel: "test-router",
			requestedThinkingLevel: "low",
		}, undefined);

		const expanded = toggleRouterDetails(entry);
		assert.equal(expanded.expanded, true);
		assert.equal(expanded.routingState, entry.routingState);
		assert.equal(toggleRouterDetails(expanded).expanded, false);
	});

	it("extends details after completion with English and Spanish answers", () => {
		const entry = createRouterDetailsEntry({
			originalPrompt: "hola",
			transformedPrompt: "hello",
			sourceLanguage: "es",
			routerModel: "test-router",
			requestedThinkingLevel: "low",
		}, undefined);

		const completed = extendRouterDetailsAfterCompletion(entry, {
			englishAnswer: "Done.",
			spanishAnswer: "Listo.",
			effectiveThinkingLevel: "low",
			fallbackEvents: ["none"],
		});

		assert.equal(completed.phase, "complete");
		assert.equal(completed.details.englishAnswer, "Done.");
		assert.equal(completed.details.spanishAnswer, "Listo.");
		assert.deepEqual(completed.details.fallbackEvents, ["none"]);
	});

	it("parses bypass prefix and resolves configurable details shortcut", () => {
		assert.deepEqual(parseSinglePromptBypass("@router:off envia esto literal"), {
			bypass: true,
			prompt: "envia esto literal",
		});
		assert.deepEqual(parseSinglePromptBypass("@router:offline inspect"), {
			bypass: false,
			prompt: "@router:offline inspect",
		});
		assert.deepEqual(parseSinglePromptBypass("@router:off"), {
			bypass: false,
			prompt: "@router:off",
		});
		assert.deepEqual(parseSinglePromptBypass("hola"), { bypass: false, prompt: "hola" });

		assert.deepEqual(resolveDetailsShortcut(), { shortcut: "ctrl+alt+r" });
		assert.deepEqual(resolveDetailsShortcut("ctrl+r"), {
			shortcut: "ctrl+r",
			conflict: "ctrl+r conflicts with Pi session rename unless remapped",
		});
		assert.deepEqual(resolveDetailsShortcut("ctrl+t"), {
			shortcut: "ctrl+t",
			conflict: "ctrl+t conflicts with Pi thinking/tree toggles unless remapped",
		});
		assert.deepEqual(resolveDetailsShortcut("ctrl+shift+r"), {
			shortcut: "ctrl+shift+r",
			conflict: "ctrl+shift+r conflicts with the files extension restore shortcut",
		});
	});
});
