import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { DEFAULT_ROUTER_CONFIG } from "../src/config.ts";
import { DEFAULT_MODEL_PROFILE } from "../src/model-profile.ts";
import type { PiAiRuntime } from "../src/pi-ai-client.ts";
import { createRouterMetadata, routePromptWithModel } from "../src/router-model.ts";

const TEST_ROUTER_CONFIG = {
	...DEFAULT_ROUTER_CONFIG.routerModel,
	provider: "test-router",
	model: "test-mini",
};

function runtimeFor(content: string, capture?: { model?: any; context?: any; options?: any; authModel?: any }): PiAiRuntime {
	return {
		modelRegistry: {
			find(provider, model) {
				const resolved = { provider, id: model, api: "test-api" };
				if (capture) capture.model = resolved;
				return resolved as any;
			},
			async getApiKeyAndHeaders(model) {
				if (capture) capture.authModel = model;
				return { ok: true, apiKey: "test-token", headers: { "x-test": "header" } };
			},
		},
		complete: (async (model: any, context: any, options: any) => {
			if (capture) {
				capture.model = model;
				capture.context = context;
				capture.options = options;
			}
			return {
				role: "assistant",
				stopReason: "stop",
				content: [{ type: "text", text: content }],
				timestamp: Date.now(),
			} as any;
		}) as any,
	};
}

