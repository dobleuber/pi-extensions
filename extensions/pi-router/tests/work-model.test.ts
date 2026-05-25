import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { DEFAULT_ROUTER_CONFIG } from "../src/config.ts";
import {
	classifyWorkModelFailure,
	formatWorkModel,
	selectedWorkModelFromPiContext,
} from "../src/work-model.ts";

describe("work-model policy", () => {
	it("keeps router model independent from selected work model", () => {
		const ctx = { model: { provider: "stratus", id: "stratus-code" } };
		const workModel = selectedWorkModelFromPiContext(ctx);

		assert.deepEqual(workModel, { provider: "stratus", model: "stratus-code" });
		assert.equal(DEFAULT_ROUTER_CONFIG.routerModel.provider, "llama-cpp");
		assert.equal(DEFAULT_ROUTER_CONFIG.routerModel.model, "gemma4");
	});

	it("formats default, Stratus, and changed work models without changing router policy", () => {
		assert.equal(formatWorkModel(undefined), "unknown");
		assert.equal(formatWorkModel({ provider: "pi-default" }), "pi-default");
		assert.equal(formatWorkModel({ provider: "stratus", model: "stratus-code" }), "stratus/stratus-code");
		assert.equal(formatWorkModel({ provider: "anthropic", model: "claude-sonnet" }), "anthropic/claude-sonnet");
	});

	it("classifies Stratus/provider failures separately from router failures", () => {
		assert.deepEqual(classifyWorkModelFailure(new Error("Stratus credits exhausted")), {
			type: "work-model",
			message: "Stratus credits exhausted",
		});
		assert.deepEqual(classifyWorkModelFailure(new Error("router model unavailable: connection refused")), {
			type: "router",
			message: "router model unavailable: connection refused",
		});
	});
});
