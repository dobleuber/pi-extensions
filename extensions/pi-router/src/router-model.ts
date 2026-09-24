import type { RouterModelConfig } from "./config.ts";
import { assistantText, completeWithPiRouterModel, userMessage, type PiAiRuntime } from "./pi-ai-client.ts";
import { validatePlaceholderIntegrity } from "./placeholder-integrity.ts";
import { maskProtectedSpans } from "./protected-text.ts";

export type ThinkingLevel = "low" | "medium" | "high";

export interface RouterModelResult {
	englishPrompt: string;
	sourceLanguage: string;
	/** Deprecated router advisory accepted for wire compatibility; never controls work execution. */
	thinkingLevel?: ThinkingLevel;
	translateFinalAnswer: boolean;
	usedConversationContext?: boolean;
	resolvedReferences?: string[];
	unresolvedReferences?: string[];
	degradedReason?: string;
}

export interface RouterMetadata {
	originalPrompt: string;
	transformedPrompt: string;
	sourceLanguage: string;
	routerModel: string;
	/** Deprecated router advisory retained only for metadata compatibility. */
	requestedThinkingLevel?: ThinkingLevel;
	usedConversationContext?: boolean;
	resolvedReferences?: string[];
	unresolvedReferences?: string[];
	fallback?: string;
}

export interface RouterContextOptions {
	conversationSummary?: string;
}

interface PreservedBlockMask {
	text: string;
	restore(text: string): string;
	values: string[];
}

const ROUTER_SYSTEM_PROMPT = `You are Pi Router, a translation/classification function. Return ONLY one JSON object. No prose, no markdown, no extra tasks, no chat transcript.
Rules:
- Translate the complete task into precise, natural, idiomatic English for a coding work model. Preserve its meaning and intent instead of mirroring source-language syntax.
- The translation value must contain only the translated task. Never copy the JSON input envelope or its conversationContext field into the translation.
- If sourceLanguage is es or mixed, translateFinalAnswer must be true.
- If sourceLanguage is en, translateFinalAnswer should be false.
- sourceLanguage is based on the original task text, not the English translation.
- Preserve commands, paths, identifiers, quoted strings, exact placeholders, and error messages exactly.
- Preserve markdown formatting, blank lines, headings, blockquotes, bullet/numbered list markers, and line breaks.
- Preserve placeholders like §P0§ and __PI_ROUTER_PRESERVED_BLOCK_0__ exactly.
- Quoted text and fenced blocks inside the task are part of the latest user prompt data; keep them when they contain examples, errors, prior messages, or bug evidence.
- Use conversation context only to resolve references such as "eso", "lo anterior", or "option 2".
- If you set usedConversationContext to true, the translation must incorporate the resolved referenced content directly.
- Do not leave unresolved placeholder phrases like "do that", "that as well", "previous task", "the above", or "lo anterior" in translation unless you also list them in unresolvedReferences.
- Do not add requirements, constraints, or tasks that are not stated by the latest user prompt or clearly referenced from context.
- If a reference cannot be resolved confidently, keep the prompt faithful and report it in unresolvedReferences instead of inventing intent.

Required JSON keys: translation, sourceLanguage, translateFinalAnswer, usedConversationContext, resolvedReferences, unresolvedReferences.
Allowed sourceLanguage: es, en, mixed, unknown.`;

export function createRouterMetadata(input: {
	originalPrompt: string;
	result: RouterModelResult;
	routerModel: RouterModelConfig;
}): RouterMetadata {
	return {
		originalPrompt: input.originalPrompt,
		transformedPrompt: input.result.englishPrompt,
		sourceLanguage: input.result.sourceLanguage,
		routerModel: `${input.routerModel.provider}/${input.routerModel.model}`,
		...(input.result.thinkingLevel !== undefined ? { requestedThinkingLevel: input.result.thinkingLevel } : {}),
		...(input.result.usedConversationContext !== undefined ? { usedConversationContext: input.result.usedConversationContext } : {}),
		...(input.result.resolvedReferences ? { resolvedReferences: input.result.resolvedReferences } : {}),
		...(input.result.unresolvedReferences ? { unresolvedReferences: input.result.unresolvedReferences } : {}),
		...(input.result.degradedReason ? { fallback: input.result.degradedReason } : {}),
	};
}

