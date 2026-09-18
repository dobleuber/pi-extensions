import type { WorkModelInfo } from "./config.ts";

export type ModelProfileId = "luna-max" | "astra-low" | "astra-medium";
export type ModelProfileSource = "default" | "prompt";
export type ProfileThinkingLevel = "low" | "medium" | "high" | "max";

export interface ModelProfile {
	readonly id: ModelProfileId;
	readonly label: string;
	readonly provider: string;
	readonly model: string;
	readonly thinkingLevel: ProfileThinkingLevel;
}

export interface ModelProfileState extends ModelProfile {
	readonly source: ModelProfileSource;
}

export interface ParsedModelProfilePrompt {
	readonly prompt: string;
	readonly profile?: ModelProfileId;
	readonly source?: ModelProfileSource;
}

export const DEFAULT_MODEL_PROFILE: ModelProfile = Object.freeze({
	id: "luna-max",
	label: "Luna Max",
	provider: "openai-codex",
	model: "gpt-5.6-luna",
	thinkingLevel: "max",
});

export const ASTRA_LOW_PROFILE: ModelProfile = Object.freeze({
	id: "astra-low",
	label: "Vega",
	provider: "openai-codex",
	model: "gpt-6-astra",
	thinkingLevel: "low",
});

export const ASTRA_MEDIUM_PROFILE: ModelProfile = Object.freeze({
	id: "astra-medium",
	label: "Astra Medium",
	provider: "openai-codex",
	model: "gpt-6-astra",
	thinkingLevel: "medium",
});

export const MODEL_PROFILES: Readonly<Record<ModelProfileId, ModelProfile>> = Object.freeze({
	[DEFAULT_MODEL_PROFILE.id]: DEFAULT_MODEL_PROFILE,
	[ASTRA_LOW_PROFILE.id]: ASTRA_LOW_PROFILE,
	[ASTRA_MEDIUM_PROFILE.id]: ASTRA_MEDIUM_PROFILE,
} as Record<ModelProfileId, ModelProfile>);

const MODEL_PROFILE_DIRECTIVE = /^\s*(Use Astra:|Usa Astra:|Use Vega:|Usa Vega:|Use Default:|Usa el modelo predeterminado:)/i;

/**
 * Recognize only the supported leading, colon-delimited profile controls.
 * Everything else, including contextual or legacy syntax, remains untouched.
 */
export function parseModelProfilePrompt(prompt: string): ParsedModelProfilePrompt {
	const match = MODEL_PROFILE_DIRECTIVE.exec(prompt);
	if (!match) {
		return { prompt };
	}

	const directive = match[1].toLowerCase();
	const taskPrompt = prompt.slice(match[0].length).replace(/^\s+/, "");
	if (!taskPrompt.trim()) {
		return { prompt };
	}

	const profile: ModelProfileId = directive === "use astra:" || directive === "usa astra:"
		? "astra-medium"
		: directive === "use vega:" || directive === "usa vega:"
			? "astra-low"
			: "luna-max";
	const source: ModelProfileSource = profile === "luna-max" ? "default" : "prompt";

	return {
		prompt: taskPrompt,
		profile,
		source,
	};
}

export function createDefaultModelProfileState(): ModelProfileState {
	return {
		...DEFAULT_MODEL_PROFILE,
		source: "default",
	};
}

export function formatModelProfile(profile: ModelProfileState): string {
	return `${profile.label} (${profile.provider}/${profile.model}, thinking:${profile.thinkingLevel})`;
}

export function applyModelProfileDirective(
	current: ModelProfileState,
	parsed: ParsedModelProfilePrompt,
): ModelProfileState {
	if (!parsed.profile) {
		return current;
	}

	const profile = MODEL_PROFILES[parsed.profile];
	return {
		...profile,
		source: parsed.source ?? (profile.id === DEFAULT_MODEL_PROFILE.id ? "default" : "prompt"),
	};
}

export interface ModelProfileRuntime {
	resolveModel: (provider: string, model: string) => unknown;
	setModel: (model: unknown) => Promise<boolean | void> | boolean | void;
	setThinkingLevel: (level: ProfileThinkingLevel) => Promise<void> | void;
	getEffectiveModel?: () => WorkModelInfo | undefined;
	getEffectiveThinkingLevel?: () => string | undefined;
}

export interface ModelProfileApplicationResult {
	applied: boolean;
	error?: string;
	effectiveModel?: WorkModelInfo;
	effectiveThinkingLevel?: string;
}

function modelIdentity(model: unknown): { provider?: string; model?: string } {
	if (!model || typeof model !== "object") return {};
	const value = model as { provider?: unknown; id?: unknown; model?: unknown };
	return {
		provider: typeof value.provider === "string" ? value.provider : undefined,
		model: typeof value.id === "string" ? value.id : typeof value.model === "string" ? value.model : undefined,
	};
}

/** Resolve and apply one complete profile before the transformed prompt is dispatched. */
export async function applyModelProfileToRuntime(
	profile: ModelProfileState,
	runtime: ModelProfileRuntime,
): Promise<ModelProfileApplicationResult> {
	let result: ModelProfileApplicationResult;
	try {
		const resolvedModel = runtime.resolveModel(profile.provider, profile.model);
		if (!resolvedModel) {
			return {
				applied: false,
				error: `model profile unavailable: ${profile.provider}/${profile.model}`,
			};
		}
		const resolvedIdentity = modelIdentity(resolvedModel);
		if (resolvedIdentity.provider !== profile.provider || resolvedIdentity.model !== profile.model) {
			return {
				applied: false,
				error: `model registry returned ${resolvedIdentity.provider ?? "unknown"}/${resolvedIdentity.model ?? "unknown"} for ${profile.provider}/${profile.model}`,
			};
		}

		const modelAccepted = await runtime.setModel(resolvedModel);
		if (modelAccepted === false) {
			result = {
				applied: false,
				error: `Pi setModel rejected model profile: ${profile.provider}/${profile.model}`,
			};
		} else {
			await runtime.setThinkingLevel(profile.thinkingLevel);

			const effectiveModel = runtime.getEffectiveModel?.() ?? {
				provider: profile.provider,
				model: profile.model,
			};
			const effectiveThinkingLevel = runtime.getEffectiveThinkingLevel?.() ?? profile.thinkingLevel;
			if (effectiveModel.provider !== profile.provider || effectiveModel.model !== profile.model) {
				result = {
					applied: false,
					error: `effective model profile mismatch: expected ${profile.provider}/${profile.model}`,
					effectiveModel,
					effectiveThinkingLevel,
				};
			} else if (effectiveThinkingLevel !== profile.thinkingLevel) {
				result = {
					applied: false,
					error: `effective thinking mismatch: expected ${profile.thinkingLevel}, got ${effectiveThinkingLevel}`,
					effectiveModel,
					effectiveThinkingLevel,
				};
			} else {
				result = { applied: true, effectiveModel, effectiveThinkingLevel };
			}
		}
	} catch (error) {
		result = {
			applied: false,
			error: error instanceof Error ? error.message : String(error),
		};
	}

	return result;
}
