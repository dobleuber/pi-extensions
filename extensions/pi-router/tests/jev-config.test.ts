import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { DEFAULT_ROUTER_CONFIG, resolveJevConfig } from "../src/config.ts";

describe("Jev router configuration", () => {
	it("has operational settings without activation or compatibility flags", () => {
		assert.deepEqual(DEFAULT_ROUTER_CONFIG.jev, {
			model: "jev-1.13.0", timeoutMs: 1000, maxStateChars: 12000,
			profileMinConfidence: 0.7, translationMinConfidence: 0.85, maxProfileCostTier: 3,
		});
	});
	it("fills missing operational settings from defaults", () => {
		assert.equal(resolveJevConfig(undefined).model, "jev-1.13.0");
		assert.equal(resolveJevConfig({ timeoutMs: 500 }).timeoutMs, 500);
		assert.equal(resolveJevConfig({ timeoutMs: 0 }).timeoutMs, 1000);
	});
});