export async function routePromptWithModel(
	prompt: string,
	config: RouterModelConfig,
	context: RouterContextOptions = {},
	runtime: PiAiRuntime = {},
): Promise<RouterModelResult> {
	if (prompt.length > config.maxInputChars) {
		return passthrough(prompt, `input exceeds router maxInputChars: ${prompt.length} > ${config.maxInputChars}`);
	}

	const preservedPrompt = maskFencedCodeBlocks(prompt);
	const protectedPrompt = maskProtectedSpans(preservedPrompt.text);
	const restorePrompt = (text: string) => preservedPrompt.restore(protectedPrompt.restore(text));
	try {
		const response = await completeWithPiRouterModel(
			config,
			buildRouterPiAiContext(protectedPrompt.text, context),
			runtime,
		);
		const content = assistantText(response);
		if (!content.trim()) {
			return passthrough(prompt, "router model returned no content");
		}
		return normalizeRouterPayload(parseRouterJsonObject(content), prompt, restorePrompt, protectedPrompt.text);
	} catch (error) {
		return passthrough(prompt, `router model unavailable: ${errorMessage(error)}`);
	}
}

function buildRouterPiAiContext(prompt: string, context: RouterContextOptions) {
	const input: { task: string; conversationContext?: string } = { task: prompt };
	if (context.conversationSummary?.trim()) {
		input.conversationContext = context.conversationSummary.trim();
	}
	return {
		systemPrompt: ROUTER_SYSTEM_PROMPT,
		messages: [userMessage(JSON.stringify(input))],
	};
}

function maskFencedCodeBlocks(text: string): PreservedBlockMask {
	const values: string[] = [];
	const masked = text.replace(/```[\s\S]*?```/g, (match) => {
		const token = `__PI_ROUTER_PRESERVED_BLOCK_${values.length}__`;
		values.push(match);
		return token;
	});
	return {
		text: masked,
		values,
		restore(output: string): string {
			let restored = output;
			const missingValues: string[] = [];
			values.forEach((value, index) => {
				const placeholder = new RegExp(`_{0,2}PI_ROUTER_PRESERV(?:ED|ADO)?_BLOCK_${index}_{0,2}`, "gi");
				const before = restored;
				restored = restored.replace(placeholder, value);
				if (before === restored && !restored.includes(value)) {
					missingValues.push(value);
				}
			});
			if (missingValues.length === 0) return restored;
			return `${restored.trimEnd()}\n\nUser-provided fenced content:\n${missingValues.join("\n\n")}`;
		},
	};
}

