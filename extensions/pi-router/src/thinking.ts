import type { ThinkingLevel } from "./router-model.ts";

/** Runtime helpers retained for direct/native Pi integrations only. */
export interface PiThinkingRuntime {
	setThinkingLevel(level: ThinkingLevel): void;
	getThinkingLevel?: () => string;
}

/** Apply an explicitly supplied native level; profile selection is owned by model-profile.ts. */
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
