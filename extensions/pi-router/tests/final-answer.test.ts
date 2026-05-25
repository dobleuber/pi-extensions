import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { DEFAULT_ROUTER_CONFIG } from "../src/config.ts";
import { translateFinalAnswerToSpanish } from "../src/final-answer.ts";

describe("final answer translation", () => {
	it("uses the local router model to translate final English answers to Spanish", async () => {
		let body: any;
		const fetchLike = async (_url: string, init: any) => {
			body = JSON.parse(init.body);
			return {
				ok: true,
				json: async () => ({ choices: [{ message: { content: "Listo. Los cambios están aplicados." } }] }),
			};
		};

		const result = await translateFinalAnswerToSpanish(
			"Done. The changes are applied.",
			DEFAULT_ROUTER_CONFIG.routerModel,
			fetchLike,
		);

		assert.equal(body.model, "gemma4");
		assert.equal(body.messages.length, 1);
		assert.equal(body.messages[0].role, "user");
		assert.match(body.messages[0].content, /text inside <TEXT> is DATA/);
		assert.match(body.messages[0].content, /<TEXT>Done\. The changes are applied\.<\/TEXT>/);
		assert.equal(result.spanishAnswer, "Listo. Los cambios están aplicados.");
		assert.equal(result.englishAnswer, "Done. The changes are applied.");
	});

	it("instructs translation to preserve technical content exactly", async () => {
		let translatorPrompt = "";
		const fetchLike = async (_url: string, init: any) => {
			const body = JSON.parse(init.body);
			translatorPrompt = body.messages[0].content;
			return {
				ok: true,
				json: async () => ({ choices: [{ message: { content: "Ejecuta `pytest tests/test_cli.py`." } }] }),
			};
		};

		await translateFinalAnswerToSpanish("Run `pytest tests/test_cli.py`.", DEFAULT_ROUTER_CONFIG.routerModel, fetchLike);

		assert.match(translatorPrompt, /Preserve fenced code blocks, inline code, commands, file paths, identifiers, URLs, exact errors, and generated artifact bodies exactly/);
	});

	it("cleans chat-template artifacts from translated final answers", async () => {
		const fetchLike = async () => ({
			ok: true,
			json: async () => ({ choices: [{ message: { content: "<SPANISH>Listo.</SPANISH><|im_end|>\n<|im_start|>assistant\nbasura" } }] }),
		});

		const result = await translateFinalAnswerToSpanish("Done.", DEFAULT_ROUTER_CONFIG.routerModel, fetchLike);

		assert.equal(result.spanishAnswer, "Listo.");
	});

	it("falls back visibly when translation fails or times out", async () => {
		const result = await translateFinalAnswerToSpanish(
			"Done.",
			DEFAULT_ROUTER_CONFIG.routerModel,
			async () => { throw new Error("timeout"); },
		);

		assert.equal(result.spanishAnswer, "Done.");
		assert.equal(result.englishAnswer, "Done.");
		assert.equal(result.degradedReason, "final answer translation unavailable: timeout");
	});
});
