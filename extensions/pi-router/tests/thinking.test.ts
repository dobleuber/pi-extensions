import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { applyThinkingLevel, thinkingCliArgs, thinkingRpcCommand } from "../src/thinking.ts";

describe("thinking transport helpers", () => {
	it("applies an explicitly supplied level through the Pi runtime", () => {
		const calls: string[] = [];
		const effective = applyThinkingLevel({
			setThinkingLevel(level: string) { calls.push(level); },
			getThinkingLevel() { return "high"; },
		}, "high");

		assert.deepEqual(calls, ["high"]);
		assert.equal(effective, "high");
	});

	it("exposes native CLI and RPC forms without selecting a level", () => {
		assert.deepEqual(thinkingCliArgs("low"), ["--thinking", "low"]);
		assert.deepEqual(thinkingRpcCommand("high"), { type: "set_thinking_level", level: "high" });
	});
});
