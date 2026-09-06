export interface ProtectedTextMask {
	text: string;
	restore(text: string): string;
	values: string[];
}

const PROTECTED_TOKEN_PREFIX = "§P";
const PROTECTED_TOKEN_SUFFIX = "§";
const PROTECTED_SPAN_PATTERN = /https?:\/\/[^\s`'"<>)\]]+|@?(?:\.{1,2}|~|\/?[A-Za-z0-9_.-]+)\/[^\s`'"<>)\]]+/g;
const TRAILING_PUNCTUATION_PATTERN = /[.,;:!?]+$/;

/** Mask paths, URLs, and other literal spans before asking a model to translate. */
export function maskProtectedSpans(text: string): ProtectedTextMask {
	const values: string[] = [];
	const reserved = new Set([...text.matchAll(/§P(\d+)§/g)].map((match) => match[1]));
	const replacements = new Map<string, string>();
	let nextIndex = 0;
	const masked = text.replace(PROTECTED_SPAN_PATTERN, (match) => {
		const trailing = match.match(TRAILING_PUNCTUATION_PATTERN)?.[0] ?? "";
		const value = trailing ? match.slice(0, -trailing.length) : match;
		if (!isPathLikeProtectedSpan(value)) return match;
		while (reserved.has(String(nextIndex))) nextIndex += 1;
		const index = String(nextIndex++);
		const token = `${PROTECTED_TOKEN_PREFIX}${index}${PROTECTED_TOKEN_SUFFIX}`;
		values.push(value);
		replacements.set(index, value);
		return token + trailing;
	});
	return {
		text: masked,
		values,
		restore(output: string): string {
			return output.replace(/§P(\d+)§(?:\d+_{2})?/g,
				(match, index: string) => replacements.get(index) ?? match);
		},
	};
}

function isPathLikeProtectedSpan(value: string): boolean {
	if (/^https?:\/\//.test(value)) return true;
	const normalized = value.startsWith("@") ? value.slice(1) : value;
	if (normalized.startsWith("./") || normalized.startsWith("../") || normalized.startsWith("~/") || normalized.startsWith("/")) {
		return true;
	}
	if (normalized.endsWith("/")) return true;
	const segments = normalized.split("/");
	const lastSegment = segments.at(-1) ?? "";
	if (segments.length > 1 && segments.every((segment) => /^[A-Za-z0-9_.-]+$/.test(segment))) return true;
	return segments.some((segment) => segment.startsWith(".")) || /\.[A-Za-z0-9][A-Za-z0-9_-]*$/.test(lastSegment);
}