function normalizeRouterPayload(
	payload: any,
	originalPrompt: string,
	restoreProtectedSpans: (text: string) => string = (text) => text,
	maskedPrompt: string = originalPrompt,
): RouterModelResult {
	const thinkingLevel = parseThinkingLevel(payload?.thinkingLevel);
	const sourceLanguage = payload?.sourceLanguage === "es" || payload?.sourceLanguage === "en" || payload?.sourceLanguage === "mixed"
		? payload.sourceLanguage
		: "unknown";
	const hasTranslationFlag = typeof payload?.translateFinalAnswer === "boolean";
	const modelTranslateFinalAnswer = hasTranslationFlag ? payload.translateFinalAnswer : true;
	const translateFinalAnswer = sourceLanguage === "es" || sourceLanguage === "mixed"
		? true
		: modelTranslateFinalAnswer;
	const usedConversationContext = payload?.usedConversationContext === true;
	const resolvedReferences = parseStringArray(payload?.resolvedReferences);
	const unresolvedReferences = parseStringArray(payload?.unresolvedReferences);
	const candidateTranslation = typeof payload?.translation === "string" && payload.translation.trim()
		? payload.translation.trim()
		: typeof payload?.englishPrompt === "string" && payload.englishPrompt.trim()
			? payload.englishPrompt.trim()
			: originalPrompt;
	const unwrappedTranslation = unwrapTranslatedTask(candidateTranslation, originalPrompt);
	if (unwrappedTranslation.error) {
		return passthrough(originalPrompt, unwrappedTranslation.error);
	}
	const translatedPrompt = unwrappedTranslation.task;
	const placeholderMismatch = validatePlaceholderIntegrity(maskedPrompt, translatedPrompt);
	if (placeholderMismatch) {
		return passthrough(originalPrompt, `router model ${placeholderMismatch}`);
	}
	const restoredPrompt = restoreProtectedSpans(translatedPrompt);
	const lostLiteral = requiredPromptLiterals(originalPrompt).find((literal) => !restoredPrompt.includes(literal));
	if (lostLiteral) {
		return passthrough(originalPrompt, `router model lost required literal: ${lostLiteral}`);
	}
	if (/^fix the tests[.!]?$/i.test(restoredPrompt) && !/\b(?:arregla|corrige|fix)\b[\s\S]*\btests?\b/i.test(originalPrompt)) {
		return passthrough(originalPrompt, "router model leaked legacy example output");
	}
	return {
		englishPrompt: restoredPrompt,
		sourceLanguage,
		thinkingLevel,
		translateFinalAnswer,
		usedConversationContext,
		resolvedReferences,
		unresolvedReferences,
	};
}

function unwrapTranslatedTask(
	translation: string,
	originalPrompt: string,
): { task: string; error?: string } {
	const originalObject = parseJsonRecord(originalPrompt);
	if (isRouterInputEnvelope(originalObject)) {
		// A user may intentionally ask the router to translate this JSON shape.
		return { task: translation };
	}

	const translatedObject = parseJsonRecord(translation);
	if (!isRouterInputEnvelope(translatedObject)) return { task: translation };
	if (typeof translatedObject.task !== "string" || !translatedObject.task.trim()) {
		return { task: originalPrompt, error: "router model returned an invalid task envelope" };
	}
	return { task: translatedObject.task.trim() };
}

function parseJsonRecord(value: string): Record<string, unknown> | undefined {
	try {
		const parsed: unknown = JSON.parse(value);
		return parsed && typeof parsed === "object" && !Array.isArray(parsed)
			? parsed as Record<string, unknown>
			: undefined;
	} catch {
		return undefined;
	}
}

function isRouterInputEnvelope(value: Record<string, unknown> | undefined): value is Record<string, unknown> {
	if (!value) return false;
	const keys = Object.keys(value);
	return keys.length > 0
		&& keys.every((key) => key === "task" || key === "conversationContext")
		&& (!Object.prototype.hasOwnProperty.call(value, "conversationContext") || typeof value.conversationContext === "string");
}

function requiredPromptLiterals(text: string): string[] {
	return [...text.matchAll(/`[^`\n]+`|"[^"\n]+"|'[^'\n]+'/g)].map((match) => match[0]);
}

function parseRouterJsonObject(content: string): any {
	const trimmed = content.trim();
	try {
		return JSON.parse(trimmed);
	} catch (error) {
		throw new SyntaxError(`router model returned invalid JSON: ${errorMessage(error)}`);
	}
}

function parseThinkingLevel(value: unknown): ThinkingLevel {
	return ["low", "medium", "high"].includes(String(value)) ? value as ThinkingLevel : "medium";
}

function parseStringArray(value: unknown): string[] {
	return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function passthrough(prompt: string, degradedReason: string): RouterModelResult {
	return {
		englishPrompt: prompt,
		sourceLanguage: "unknown",
		thinkingLevel: "medium",
		translateFinalAnswer: true,
		usedConversationContext: false,
		resolvedReferences: [],
		unresolvedReferences: [],
		degradedReason,
	};
}

function errorMessage(error: unknown): string {
	return error instanceof Error ? error.message : String(error);
}
