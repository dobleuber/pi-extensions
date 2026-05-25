import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
	DEFAULT_ROUTER_CONFIG,
	resolveRouterState,
	routerStatusSummary,
	type WorkModelInfo,
} from "../src/config.ts";

describe("router configuration", () => {
	it("defaults to disabled routing with local gemma4 as the router model", () => {
		assert.equal(DEFAULT_ROUTER_CONFIG.state, "off");
		assert.equal(DEFAULT_ROUTER_CONFIG.routerModel.provider, "llama-cpp");
		assert.equal(DEFAULT_ROUTER_CONFIG.routerModel.model, "gemma4");
		assert.equal(DEFAULT_ROUTER_CONFIG.routerModel.baseUrl, "http://127.0.0.1:11434/v1");
		assert.equal(DEFAULT_ROUTER_CONFIG.routerModel.timeoutMs, 5000);
		assert.equal(DEFAULT_ROUTER_CONFIG.routerModel.fallbackMode, "passthrough-with-warning");
		assert.equal(DEFAULT_ROUTER_CONFIG.routerModel.maxInputChars, 12000);
	});

	it("resolves global, session, and single-prompt overrides", () => {
		assert.deepEqual(resolveRouterState({ state: "off" }, { sessionState: "on" }), {
			state: "on",
			reason: "session override",
		});
		assert.deepEqual(resolveRouterState({ state: "on" }, { sessionState: "off" }), {
			state: "off",
			reason: "session override",
		});
		assert.deepEqual(resolveRouterState({ state: "on" }, { singlePromptBypass: true }), {
			state: "off",
			reason: "single prompt bypass",
		});
	});

	it("builds a compact status summary with router and work-model details", () => {
		const workModel: WorkModelInfo = { provider: "stratus", model: "stratus-code" };
		const summary = routerStatusSummary({
			config: { ...DEFAULT_ROUTER_CONFIG, state: "on" },
			workModel,
			degradedReason: "router timeout",
		});

		assert.equal(summary, "router:on routerModel:llama-cpp/gemma4 workModel:stratus/stratus-code degraded:router timeout");
	});
});
