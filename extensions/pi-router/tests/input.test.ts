import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { shouldRouteInput } from "../src/input.ts";

describe("input routing guard", () => {
	it("routes normal user prompts", () => {
		assert.equal(shouldRouteInput({ text: "mejora el router de pi", source: "interactive" }), true);
		assert.equal(shouldRouteInput({ text: "please improve the Pi router", source: "rpc" }), true);
	});

	it("skips slash commands and prompt-template invocations", () => {
		for (const text of ["/model", "/opsx:continue", "/template arg", "   /custom-template  "]) {
			assert.equal(shouldRouteInput({ text, source: "interactive" }), false, text);
		}
	});

	it("skips raw shell command syntax and extension-injected messages", () => {
		assert.equal(shouldRouteInput({ text: "!pwd", source: "interactive" }), false);
		assert.equal(shouldRouteInput({ text: "!!rg router", source: "interactive" }), false);
		assert.equal(shouldRouteInput({ text: "hola", source: "extension" }), false);
		assert.equal(shouldRouteInput({ text: "   ", source: "interactive" }), false);
	});
});
