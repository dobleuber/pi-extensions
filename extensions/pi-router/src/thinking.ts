import type { ThinkingLevel } from "./router-model.ts";

export interface ThinkingDecision {
	level: ThinkingLevel;
	reason: string;
}

export interface PiThinkingRuntime {
	setThinkingLevel(level: ThinkingLevel): void;
	getThinkingLevel?: () => string;
}

export interface ThinkingMetadata {
	requestedThinkingLevel: ThinkingLevel;
	effectiveThinkingLevel?: string;
	thinkingReason: string;
}

const SIMPLE_PATTERNS = [
	/\bhola\b/i,
	/\bdime la hora\b/i,
	/\bque hora\b/i,
	/\bexplica brevemente\b/i,
	/\bstatus\b/i,
];

const ROUTINE_PATTERNS = [
	/\breadme\b/i,
	/\btests?\b/i,
	/\bpruebas\b/i,
	/\bedita\b/i,
	/\bactualiza\b/i,
	/\bdocumenta\b/i,
];

const HIGH_RISK_PATTERNS = [
	/\brefactor/i,
	/\bmultiples?\s+modulos\b/i,
	/\barquitectura\b/i,
	/\bdebug/i,
	/\bseguridad\b/i,
	/\bperformance\b/i,
	/\bborra\b/i,
	/\belimina\b/i,
	/\bdestruye\b/i,
	/\buninstall\b/i,
];

export function selectThinkingLevel(prompt: string, modelSuggestion?: ThinkingLevel): ThinkingDecision {
	if (matchesAny(HIGH_RISK_PATTERNS, prompt)) {
		return { level: "high", reason: "complex, risky, or destructive task" };
	}
	if (matchesAny(SIMPLE_PATTERNS, prompt)) {
		return { level: "low", reason: "simple low-risk prompt" };
	}
	if (matchesAny(ROUTINE_PATTERNS, prompt)) {
		return { level: "medium", reason: "routine coding or documentation task" };
	}
	if (modelSuggestion === "high") {
		return { level: "high", reason: "router model classified prompt as high complexity" };
	}
	if (modelSuggestion === "low") {
		return { level: "medium", reason: "uncertain prompt, conservative default" };
	}
	return { level: modelSuggestion ?? "medium", reason: "uncertain prompt, conservative default" };
}

export function applyThinkingLevel(runtime: PiThinkingRuntime, level: ThinkingLevel): string | undefined {
	runtime.setThinkingLevel(level);
	return runtime.getThinkingLevel?.();
}

export function thinkingCliArgs(level: ThinkingLevel): string[] {
	return ["--thinking", level];
}

export function thinkingRpcCommand(level: ThinkingLevel): { type: "set_thinking_level"; level: ThinkingLevel } {
	return { type: "set_thinking_level", level };
}

export function createThinkingMetadata(
	requestedThinkingLevel: ThinkingLevel,
	effectiveThinkingLevel: string | undefined,
	thinkingReason: string,
): ThinkingMetadata {
	return {
		requestedThinkingLevel,
		...(effectiveThinkingLevel ? { effectiveThinkingLevel } : {}),
		thinkingReason,
	};
}

function matchesAny(patterns: RegExp[], value: string): boolean {
	return patterns.some((pattern) => pattern.test(value));
}
