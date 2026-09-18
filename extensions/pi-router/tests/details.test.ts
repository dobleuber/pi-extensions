import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { ASTRA_MEDIUM_PROFILE, createDefaultModelProfileState } from "../src/model-profile.ts";
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
			routerModel: "openai-codex/gpt-5.4-mini",
			requestedThinkingLevel: "medium",
		}, { provider: "stratus", model: "stratus-code" });

		assert.equal(entry.phase, "pre-dispatch");
		assert.equal(entry.expanded, false);
		assert.equal(entry.summary, "router: es→en profile:Luna Max model:openai-codex/gpt-5.6-luna thinking:max workModel:stratus/stratus-code");
		assert.equal(entry.details.profileSource, "default");
		assert.equal(entry.details.profileModel, "openai-codex/gpt-5.6-luna");
		assert.equal(entry.details.transformedPrompt, "Improve the router.");
	});

	it("retains requested and effective profile diagnostics when application fails", () => {
		const entry = createRouterDetailsEntry({
			originalPrompt: "Use Astra: hola",
			transformedPrompt: "hola",
			sourceLanguage: "es",
			routerModel: "openai-codex/gpt-5.4-mini",
			requestedThinkingLevel: "medium",
		}, undefined, createDefaultModelProfileState(), {
			requestedProfile: { ...ASTRA_MEDIUM_PROFILE, source: "prompt" },
			profileApplicationError: "model unavailable",
		});

		assert.equal(entry.details.profile, "Luna Max");
		assert.equal(entry.details.requestedProfile, "Astra Medium");
		assert.equal(entry.details.requestedProfileModel, "openai-codex/gpt-6-astra");
		assert.equal(entry.details.requestedProfileThinkingLevel, "medium");
		assert.equal(entry.details.effectiveModel, undefined);
		assert.equal(entry.details.profileApplicationError, "model unavailable");
	});

	it("toggles details without changing routing enablement", () => {
		const entry = createRouterDetailsEntry({
			originalPrompt: "hola",
			transformedPrompt: "hello",
			sourceLanguage: "es",
			routerModel: "openai-codex/gpt-5.4-mini",
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
			routerModel: "openai-codex/gpt-5.4-mini",
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
