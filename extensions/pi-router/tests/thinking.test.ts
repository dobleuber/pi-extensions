import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
	applyThinkingLevel,
	createThinkingMetadata,
	selectThinkingLevel,
	thinkingCliArgs,
	thinkingRpcCommand,
} from "../src/thinking.ts";

describe("thinking-level routing", () => {
	it("selects low, medium, and high from deterministic prompt policy", () => {
		assert.deepEqual(selectThinkingLevel("hola, dime la hora"), {
			level: "low",
			reason: "simple low-risk prompt",
		});
		assert.deepEqual(selectThinkingLevel("actualiza el README y corre los tests"), {
			level: "medium",
			reason: "routine coding or documentation task",
		});
		assert.deepEqual(selectThinkingLevel("refactoriza multiples modulos y borra lo obsoleto"), {
			level: "high",
			reason: "complex, risky, or destructive task",
		});
	});

	it("uses medium for uncertain prompts and clamps unsafe model suggestions", () => {
		assert.equal(selectThinkingLevel("haz eso").level, "medium");
		assert.deepEqual(selectThinkingLevel("elimina la carpeta build", "low"), {
			level: "high",
			reason: "complex, risky, or destructive task",
		});
		assert.deepEqual(selectThinkingLevel("explica brevemente que es git", "high"), {
			level: "low",
			reason: "simple low-risk prompt",
		});
	});

	it("applies thinking through Pi runtime API and exposes CLI/RPC forms", () => {
		const calls: string[] = [];
		const effective = applyThinkingLevel({
			setThinkingLevel(level: string) { calls.push(level); },
			getThinkingLevel() { return "medium"; },
		}, "high");

		assert.deepEqual(calls, ["high"]);
		assert.equal(effective, "medium");
		assert.deepEqual(thinkingCliArgs("low"), ["--thinking", "low"]);
		assert.deepEqual(thinkingRpcCommand("high"), { type: "set_thinking_level", level: "high" });
	});

	it("records requested and effective thinking levels for diagnostics", () => {
		assert.deepEqual(createThinkingMetadata("high", "medium", "model clamped level"), {
			requestedThinkingLevel: "high",
			effectiveThinkingLevel: "medium",
			thinkingReason: "model clamped level",
		});
	});
});
