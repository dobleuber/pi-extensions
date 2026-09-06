import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { maskProtectedSpans } from "../src/protected-text.ts";

describe("protected literal spans", () => {
	it("allocates around literal placeholder IDs without changing them", () => {
		const mask = maskProtectedSpans("See https://example.com and keep §P0§ and §P2§.");
		assert.equal(mask.text, "See §P1§ and keep §P0§ and §P2§.");
		assert.deepEqual(mask.values, ["https://example.com"]);
		assert.equal(mask.restore(mask.text), "See https://example.com and keep §P0§ and §P2§.");
	});

	it("does not recursively expand placeholder literals inside restored URLs", () => {
		const input = "See https://example.com/§P1§ and https://other.test.";
		const mask = maskProtectedSpans(input);
		assert.equal(mask.restore(mask.text), input);
	});

	it("protects relative directory paths without extensions and restores punctuation", () => {
		const mask = maskProtectedSpans("Review extensions/pi-router, then open src/router-model.");

		assert.equal(mask.values.length, 2);
		assert.equal(mask.values[0], "extensions/pi-router");
		assert.equal(mask.values[1], "src/router-model");
		assert.doesNotMatch(mask.text, /extensions\/pi-router|src\/router-model/);
		assert.equal(mask.restore(`${mask.text} Done.`), "Review extensions/pi-router, then open src/router-model. Done.");
	});

	it("keeps existing URL, hidden-file, and placeholder-shaped protections intact", () => {
		const mask = maskProtectedSpans("See https://example.test/docs, folder/.env.local, and ../config.");

		assert.deepEqual(mask.values, ["https://example.test/docs", "folder/.env.local", "../config"]);
		assert.equal(mask.restore("§P0§ §P1§ §P2§"), "https://example.test/docs folder/.env.local ../config");
	});
});
