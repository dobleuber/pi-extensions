import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { DEFAULT_ROUTER_CONFIG } from "../src/config.ts";
import { createRouterMetadata, routePromptWithModel } from "../src/router-model.ts";

describe("local router model", () => {
	it("calls llama.cpp gemma4 to translate a Spanish prompt into an English work prompt", async () => {
		const calls: Array<{ url: string; body: any }> = [];
		const fetchLike = async (url: string, init: any) => {
			calls.push({ url, body: JSON.parse(init.body) });
			return {
				ok: true,
				json: async () => ({
					choices: [{
						message: {
							content: JSON.stringify({
								sourceLanguage: "es",
								englishPrompt: "Improve the Pi router.",
								thinkingLevel: "medium",
								translateFinalAnswer: true,
							}),
						},
					}],
				}),
			};
		};

		const result = await routePromptWithModel("mejora el router de Pi", DEFAULT_ROUTER_CONFIG.routerModel, fetchLike);

		assert.equal(calls[0].url, "http://127.0.0.1:11434/v1/chat/completions");
		assert.equal(calls[0].body.model, "gemma4");
		assert.equal(calls[0].body.messages.length, 1);
		assert.equal(calls[0].body.messages[0].role, "user");
		assert.match(calls[0].body.messages[0].content, /<TASK>mejora el router de Pi<\/TASK>/);
		assert.equal(result.englishPrompt, "Improve the Pi router.");
		assert.equal(result.sourceLanguage, "es");
		assert.equal(result.thinkingLevel, "medium");
		assert.equal(result.translateFinalAnswer, true);
	});

	it("sends conversation context only for faithful reference resolution", async () => {
		let body: any;
		const fetchLike = async (_url: string, init: any) => {
			body = JSON.parse(init.body);
			return {
				ok: true,
				json: async () => ({
					choices: [{
						message: {
							content: JSON.stringify({
								sourceLanguage: "es",
								englishPrompt: "Add the router details toggle to the Pi router.",
								thinkingLevel: "medium",
								translateFinalAnswer: true,
								usedConversationContext: true,
								resolvedReferences: ["eso = router details toggle"],
								unresolvedReferences: [],
							}),
						},
					}],
				}),
			};
		};

		const result = await routePromptWithModel(
			"agrega eso al router de Pi",
			DEFAULT_ROUTER_CONFIG.routerModel,
			fetchLike,
			{ conversationSummary: "The current topic is adding a router details toggle." },
		);

		assert.equal(body.messages.length, 1);
		assert.match(body.messages[0].content, /Use conversation context only to resolve references/);
		assert.match(body.messages[0].content, /Conversation context for reference resolution only:\nThe current topic is adding a router details toggle\./);
		assert.match(body.messages[0].content, /<TASK>agrega eso al router de Pi<\/TASK>/);
		assert.equal(result.usedConversationContext, true);
		assert.deepEqual(result.resolvedReferences, ["eso = router details toggle"]);
		assert.deepEqual(result.unresolvedReferences, []);
	});

	it("records unresolved references without inventing intent", async () => {
		const fetchLike = async () => ({
			ok: true,
			json: async () => ({
				choices: [{
					message: {
						content: JSON.stringify({
							sourceLanguage: "es",
							englishPrompt: "Continue with that.",
							thinkingLevel: "medium",
							translateFinalAnswer: true,
							usedConversationContext: false,
							resolvedReferences: [],
							unresolvedReferences: ["eso"],
						}),
					},
				}],
			}),
		});

		const result = await routePromptWithModel("continua con eso", DEFAULT_ROUTER_CONFIG.routerModel, fetchLike);

		assert.deepEqual(result.unresolvedReferences, ["eso"]);
		const metadata = createRouterMetadata({
			originalPrompt: "continua con eso",
			result,
			routerModel: DEFAULT_ROUTER_CONFIG.routerModel,
		});
		assert.deepEqual(metadata.unresolvedReferences, ["eso"]);
	});

	it("instructs the router model to preserve technical tokens", async () => {
		let routerPrompt = "";
		const fetchLike = async (_url: string, init: any) => {
			const body = JSON.parse(init.body);
			routerPrompt = body.messages[0].content;
			return {
				ok: true,
				json: async () => ({
					choices: [{ message: { content: '{"translation":"Run `pytest tests/test_cli.py`.","sourceLanguage":"es","thinkingLevel":"low","translateFinalAnswer":true}' } }],
				}),
			};
		};

		await routePromptWithModel("corre `pytest tests/test_cli.py`", DEFAULT_ROUTER_CONFIG.routerModel, fetchLike);

		assert.match(routerPrompt, /Preserve commands, paths, identifiers, quoted strings, and error messages/);
	});

	it("parses the first valid JSON object and ignores repeated trailing text", async () => {
		const fetchLike = async () => ({
			ok: true,
			json: async () => ({
				choices: [{ message: { content: '{"translation":"Give the current status of the router","sourceLanguage":"es","thinkingLevel":"medium","translateFinalAnswer":true}\n</TASK>\n{"translation":"repeated"}' } }],
			}),
		});

		const result = await routePromptWithModel("Dame el estado actual del router", DEFAULT_ROUTER_CONFIG.routerModel, fetchLike);

		assert.equal(result.englishPrompt, "Give the current status of the router");
		assert.equal(result.sourceLanguage, "es");
		assert.equal(result.translateFinalAnswer, true);
	});

	it("creates metadata for logs and details inspection", () => {
		const metadata = createRouterMetadata({
			originalPrompt: "mejora el router",
			result: {
				sourceLanguage: "es",
				englishPrompt: "Improve the router.",
				thinkingLevel: "medium",
				translateFinalAnswer: true,
				degradedReason: "fallback",
			},
			routerModel: DEFAULT_ROUTER_CONFIG.routerModel,
		});

		assert.deepEqual(metadata, {
			originalPrompt: "mejora el router",
			transformedPrompt: "Improve the router.",
			sourceLanguage: "es",
			routerModel: "llama-cpp/gemma4",
			requestedThinkingLevel: "medium",
			fallback: "fallback",
		});
	});

	it("passes an abort signal to bound router model calls", async () => {
		let signal: AbortSignal | undefined;
		const fetchLike = async (_url: string, init: any) => {
			signal = init.signal;
			return {
				ok: true,
				json: async () => ({
					choices: [{ message: { content: '{"englishPrompt":"Hello","sourceLanguage":"en","thinkingLevel":"low","translateFinalAnswer":true}' } }],
				}),
			};
		};

		await routePromptWithModel("hello", DEFAULT_ROUTER_CONFIG.routerModel, fetchLike);

		assert.ok(signal instanceof AbortSignal);
	});

	it("falls back to passthrough when the router model is unavailable or input is oversized", async () => {
		const unavailable = await routePromptWithModel(
			"hola",
			DEFAULT_ROUTER_CONFIG.routerModel,
			async () => { throw new Error("connection refused"); },
		);
		const oversized = await routePromptWithModel(
			"x".repeat(DEFAULT_ROUTER_CONFIG.routerModel.maxInputChars + 1),
			DEFAULT_ROUTER_CONFIG.routerModel,
			async () => { throw new Error("should not be called"); },
		);

		assert.equal(unavailable.englishPrompt, "hola");
		assert.equal(unavailable.degradedReason, "router model unavailable: connection refused");
		assert.equal(oversized.degradedReason, "input exceeds router maxInputChars: 12001 > 12000");
	});
});
