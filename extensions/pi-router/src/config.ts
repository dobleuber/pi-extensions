export type RouterState = "off" | "on";
export type RouterFallbackMode = "passthrough" | "passthrough-with-warning" | "error";

export interface RouterModelConfig {
	provider: string;
	model: string;
	baseUrl: string;
	timeoutMs: number;
	fallbackMode: RouterFallbackMode;
	maxInputChars: number;
}

export interface RouterConfig {
	state: RouterState;
	routerModel: RouterModelConfig;
	detailsShortcut?: string;
}

export interface RouterStateOverrides {
	sessionState?: RouterState;
	singlePromptBypass?: boolean;
}

export interface ResolvedRouterState {
	state: RouterState;
	reason: string;
}

export interface WorkModelInfo {
	provider?: string;
	model?: string;
}

export interface RouterStatusInput {
	config: RouterConfig;
	workModel?: WorkModelInfo | null;
	degradedReason?: string | null;
}

export const DEFAULT_ROUTER_CONFIG: RouterConfig = {
	state: "off",
	routerModel: {
		provider: "llama-cpp",
		model: "gemma4",
		baseUrl: "http://127.0.0.1:11434/v1",
		timeoutMs: 5000,
		fallbackMode: "passthrough-with-warning",
		maxInputChars: 12000,
	},
	detailsShortcut: "ctrl+alt+r",
};

export function resolveRouterState(
	config: Pick<RouterConfig, "state">,
	overrides: RouterStateOverrides = {},
): ResolvedRouterState {
	if (overrides.singlePromptBypass) {
		return { state: "off", reason: "single prompt bypass" };
	}
	if (overrides.sessionState !== undefined) {
		return { state: overrides.sessionState, reason: "session override" };
	}
	return { state: config.state, reason: "global default" };
}

export function routerStatusSummary(input: RouterStatusInput): string {
	const routerModel = formatModel(input.config.routerModel.provider, input.config.routerModel.model);
	const workModel = formatModel(input.workModel?.provider, input.workModel?.model);
	const parts = [`router:${input.config.state}`, `routerModel:${routerModel}`, `workModel:${workModel}`];
	if (input.degradedReason) {
		parts.push(`degraded:${input.degradedReason}`);
	}
	return parts.join(" ");
}

function formatModel(provider?: string, model?: string): string {
	if (!provider && !model) return "unknown";
	if (!provider) return model ?? "unknown";
	if (!model) return provider;
	return `${provider}/${model}`;
}
