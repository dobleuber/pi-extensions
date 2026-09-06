import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { DEFAULT_ROUTER_CONFIG } from "../src/config.ts";
import type { PiAiRuntime } from "../src/pi-ai-client.ts";
import { translateFinalAnswerToSpanish } from "../src/final-answer.ts";

const TEST_ROUTER_CONFIG = {
	...DEFAULT_ROUTER_CONFIG.routerModel,
	provider: "test-router",
	model: "test-mini",
};

function runtimeFor(content: string, capture?: { model?: any; context?: any; options?: any }, sourceLanguage = "en"): PiAiRuntime {
	return {
		modelRegistry: {
			find(provider, model) {
				const resolved = { provider, id: model, api: "test-api" };
				if (capture) capture.model = resolved;
				return resolved as any;
			},
			async getApiKeyAndHeaders() {
				return { ok: true, apiKey: "test-token" };
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
				content: [{ type: "text", text: JSON.stringify({ sourceLanguage, translation: content }) }],
				timestamp: Date.now(),
			} as any;
		}) as any,
	};
}

describe("remote final-answer translation", () => {
	it("does not silently accept the recorded mixed-language stress response as Spanish", async () => {
		const answer = readFileSync(new URL("./fixtures/router-stress-answer.md", import.meta.url), "utf8");
		let calls = 0;
		const runtime = runtimeFor("");
		runtime.complete = (async () => { calls += 1; throw new Error("test translator offline"); }) as any;

		const result = await translateFinalAnswerToSpanish(answer, TEST_ROUTER_CONFIG, runtime);
		assert.ok(calls > 0);
		assert.match(result.degradedReason ?? "", /test translator offline/);
	});

	it("dispatches default final translation to Luna without reasoning", async () => {
		const capture: any = {};
		const result = await translateFinalAnswerToSpanish(
			"Done. The changes are applied.",
			DEFAULT_ROUTER_CONFIG.routerModel,
			runtimeFor("Listo. Los cambios están aplicados.", capture),
		);

		assert.equal(capture.model.provider, "openai-codex");
		assert.equal(capture.model.id, "gpt-5.6-luna");
		assert.equal(capture.options.reasoningEffort, "none");
		assert.equal(result.spanishAnswer, "Listo. Los cambios están aplicados.");
		assert.equal(result.degradedReason, undefined);
	});

	it("resolves the remote router model and auth through Pi for English answers", async () => {
		const capture: any = {};
		const result = await translateFinalAnswerToSpanish(
			"Done. The changes are applied.",
			TEST_ROUTER_CONFIG,
			runtimeFor("Listo. Los cambios están aplicados.", capture),
		);

		assert.deepEqual(capture.model, { provider: "test-router", id: "test-mini", api: "test-api" });
		assert.equal(capture.options.apiKey, "test-token");
		assert.match(capture.context.messages[0].content[0].text, /BEGIN_PI_ROUTER_TRANSLATION_TEXT/);
		assert.match(capture.context.messages[0].content[0].text, /Done\. The changes are applied\./);
		assert.equal(result.spanishAnswer, "Listo. Los cambios están aplicados.");
		assert.equal(result.englishAnswer, "Done. The changes are applied.");
	});

	it("preserves technical content while translating prose", async () => {
		let context: any;
		const runtime = runtimeFor("Ejecuta __PI_ROUTER_INLINE_0__.");
		const originalComplete = runtime.complete!;
		runtime.complete = (async (model: any, value: any, options: any) => {
			context = value;
			return originalComplete(model, value, options);
		}) as any;

		const result = await translateFinalAnswerToSpanish("Run `pytest tests/test_cli.py`.", TEST_ROUTER_CONFIG, runtime);

		assert.doesNotMatch(context.messages[0].content[0].text, /pytest tests\/test_cli\.py/);
		assert.match(context.messages[0].content[0].text, /__PI_ROUTER_INLINE_0__/);
		assert.equal(result.spanishAnswer, "Ejecuta `pytest tests/test_cli.py`.");
	});

	it("preserves relative directory paths and trailing punctuation in final answers", async () => {
		let context: any;
		const runtime = runtimeFor("Revisa §P0§.");
		const originalComplete = runtime.complete!;
		runtime.complete = (async (model: any, value: any, options: any) => {
			context = value;
			return originalComplete(model, value, options);
		}) as any;

		const result = await translateFinalAnswerToSpanish("Review extensions/pi-router.", TEST_ROUTER_CONFIG, runtime);

		assert.doesNotMatch(context.messages[0].content[0].text, /extensions\/pi-router/);
		assert.match(context.messages[0].content[0].text, /§P0§/);
		assert.equal(result.spanishAnswer, "Revisa extensions/pi-router.");
	});

	it("cleans chat-template artifacts and echoed translation delimiters", async () => {
		const result = await translateFinalAnswerToSpanish(
			"Done.",
			TEST_ROUTER_CONFIG,
			runtimeFor("---BEGIN_PI_ROUTER_TRANSLATION_TEXT---\nListo.\n---END_PI_ROUTER_TRANSLATION_TEXT---<|im_end|>\n<|im_start|>assistant\nbasura"),
		);
		assert.equal(result.spanishAnswer, "Listo.");
	});

	it("accepts unchanged Spanish after checking the actual prose with the model", async () => {
		const answer = "Encontré la causa de las advertencias. Los cambios recientes no rompieron la traducción.";
		const capture: any = {};
		const result = await translateFinalAnswerToSpanish(answer, TEST_ROUTER_CONFIG, runtimeFor(answer, capture, "es"));

		assert.ok(capture.context);
		assert.equal(result.spanishAnswer, answer);
		assert.equal(result.degradedReason, undefined);
	});

	it("translates English even when the same paragraph contains Spanish", async () => {
		const answer = "The router is ready. La traducción conserva rutas y comandos.";
		const spanish = "El router está listo. La traducción conserva rutas y comandos.";
		const capture: any = {};
		const result = await translateFinalAnswerToSpanish(answer, TEST_ROUTER_CONFIG, runtimeFor(spanish, capture, "mixed"));

		assert.ok(capture.context);
		assert.equal(result.spanishAnswer, spanish);
		assert.equal(result.degradedReason, undefined);
	});

	it("does not use Spanish in fenced code to skip English prose", async () => {
		const code = '```js\nconst label = "La traducción conserva rutas y comandos.";\n```';
		const capture: any = {};
		const result = await translateFinalAnswerToSpanish(`The router is ready.\n\n${code}`, TEST_ROUTER_CONFIG, runtimeFor("El router está listo.", capture));

		assert.doesNotMatch(capture.context.messages[0].content[0].text, /La traducción/);
		assert.equal(result.spanishAnswer, `El router está listo.\n\n${code}`);
		assert.equal(result.degradedReason, undefined);
	});

	it("does not use Spanish in inline code to skip English prose", async () => {
		const answer = "Review `La traducción conserva rutas y comandos.` before deployment.";
		const result = await translateFinalAnswerToSpanish(answer, TEST_ROUTER_CONFIG, runtimeFor("Revisa __PI_ROUTER_INLINE_0__ antes del despliegue."));

		assert.equal(result.spanishAnswer, "Revisa `La traducción conserva rutas y comandos.` antes del despliegue.");
		assert.equal(result.degradedReason, undefined);
	});

	it("accepts unchanged short Spanish without an untranslated-output warning", async () => {
		const answer = "Sí, aquí estoy. ¿Qué quieres probar?";
		const result = await translateFinalAnswerToSpanish(answer, TEST_ROUTER_CONFIG, runtimeFor(answer, undefined, "es"));
		assert.equal(result.spanishAnswer, answer);
		assert.equal(result.degradedReason, undefined);
	});

	it("accepts language-neutral headings without changing technical labels", async () => {
		const result = await translateFinalAnswerToSpanish("### TypeScript", TEST_ROUTER_CONFIG, runtimeFor("### TypeScript", undefined, "none"));
		assert.equal(result.spanishAnswer, "### TypeScript");
		assert.equal(result.degradedReason, undefined);
	});

	it("still rejects unchanged mixed-language prose", async () => {
		const answer = "The router is ready. La traducción conserva rutas y comandos.";
		const result = await translateFinalAnswerToSpanish(answer, TEST_ROUTER_CONFIG, runtimeFor(answer, undefined, "mixed"));
		assert.equal(result.spanishAnswer, answer);
		assert.match(result.degradedReason ?? "", /untranslated output/);
	});

	it("rejects invalid translation metadata instead of guessing the language", async () => {
		const result = await translateFinalAnswerToSpanish("Done.", TEST_ROUTER_CONFIG, runtimeFor("Listo.", undefined, "invalid"));
		assert.equal(result.spanishAnswer, "Done.");
		assert.match(result.degradedReason ?? "", /invalid translation payload/);
	});

	it("restores literal inline placeholder examples without recursively expanding them", async () => {
		const answer = "Preserve `__PI_ROUTER_INLINE_1__` and `settings.json`.";
		const result = await translateFinalAnswerToSpanish(answer, TEST_ROUTER_CONFIG, runtimeFor("Conserva __PI_ROUTER_INLINE_0__ y __PI_ROUTER_INLINE_2__."));
		assert.equal(result.spanishAnswer, "Conserva `__PI_ROUTER_INLINE_1__` y `settings.json`.");
		assert.equal(result.degradedReason, undefined);
	});

	it("does not allocate inline mask IDs already used by bare literal tokens", async () => {
		const answer = "Run `foo` and preserve __PI_ROUTER_INLINE_0__.";
		const result = await translateFinalAnswerToSpanish(answer, TEST_ROUTER_CONFIG,
			runtimeFor("Ejecuta __PI_ROUTER_INLINE_1__ y conserva __PI_ROUTER_INLINE_0__."));
		assert.equal(result.spanishAnswer, "Ejecuta `foo` y conserva __PI_ROUTER_INLINE_0__.");
		assert.equal(result.degradedReason, undefined);
	});

	it("preserves bare path tokens alongside masked URLs", async () => {
		const answer = "Review https://example.com and preserve §P0§.";
		const result = await translateFinalAnswerToSpanish(answer, TEST_ROUTER_CONFIG,
			runtimeFor("Revisa §P1§ y conserva §P0§."));
		assert.equal(result.spanishAnswer, "Revisa https://example.com y conserva §P0§.");
		assert.equal(result.degradedReason, undefined);
	});

	it("does not allocate fenced-code mask IDs already used by literal tokens", async () => {
		const code = "```ts\nconst x = 1;\n```";
		const answer = `Done.\n\n__PI_ROUTER_PRESERVED_BLOCK_0__\n\n${code}`;
		const result = await translateFinalAnswerToSpanish(answer, TEST_ROUTER_CONFIG, runtimeFor("Listo."));
		assert.equal(result.spanishAnswer, `Listo.\n\n__PI_ROUTER_PRESERVED_BLOCK_0__\n\n${code}`);
		assert.equal(result.degradedReason, undefined);
	});

	it("rejects translation payloads with unexpected fields", async () => {
		const runtime = runtimeFor("");
		runtime.complete = (async () => ({
			role: "assistant", stopReason: "stop", timestamp: Date.now(),
			content: [{ type: "text", text: JSON.stringify({ sourceLanguage: "es", translation: "Sí.", extra: true }) }],
		})) as any;
		const result = await translateFinalAnswerToSpanish("Sí.", TEST_ROUTER_CONFIG, runtime);
		assert.equal(result.spanishAnswer, "Sí.");
		assert.match(result.degradedReason ?? "", /invalid translation payload/);
	});

	it("falls back visibly when translation is unchanged or unavailable", async () => {
		const unchanged = await translateFinalAnswerToSpanish("Done. The changes are applied.", TEST_ROUTER_CONFIG, runtimeFor("Done. The changes are applied."));
		const unavailable = await translateFinalAnswerToSpanish("Done.", TEST_ROUTER_CONFIG);

		assert.equal(unchanged.spanishAnswer, "Done. The changes are applied.");
		assert.match(unchanged.degradedReason ?? "", /untranslated output/);
		assert.equal(unavailable.spanishAnswer, "Done.");
		assert.match(unavailable.degradedReason ?? "", /model registry unavailable/);
	});
});
