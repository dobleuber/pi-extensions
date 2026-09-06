import type { RouterConfig, WorkModelInfo } from "./config.ts";
import { resolveRouterState } from "./config.ts";
import {
	createRouterDetailsEntry,
	parseSinglePromptBypass,
	type RouterDetailsEntry,
	type RouterProfileDetailsOptions,
} from "./details.ts";
import {
	applyModelProfileDirective,
	createDefaultModelProfileState,
	formatModelProfile,
	parseModelProfilePrompt,
	type ModelProfileApplicationResult,
	type ModelProfileState,
} from "./model-profile.ts";
import { createRouterMetadata, routePromptWithModel, type RouterContextOptions, type RouterModelResult } from "./router-model.ts";
import type { PiAiRuntime } from "./pi-ai-client.ts";

export interface PrepareRoutedPromptInput {
	prompt: string;
	config: RouterConfig;
	workModel?: WorkModelInfo;
	context?: RouterContextOptions;
	profileState?: ModelProfileState;
	runtime?: PiAiRuntime;
	routePrompt?: (prompt: string, config: RouterConfig["routerModel"], context?: RouterContextOptions, runtime?: PiAiRuntime) => Promise<RouterModelResult>;
	applyModelProfile?: (profile: ModelProfileState, previous: ModelProfileState) => Promise<ModelProfileApplicationResult> | ModelProfileApplicationResult;
}

export type PreparedRoutedPrompt =
	| { action: "continue"; prompt: string; bypassed?: boolean }
	| { action: "handled"; message: string; details: RouterDetailsEntry; result: RouterModelResult; profile: ModelProfileState }
	| { action: "transform"; prompt: string; details: RouterDetailsEntry; result: RouterModelResult; profile: ModelProfileState; warning?: string };

export async function prepareRoutedPrompt(input: PrepareRoutedPromptInput): Promise<PreparedRoutedPrompt> {
	const bypass = parseSinglePromptBypass(input.prompt);
	if (bypass.bypass) {
		return { action: "continue", prompt: bypass.prompt, bypassed: true };
	}

	const state = resolveRouterState(input.config);
	if (state.state === "off") {
		return { action: "continue", prompt: input.prompt };
	}

	const activeProfile = input.profileState ?? createDefaultModelProfileState();
	const parsedPrompt = parseModelProfilePrompt(input.prompt);
	const requestedProfile = applyModelProfileDirective(activeProfile, parsedPrompt);
	const application = await applyProfile(input, requestedProfile, activeProfile);
	if (!application.applied) {
		const result = profileApplicationFailureResult(parsedPrompt.prompt, application.error);
		const metadata = createRouterMetadata({
			originalPrompt: input.prompt,
			result,
			routerModel: input.config.routerModel,
		});
		const details = createRouterDetailsEntry(metadata, input.workModel, activeProfile, {
			requestedProfile: requestedProfile.id === activeProfile.id ? undefined : requestedProfile,
			effectiveModel: application.effectiveModel,
			effectiveThinkingLevel: application.effectiveThinkingLevel,
			profileApplicationError: application.error ?? "profile application failed",
		});
		return {
			action: "handled",
			message: `Pi router profile ${formatModelProfile(requestedProfile)} was not applied; prompt was not dispatched: ${application.error ?? "unknown error"}`,
			details,
			result,
			profile: activeProfile,
		};
	}

	const routePrompt = input.routePrompt ?? ((prompt, routerModel, context, runtime) => routePromptWithModel(prompt, routerModel, context, runtime));
	const result = await routePrompt(parsedPrompt.prompt, input.config.routerModel, input.context, input.runtime);
	const metadata = createRouterMetadata({
		originalPrompt: input.prompt,
		result,
		routerModel: input.config.routerModel,
	});
	const details = createRouterDetailsEntry(metadata, input.workModel, requestedProfile, {
		effectiveModel: application.effectiveModel,
		effectiveThinkingLevel: application.effectiveThinkingLevel,
	});

	if (result.degradedReason && input.config.routerModel.fallbackMode === "error") {
		return {
			action: "handled",
			message: `Pi router unavailable; prompt was not dispatched: ${result.degradedReason}`,
			details,
			result,
			profile: requestedProfile,
		};
	}

	if (result.degradedReason && input.config.routerModel.fallbackMode === "passthrough-with-warning") {
		return {
			action: "transform",
			prompt: parsedPrompt.prompt,
			warning: `Pi router warning: translation unavailable; dispatching original prompt. ${result.degradedReason}`,
			details,
			result,
			profile: requestedProfile,
		};
	}

	return {
		action: "transform",
		prompt: result.englishPrompt,
		details,
		result,
		profile: requestedProfile,
	};
}

async function applyProfile(
	input: PrepareRoutedPromptInput,
	requestedProfile: ModelProfileState,
	activeProfile: ModelProfileState,
): Promise<ModelProfileApplicationResult> {
	try {
		return input.applyModelProfile
			? await input.applyModelProfile(requestedProfile, activeProfile)
			: defaultApplication(requestedProfile);
	} catch (error) {
		return {
			applied: false,
			error: error instanceof Error ? error.message : String(error),
		};
	}
}

function defaultApplication(profile: ModelProfileState): ModelProfileApplicationResult {
	return {
		applied: true,
		effectiveModel: { provider: profile.provider, model: profile.model },
		effectiveThinkingLevel: profile.thinkingLevel,
	};
}

function profileApplicationFailureResult(prompt: string, error = "profile application failed"): RouterModelResult {
	return {
		englishPrompt: prompt,
		sourceLanguage: "unknown",
		thinkingLevel: "medium",
		translateFinalAnswer: false,
		degradedReason: error,
	};
}