describe("remote router model", () => {
	it("dispatches default prompt routing to Luna without reasoning", async () => {
		const capture: any = {};
		const result = await routePromptWithModel(
			"Revisa el router.",
			DEFAULT_ROUTER_CONFIG.routerModel,
			{},
			runtimeFor(JSON.stringify({ sourceLanguage: "es", translation: "Review the router.", translateFinalAnswer: true }), capture),
		);

		assert.equal(capture.model.provider, "openai-codex");
		assert.equal(capture.model.id, DEFAULT_MODEL_PROFILE.model);
		assert.equal(capture.options.reasoningEffort, "none");
		assert.equal(result.englishPrompt, "Review the router.");
		assert.equal(result.degradedReason, undefined);
	});

	it("resolves the configured model and auth through Pi before completing", async () => {
		const capture: any = {};
		const result = await routePromptWithModel(
			"mejora el router de Pi",
			TEST_ROUTER_CONFIG,
			{},
			runtimeFor(JSON.stringify({
				sourceLanguage: "es",
				translation: "Improve the Pi router.",
				thinkingLevel: "medium",
				translateFinalAnswer: true,
				usedConversationContext: false,
				resolvedReferences: [],
				unresolvedReferences: [],
			}), capture),
		);

		assert.deepEqual(capture.model, { provider: "test-router", id: "test-mini", api: "test-api" });
		assert.equal(capture.authModel, capture.model);
		assert.equal(capture.options.apiKey, "test-token");
		assert.deepEqual(capture.options.headers, { "x-test": "header" });
		assert.equal(capture.options.timeoutMs, TEST_ROUTER_CONFIG.timeoutMs);
		assert.equal(capture.options.reasoningEffort, "none");
		assert.match(capture.context.systemPrompt, /Return ONLY one JSON object/);
		assert.match(capture.context.systemPrompt, /natural, idiomatic English/);
		assert.match(capture.context.systemPrompt, /translation value must contain only the translated task/);
		assert.deepEqual(JSON.parse(capture.context.messages[0].content[0].text), { task: "mejora el router de Pi" });
		assert.equal(result.englishPrompt, "Improve the Pi router.");
		assert.equal(result.sourceLanguage, "es");
		assert.equal(result.thinkingLevel, "medium");
		assert.equal(result.translateFinalAnswer, true);
	});

	it("sends conversation context only for faithful reference resolution", async () => {
		let context: any;
		const runtime = runtimeFor(JSON.stringify({
			sourceLanguage: "es",
			translation: "Add the router details toggle to the Pi router.",
			translateFinalAnswer: true,
			usedConversationContext: true,
			resolvedReferences: ["eso = router details toggle"],
			unresolvedReferences: [],
		}));
		const originalComplete = runtime.complete!;
		runtime.complete = (async (model: any, value: any, options: any) => {
			context = value;
			return originalComplete(model, value, options);
		}) as any;

		const result = await routePromptWithModel(
			"agrega eso al router de Pi",
			TEST_ROUTER_CONFIG,
			{ conversationSummary: "The current topic is adding a router details toggle." },
			runtime,
		);

		assert.deepEqual(JSON.parse(context.messages[0].content[0].text), {
			task: "agrega eso al router de Pi",
			conversationContext: "The current topic is adding a router details toggle.",
		});
		assert.equal(result.usedConversationContext, true);
		assert.deepEqual(result.resolvedReferences, ["eso = router details toggle"]);
	});

	it("unwraps a router input envelope echoed inside the translated task", async () => {
		const translatedTask = "Implement the reviewed specification.";
		const echoedEnvelope = JSON.stringify({
			task: translatedTask,
			conversationContext: "Prior discussion that must not be copied into the task.",
		});
		const result = await routePromptWithModel(
			"Implementa la especificación revisada.",
			TEST_ROUTER_CONFIG,
			{ conversationSummary: "Prior discussion that must not be copied into the task." },
			runtimeFor(JSON.stringify({
				sourceLanguage: "es",
				translation: echoedEnvelope,
				translateFinalAnswer: true,
			})),
		);

		assert.equal(result.englishPrompt, translatedTask);
		assert.equal(result.degradedReason, undefined);
	});

	it("preserves user-authored JSON with a task field", async () => {
		const originalJson = JSON.stringify({ task: "review this payload" });
		const result = await routePromptWithModel(
			originalJson,
			TEST_ROUTER_CONFIG,
			{},
			runtimeFor(JSON.stringify({
				sourceLanguage: "en",
				translation: originalJson,
				translateFinalAnswer: false,
			})),
		);

		assert.equal(result.englishPrompt, originalJson);
	});

	it("preserves paths and fenced blocks through opaque placeholders", async () => {
		const path = "openspec/changes/router-remote/";
		let context: any;
		const runtime = runtimeFor(JSON.stringify({
			sourceLanguage: "es",
			translation: "Review §P0§ and __PI_ROUTER_PRESERVED_BLOCK_0__.",
			translateFinalAnswer: true,
		}));
		const originalComplete = runtime.complete!;
		runtime.complete = (async (model: any, value: any, options: any) => {
			context = value;
			return originalComplete(model, value, options);
		}) as any;
		const fenced = "```txt\nkeep exact\n```";

		const result = await routePromptWithModel(`Revisa ${path}\n${fenced}`, TEST_ROUTER_CONFIG, {}, runtime);

		const routedInput = JSON.parse(context.messages[0].content[0].text);
		assert.doesNotMatch(routedInput.task, /router-remote/);
		assert.doesNotMatch(routedInput.task, /keep exact/);
		assert.match(routedInput.task, /§P0§/);
		assert.match(routedInput.task, /__PI_ROUTER_PRESERVED_BLOCK_0__/);
		assert.equal(result.englishPrompt, `Review ${path} and ${fenced}.`);
	});

	it("preserves relative directory paths without extensions through routing", async () => {
		let context: any;
		const runtime = runtimeFor(JSON.stringify({
			sourceLanguage: "es",
			translation: "Review §P0§ carefully.",
			translateFinalAnswer: true,
		}));
		const originalComplete = runtime.complete!;
		runtime.complete = (async (model: any, value: any, options: any) => {
			context = value;
			return originalComplete(model, value, options);
		}) as any;

		const result = await routePromptWithModel("Revisa extensions/pi-router.", TEST_ROUTER_CONFIG, {}, runtime);

		assert.doesNotMatch(context.messages[0].content[0].text, /extensions\/pi-router/);
		assert.match(context.messages[0].content[0].text, /§P0§/);
		assert.equal(result.englishPrompt, "Review extensions/pi-router carefully.");
	});

	it("accepts a faithful translation when ordinary prose line breaks are joined", async () => {
		const result = await routePromptWithModel(
			"Revisa el router.\nNo hagas cambios todavía.\nEnumera los riesgos.",
			TEST_ROUTER_CONFIG,
			{},
			runtimeFor(JSON.stringify({
				sourceLanguage: "es",
				translation: "Review the router. Don't make changes yet. List the risks.",
				translateFinalAnswer: true,
			})),
		);

		assert.equal(result.englishPrompt, "Review the router. Don't make changes yet. List the risks.");
		assert.equal(result.sourceLanguage, "es");
		assert.equal(result.degradedReason, undefined);
	});

	it("accepts a translation when Markdown list layout changes", async () => {
		const prompt = "Revisa estas reglas:\n- conserva la estructura\n- ejecuta las pruebas";
		const result = await routePromptWithModel(
			prompt,
			TEST_ROUTER_CONFIG,
			{},
			runtimeFor(JSON.stringify({
				sourceLanguage: "es",
				translation: "Review these rules: preserve the structure and run the tests.",
				translateFinalAnswer: true,
			})),
		);

		assert.equal(result.englishPrompt, "Review these rules: preserve the structure and run the tests.");
		assert.equal(result.degradedReason, undefined);
	});

	it("accepts a translation when paragraph boundaries change", async () => {
		const result = await routePromptWithModel(
			"Revisa el router.\n\nEnumera los riesgos.",
			TEST_ROUTER_CONFIG,
			{},
			runtimeFor(JSON.stringify({
				sourceLanguage: "es",
				translation: "Review the router. List the risks.",
				translateFinalAnswer: true,
			})),
		);

		assert.equal(result.englishPrompt, "Review the router. List the risks.");
		assert.equal(result.degradedReason, undefined);
	});

	it("rejects contaminated non-JSON output instead of guessing at a translation", async () => {
		const result = await routePromptWithModel(
			"Dame el estado actual del router",
			TEST_ROUTER_CONFIG,
			{},
			runtimeFor("No, no estoy asumiendo nada.\n{\"translation\":\"What is the status?\"}"),
		);

		assert.equal(result.englishPrompt, "Dame el estado actual del router");
		assert.match(result.degradedReason ?? "", /router model returned invalid JSON/);
	});

	it("records unresolved references without inventing intent", async () => {
		const result = await routePromptWithModel(
			"continua con eso",
			TEST_ROUTER_CONFIG,
			{},
			runtimeFor(JSON.stringify({
				sourceLanguage: "es",
				translation: "Continue with that.",
				translateFinalAnswer: true,
				usedConversationContext: false,
				resolvedReferences: [],
				unresolvedReferences: ["eso"],
			})),
		);
		assert.deepEqual(result.unresolvedReferences, ["eso"]);
		assert.deepEqual(createRouterMetadata({ originalPrompt: "continua con eso", result, routerModel: TEST_ROUTER_CONFIG }).unresolvedReferences, ["eso"]);
	});

	it("uses a conservative final-answer decision for Spanish and English source text", async () => {
		const spanish = await routePromptWithModel("hola", TEST_ROUTER_CONFIG, {}, runtimeFor(JSON.stringify({
			sourceLanguage: "es", translation: "Hello", translateFinalAnswer: false,
		})));
		const english = await routePromptWithModel("hello", TEST_ROUTER_CONFIG, {}, runtimeFor(JSON.stringify({
			sourceLanguage: "en", translation: "hello", translateFinalAnswer: false,
		})));

		assert.equal(spanish.translateFinalAnswer, true);
		assert.equal(english.translateFinalAnswer, false);
	});

	it("passes the active Pi abort signal to the provider adapter", async () => {
		const signal = new AbortController().signal;
		const capture: any = {};
		await routePromptWithModel("hello", TEST_ROUTER_CONFIG, {}, {
			...runtimeFor(JSON.stringify({ sourceLanguage: "en", translation: "hello", translateFinalAnswer: false }), capture),
			signal,
		});
		assert.equal(capture.options.signal, signal);
	});

	it("falls back when the registry/model is unavailable or input is oversized", async () => {
		const unavailable = await routePromptWithModel("hola", TEST_ROUTER_CONFIG);
		const oversized = await routePromptWithModel("x".repeat(TEST_ROUTER_CONFIG.maxInputChars + 1), TEST_ROUTER_CONFIG, {}, runtimeFor("should not run"));

		assert.equal(unavailable.englishPrompt, "hola");
		assert.match(unavailable.degradedReason ?? "", /model registry unavailable/);
		assert.equal(oversized.degradedReason, "input exceeds router maxInputChars: 12001 > 12000");
	});
});
