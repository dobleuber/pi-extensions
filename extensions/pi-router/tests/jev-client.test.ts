import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
	DEFAULT_JEV_CONFIG,
	buildJevInputRequest,
	buildJevResponseRequest,
	createJevDecisionClient,
	type JevSystemOneResult,
} from "../src/jev.ts";

describe("Jev decision client", () => {
	it("builds one bounded input request with profile, translation, and language questions", () => {
		const request = buildJevInputRequest(
			{
				prompt: "mejora el router",
				conversationSummary: "The previous task added profile directives.",
			},
			DEFAULT_JEV_CONFIG,
		);

		assert.equal(request.model, "jev-1.13.0");
		assert.deepEqual(request.state, {
			task: "mejora el router",
			conversationSummary: "The previous task added profile directives.",
		});
		assert.deepEqual(Object.keys(request.questions), ["profile", "inputTranslation", "sourceLanguage"]);
		assert.deepEqual(Object.keys(request.questions.profile.criteria), ["luna", "sol", "astra"]);
		const costCapped = buildJevInputRequest({ prompt: "routine" }, { ...DEFAULT_JEV_CONFIG, maxProfileCostTier: 1 });
		assert.deepEqual(Object.keys(costCapped.questions.profile.criteria), ["luna"]);
		assert.deepEqual(Object.keys(request.questions.inputTranslation.criteria), ["required", "not_required", "uncertain"]);
	});

	it("builds a bounded response-only translation request", () => {
		const request = buildJevResponseRequest("La respuesta ya está en español.", DEFAULT_JEV_CONFIG);
		assert.deepEqual(request.state, { response: "La respuesta ya está en español." });
		assert.deepEqual(Object.keys(request.questions), ["responseTranslation"]);
		assert.deepEqual(Object.keys(request.questions.responseTranslation.criteria), ["required", "not_required", "uncertain"]);
	});

	it("normalizes a valid input decision and maps the selected profile", async () => {
		const result: JevSystemOneResult = {
			model: "jev-1.13",
			usage: { input_tokens: 42, output_tokens: 0 },
			answers: {
				profile: { type: "choice", choice: "sol", confidence: 0.91, probabilities: { sol: 0.91, luna: 0.04, astra: 0.05 } },
				inputTranslation: { type: "choice", choice: "required", confidence: 0.99, probabilities: { required: 0.99, not_required: 0.01, uncertain: 0 } },
				sourceLanguage: { type: "choice", choice: "es", confidence: 0.99, probabilities: { en: 0, es: 0.99, mixed: 0.01, other: 0 } },
			},
		};
		const client = createJevDecisionClient({ ...DEFAULT_JEV_CONFIG }, {
			systemOne: async () => result,
		});

		const decision = await client.decideInput({ prompt: "mejora el router" });
		assert.equal(decision.profile?.id, "sol");
		assert.equal(decision.profile?.source, "automatic");
		assert.equal(decision.inputTranslation, "required");
		assert.equal(decision.sourceLanguage, "es");
		assert.equal(decision.model, "jev-1.13");
		assert.equal(decision.usage.input_tokens, 42);
		assert.equal(typeof decision.metadata.durationMs, "number");
		assert.ok((decision.metadata.durationMs ?? -1) >= 0);
	});

	it("rejects a disabled Terra decision", async () => {
		const client = createJevDecisionClient(DEFAULT_JEV_CONFIG, {
			systemOne: async () => ({
				model: "jev-1.13.0", usage: { input_tokens: 10, output_tokens: 1 },
				answers: {
					profile: { type: "choice", choice: "terra", confidence: 0.9, probabilities: { luna: 0.05, terra: 0.9, sol: 0.03, astra: 0.02 } },
					inputTranslation: { type: "choice", choice: "required", confidence: 1, probabilities: { required: 1, not_required: 0, uncertain: 0 } },
					sourceLanguage: { type: "choice", choice: "es", confidence: 1, probabilities: { en: 0, es: 1, mixed: 0, other: 0 } },
				},
			}),
		});
		await assert.rejects(() => client.decideInput({ prompt: "Migra esta integración." }), /invalid Jev choice answer: profile/);
	});

	it("accepts an input bypass only for a sufficiently certain not-required result", async () => {
		const result: JevSystemOneResult = {
			model: "jev-1.13",
			usage: { input_tokens: 12, output_tokens: 0 },
			answers: {
				profile: { type: "choice", choice: "luna", confidence: 0.88, probabilities: { sol: 0.08, luna: 0.88, astra: 0.04 } },
				inputTranslation: { type: "choice", choice: "not_required", confidence: 0.9, probabilities: { required: 0.04, not_required: 0.9, uncertain: 0.06 } },
				sourceLanguage: { type: "choice", choice: "en", confidence: 0.95, probabilities: { en: 0.95, es: 0.02, mixed: 0.02, other: 0.01 } },
			},
		};
		const client = createJevDecisionClient({ ...DEFAULT_JEV_CONFIG, translationMinConfidence: 0.8 }, {
			systemOne: async () => result,
		});

		const decision = await client.decideInput({ prompt: "inspect the router" });
		assert.equal(decision.inputTranslation, "not_required");
		assert.equal(decision.canBypassInputTranslation, true);
	});

	it("does not bypass when an otherwise negative translation choice conflicts with a non-English source label", async () => {
		const client = createJevDecisionClient({ ...DEFAULT_JEV_CONFIG }, {
			systemOne: async () => ({
				model: "jev-1.13",
				usage: { input_tokens: 1, output_tokens: 0 },
				answers: {
					profile: { type: "choice", choice: "luna", confidence: 0.9, probabilities: { sol: 0.05, luna: 0.9, astra: 0.05 } },
					inputTranslation: { type: "choice", choice: "not_required", confidence: 0.99, probabilities: { required: 0, not_required: 0.99, uncertain: 0.01 } },
					sourceLanguage: { type: "choice", choice: "es", confidence: 0.99, probabilities: { en: 0, es: 0.99, mixed: 0.01, other: 0 } },
				},
			}),
		});
		const decision = await client.decideInput({ prompt: "instrucción" });
		assert.equal(decision.inputTranslation, "not_required");
		assert.equal(decision.canBypassInputTranslation, false);
	});

	it("uses uncertainty when the translation choice does not meet the threshold", async () => {
		const result: JevSystemOneResult = {
			model: "jev-1.13",
			usage: { input_tokens: 12, output_tokens: 0 },
			answers: {
				profile: { type: "choice", choice: "luna", confidence: 0.4, probabilities: { sol: 0.35, luna: 0.4, astra: 0.25 } },
				inputTranslation: { type: "choice", choice: "not_required", confidence: 0.4, probabilities: { required: 0.3, not_required: 0.4, uncertain: 0.3 } },
				sourceLanguage: { type: "choice", choice: "en", confidence: 0.4, probabilities: { en: 0.4, es: 0.3, mixed: 0.2, other: 0.1 } },
			},
		};
		const client = createJevDecisionClient({ ...DEFAULT_JEV_CONFIG, translationMinConfidence: 0.8, profileMinConfidence: 0.8 }, {
			systemOne: async () => result,
		});

		const decision = await client.decideInput({ prompt: "follow up" });
		assert.equal(decision.profile, undefined);
		assert.equal(decision.inputTranslation, "uncertain");
		assert.equal(decision.canBypassInputTranslation, false);
	});

	it("uses the same response decision shape for the final-answer check", async () => {
		const result: JevSystemOneResult = {
			model: "jev-1.13",
			usage: { input_tokens: 21, output_tokens: 0 },
			answers: {
				responseTranslation: { type: "choice", choice: "not_required", confidence: 0.97, probabilities: { required: 0.01, not_required: 0.97, uncertain: 0.02 } },
			},
		};
		const client = createJevDecisionClient({ ...DEFAULT_JEV_CONFIG }, {
			systemOne: async () => result,
		});

		const decision = await client.decideResponse("Ya está listo.");
		assert.equal(decision.translation, "not_required");
		assert.equal(decision.canBypass, true);
	});

	it("rejects malformed choices and probabilities instead of guessing", async () => {
		const client = createJevDecisionClient({ ...DEFAULT_JEV_CONFIG }, {
			systemOne: async () => ({
				model: "jev-1.13",
				usage: { input_tokens: 1, output_tokens: 0 },
				answers: {
					profile: { type: "choice", choice: "unknown", confidence: 0.99, probabilities: { unknown: 0.99 } },
					inputTranslation: { type: "choice", choice: "required", confidence: 0.99, probabilities: { required: 1.2 } },
					sourceLanguage: { type: "choice", choice: "en", confidence: 0.99, probabilities: { en: 1 } },
				},
			}),
		});

		await assert.rejects(() => client.decideInput({ prompt: "bad response" }), /invalid Jev choice answer: profile/);
	});

	it("rejects oversize bounded state before making a transport request", () => {
		assert.throws(() => buildJevInputRequest({ prompt: "a very long task" }, { ...DEFAULT_JEV_CONFIG, maxStateChars: 5 }), /state exceeds configured limit/);
		assert.throws(() => buildJevResponseRequest("a very long response", { ...DEFAULT_JEV_CONFIG, maxStateChars: 5 }), /state exceeds configured limit/);
	});

	it("enforces a bounded deadline and aborts the underlying transport", async () => {
		let requestSignal: AbortSignal | undefined;
		const client = createJevDecisionClient({ ...DEFAULT_JEV_CONFIG, timeoutMs: 15 }, {
			systemOne: async (_request, options) => {
				requestSignal = options?.signal;
				return await new Promise<JevSystemOneResult>(() => {});
			},
		});

		await assert.rejects(() => client.decideResponse("slow response"), /timed out after 15ms/);
		assert.equal(requestSignal?.aborted, true);
	});

	it("accepts distributions for exactly the cost-capped candidate set", async () => {
		for (const maxProfileCostTier of [1, 2] as const) {
			const client = createJevDecisionClient({ ...DEFAULT_JEV_CONFIG, maxProfileCostTier }, {
				systemOne: async () => ({
					model: "jev-1.13", usage: { input_tokens: 1, output_tokens: 0 },
					answers: {
						profile: { type: "choice", choice: "luna", confidence: 1, probabilities: Object.fromEntries(maxProfileCostTier === 1 ? [["luna", 1]] : [["luna", 1], ["sol", 0]]) },
						inputTranslation: { type: "choice", choice: "required", confidence: 1, probabilities: { required: 1, not_required: 0, uncertain: 0 } },
						sourceLanguage: { type: "choice", choice: "es", confidence: 1, probabilities: { en: 0, es: 1, mixed: 0, other: 0 } },
					},
				}),
			});
			assert.equal((await client.decideInput({ prompt: "hola" })).profileKey, "luna");
		}
	});

	it("does not start transport when cancelled before its scheduled dispatch", async () => {
		let calls = 0;
		const controller = new AbortController();
		const client = createJevDecisionClient(DEFAULT_JEV_CONFIG, {
			systemOne: async () => { calls++; throw new Error("must not dispatch"); },
		});
		const pending = client.decideResponse("cancel", { signal: controller.signal });
		controller.abort();
		await assert.rejects(pending, /aborted/);
		assert.equal(calls, 0);
	});

	it("propagates caller cancellation without waiting for the transport", async () => {
		const controller = new AbortController();
		const client = createJevDecisionClient({ ...DEFAULT_JEV_CONFIG, timeoutMs: 1000 }, {
			systemOne: async () => await new Promise<JevSystemOneResult>(() => {}),
		});
		const pending = client.decideResponse("cancel me", { signal: controller.signal });
		controller.abort();
		await assert.rejects(() => pending, /Jev request aborted/);
	});
});
