import { DEFAULT_JEV_CONFIG, type JevConfig } from "./jev.ts";
import type { JevCostTier } from "./jev-policy.ts";
import type { ModelProfileState } from "./model-profile.ts";

export type RouterState = "off" | "on";
export type RouterFallbackMode = "passthrough" | "passthrough-with-warning" | "error";

export interface RouterModelConfig {
	provider: string;
	model: string;
	timeoutMs: number;
	fallbackMode: RouterFallbackMode;
	maxInputChars: number;
}

export interface RouterConfig {
	state: RouterState;
	routerModel: RouterModelConfig;
	detailsShortcut?: string;
	jev?: JevConfig;
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
	profile?: ModelProfileState | null;
	degradedReason?: string | null;
}

export const DEFAULT_ROUTER_CONFIG: RouterConfig = {
	state: "off",
	routerModel: {
		provider: "openai-codex",
		model: "gpt-5.6-luna",
		timeoutMs: 15000,
		fallbackMode: "passthrough-with-warning",
		maxInputChars: 12000,
	},
	detailsShortcut: "ctrl+alt+r",
	jev: DEFAULT_JEV_CONFIG,
};

export function resolveJevConfig(config?: Partial<JevConfig>): JevConfig {
	return {
		model: typeof config?.model === "string" && config.model.trim() ? config.model : DEFAULT_JEV_CONFIG.model,
		timeoutMs: typeof config?.timeoutMs === "number" && config.timeoutMs > 0 ? config.timeoutMs : DEFAULT_JEV_CONFIG.timeoutMs,
		maxStateChars: typeof config?.maxStateChars === "number" && config.maxStateChars > 0 ? config.maxStateChars : DEFAULT_JEV_CONFIG.maxStateChars,
		profileMinConfidence: boundedConfidence(config?.profileMinConfidence, DEFAULT_JEV_CONFIG.profileMinConfidence),
		translationMinConfidence: boundedConfidence(config?.translationMinConfidence, DEFAULT_JEV_CONFIG.translationMinConfidence),
		maxProfileCostTier: boundedCostTier(config?.maxProfileCostTier, DEFAULT_JEV_CONFIG.maxProfileCostTier),
	};
}

function boundedConfidence(value: number | undefined, fallback: number): number {
	return typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= 1 ? value : fallback;
}

function boundedCostTier(value: JevCostTier | undefined, fallback: JevCostTier): JevCostTier {
	return value === 1 || value === 2 || value === 3 ? value : fallback;
}

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
	const parts = [`router:${input.config.state}`];
	if (input.profile) {
		parts.push(`profile:${input.profile.label}`, `profileSource:${input.profile.source}`, `profileModel:${formatModel(input.profile.provider, input.profile.model)}`, `profileThinking:${input.profile.thinkingLevel}`);
	}
	parts.push(`routerModel:${routerModel}`, `workModel:${workModel}`);
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
