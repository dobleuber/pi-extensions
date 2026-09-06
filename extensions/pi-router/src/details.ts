import type { WorkModelInfo } from "./config.ts";
import { createDefaultModelProfileState, type ModelProfileState } from "./model-profile.ts";
import type { RouterMetadata } from "./router-model.ts";

export type RouterDetailsPhase = "pre-dispatch" | "complete";

export interface RouterDetails {
	originalPrompt: string;
	transformedPrompt: string;
	sourceLanguage: string;
	routerModel: string;
	requestedThinkingLevel: ModelProfileState["thinkingLevel"];
	workModel: string;
	profileId: ModelProfileState["id"];
	profile: string;
	profileSource: ModelProfileState["source"];
	profileModel: string;
	profileThinkingLevel: ModelProfileState["thinkingLevel"];
	assistantTimestamp?: number;
	effectiveModel?: string;
	requestedProfile?: string;
	requestedProfileModel?: string;
	requestedProfileThinkingLevel?: ModelProfileState["thinkingLevel"];
	profileApplicationError?: string;
	englishAnswer?: string;
	spanishAnswer?: string;
	/** Per-content-block answers preserve boundaries for transient context restoration. */
	englishAnswerBlocks?: string[];
	spanishAnswerBlocks?: string[];
	effectiveThinkingLevel?: string;
	fallbackEvents?: string[];
}

export interface RouterDetailsEntry {
	phase: RouterDetailsPhase;
	expanded: boolean;
	routingState: "on";
	summary: string;
	details: RouterDetails;
}

export interface CompletedRouterDetails {
	englishAnswer: string;
	spanishAnswer: string;
	englishAnswerBlocks?: string[];
	spanishAnswerBlocks?: string[];
	assistantTimestamp?: number;
	effectiveThinkingLevel?: string;
	fallbackEvents?: string[];
}

export interface RouterProfileDetailsOptions {
	requestedProfile?: ModelProfileState;
	effectiveModel?: WorkModelInfo;
	effectiveThinkingLevel?: string;
	profileApplicationError?: string;
}

export function createRouterDetailsEntry(
	metadata: RouterMetadata,
	workModel: WorkModelInfo | undefined,
	profile: ModelProfileState = createDefaultModelProfileState(),
	options: RouterProfileDetailsOptions = {},
): RouterDetailsEntry {
	const formattedWorkModel = formatWorkModel(workModel);
	const profileModel = formatWorkModel({ provider: profile.provider, model: profile.model });
	const effectiveModel = options.effectiveModel
		? formatWorkModel(options.effectiveModel)
		: options.profileApplicationError
			? undefined
			: profileModel;
	const requestedProfile = options.requestedProfile && options.requestedProfile.id !== profile.id
		? options.requestedProfile.label
		: undefined;
	const requestedProfileModel = options.requestedProfile && options.requestedProfile.id !== profile.id
		? formatWorkModel({ provider: options.requestedProfile.provider, model: options.requestedProfile.model })
		: undefined;
	return {
		phase: "pre-dispatch",
		expanded: false,
		routingState: "on",
		summary: `router: ${metadata.sourceLanguage}→en profile:${profile.label} model:${profileModel} thinking:${profile.thinkingLevel} workModel:${formattedWorkModel}`,
		details: {
			originalPrompt: metadata.originalPrompt,
			transformedPrompt: metadata.transformedPrompt,
			sourceLanguage: metadata.sourceLanguage,
			routerModel: metadata.routerModel,
			requestedThinkingLevel: profile.thinkingLevel,
			workModel: formattedWorkModel,
			profileId: profile.id,
			profile: profile.label,
			profileSource: profile.source,
			profileModel,
			profileThinkingLevel: profile.thinkingLevel,
			...(effectiveModel ? { effectiveModel } : {}),
			...(requestedProfile ? { requestedProfile } : {}),
			...(requestedProfileModel ? { requestedProfileModel } : {}),
			...(options.requestedProfile && requestedProfile ? { requestedProfileThinkingLevel: options.requestedProfile.thinkingLevel } : {}),
			...(options.effectiveThinkingLevel ? { effectiveThinkingLevel: options.effectiveThinkingLevel } : {}),
			...(options.profileApplicationError ? { profileApplicationError: options.profileApplicationError } : {}),
			...(metadata.fallback ? { fallbackEvents: [metadata.fallback] } : {}),
		},
	};
}

export function toggleRouterDetails(entry: RouterDetailsEntry): RouterDetailsEntry {
	return { ...entry, expanded: !entry.expanded };
}

export function extendRouterDetailsAfterCompletion(
	entry: RouterDetailsEntry,
	completion: CompletedRouterDetails,
): RouterDetailsEntry {
	return {
		...entry,
		phase: "complete",
		details: {
			...entry.details,
			englishAnswer: completion.englishAnswer,
			spanishAnswer: completion.spanishAnswer,
			...(completion.englishAnswerBlocks ? { englishAnswerBlocks: completion.englishAnswerBlocks } : {}),
			...(completion.spanishAnswerBlocks ? { spanishAnswerBlocks: completion.spanishAnswerBlocks } : {}),
			...(completion.assistantTimestamp !== undefined ? { assistantTimestamp: completion.assistantTimestamp } : {}),
			...(completion.effectiveThinkingLevel ? { effectiveThinkingLevel: completion.effectiveThinkingLevel } : {}),
			...(completion.fallbackEvents ? { fallbackEvents: completion.fallbackEvents } : {}),
		},
	};
}

export function parseSinglePromptBypass(text: string): { bypass: boolean; prompt: string } {
	const trimmed = text.trimStart();
	const prefix = "@router:off";
	if (!trimmed.startsWith(prefix)) {
		return { bypass: false, prompt: text };
	}
	return { bypass: true, prompt: trimmed.slice(prefix.length).trimStart() };
}

export function resolveDetailsShortcut(shortcut = "ctrl+alt+r"): { shortcut: string; conflict?: string } {
	const normalized = shortcut.toLowerCase();
	if (normalized === "ctrl+r") {
		return { shortcut, conflict: "ctrl+r conflicts with Pi session rename unless remapped" };
	}
	if (normalized === "ctrl+t") {
		return { shortcut, conflict: "ctrl+t conflicts with Pi thinking/tree toggles unless remapped" };
	}
	if (normalized === "ctrl+shift+r") {
		return { shortcut, conflict: "ctrl+shift+r conflicts with the files extension restore shortcut" };
	}
	return { shortcut };
}

function formatWorkModel(workModel?: WorkModelInfo): string {
	if (!workModel?.provider && !workModel?.model) return "unknown";
	if (!workModel.provider) return workModel.model ?? "unknown";
	if (!workModel.model) return workModel.provider;
	return `${workModel.provider}/${workModel.model}`;
}
