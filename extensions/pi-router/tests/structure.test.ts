import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..");

describe("pi-router extension package", () => {
	it("declares an installable Pi extension entrypoint", async () => {
		const packageJson = JSON.parse(await readFile(resolve(root, "package.json"), "utf8"));

		assert.equal(packageJson.name, "pi-router-extension");
		assert.deepEqual(packageJson.pi.extensions, ["./src/index.ts"]);
	});

	it("exports a default extension factory", async () => {
		const source = await readFile(resolve(root, "src/index.ts"), "utf8");

		assert.match(source, /export default function/);
		assert.match(source, /ExtensionAPI/);
	});
});
