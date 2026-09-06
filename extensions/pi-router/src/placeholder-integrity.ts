type PlaceholderKind = "INLINE" | "PROTECTED" | "PRESERVED_BLOCK";

/** Return a diagnostic when a translation changes a protected literal token. */
export function validatePlaceholderIntegrity(input: string, output: string): string | null {
	const malformed = output.match(/§P\d+§\d+__|_{0,2}PI_ROUTER_(?:INLINE|EN_LINEA|PRESERV(?:ED|ADO)_BLOCK)_\d+__\d+__/i)?.[0];
	if (malformed) return `malformed placeholder: ${malformed}`;
	const expected = placeholderMultiset(input);
	const actual = placeholderMultiset(output);
	if (expected.size === actual.size && [...expected].every(([key, count]) => actual.get(key) === count)) {
		return null;
	}
	return `placeholder mismatch: expected ${formatMultiset(expected)}, got ${formatMultiset(actual)}`;
}

function placeholderMultiset(text: string): Map<string, number> {
	const placeholders = new Map<string, number>();
	const add = (kind: PlaceholderKind, index: string) => {
		const key = `${kind}_${index}`;
		placeholders.set(key, (placeholders.get(key) ?? 0) + 1);
	};
	for (const match of text.matchAll(/§P(\d+)§/g)) add("PROTECTED", match[1]);
	for (const match of text.matchAll(/_{0,2}PI_ROUTER_(?:INLINE|EN_LINEA)_(\d+)_{0,2}(?:\d+_{2})?/gi)) add("INLINE", match[1]);
	for (const match of text.matchAll(/_{0,2}PI_ROUTER_PRESERV(?:ED|ADO)_BLOCK_(\d+)_{0,2}/gi)) add("PRESERVED_BLOCK", match[1]);
	return placeholders;
}

function formatMultiset(placeholders: Map<string, number>): string {
	return `[${[...placeholders.entries()].map(([key, count]) => `${key}x${count}`).join(", ")}]`;
}
