import type { RouterConfig, WorkModelInfo } from "./config.ts";
import { resolveRouterState } from "./config.ts";
import {
	createRouterDetailsEntry,
	parseSinglePromptBypass,
	type RouterDetailsEntry,
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
import type { JevDecisionClient, JevInputDecision } from "./jev.ts";
import { JEV_PROFILE_CATALOG_VERSION, JEV_PROFILE_CRITERIA_VERSION, profileForJevKey } from "./jev-policy.ts";
import type { PiAiRuntime } from "./pi-ai-client.ts";

export interface PrepareRoutedPromptInput {
	prompt: string;
	config: RouterConfig;
	workModel?: WorkModelInfo;
	context?: RouterContextOptions;
	profileState?: ModelProfileState;
	runtime?: PiAiRuntime;
	jev?: JevDecisionClient;
	routePrompt?: (prompt: string, config: RouterConfig["routerModel"], context?: RouterContextOptions, runtime?: PiAiRuntime) => Promise<RouterModelResult>;
	applyModelProfile?: (profile: ModelProfileState, previous: ModelProfileState) => Promise<ModelProfileApplicationResult> | ModelProfileApplicationResult;
}

export type PreparedRoutedPrompt =
	| { action: "continue"; prompt: string; bypassed?: boolean }
	| { action: "handled"; message: string; details: RouterDetailsEntry; result: RouterModelResult; profile: ModelProfileState }
	| { action: "transform"; prompt: string; details: RouterDetailsEntry; result: RouterModelResult; profile: ModelProfileState; warning?: string };

interface JevInputEvaluation {
	decision?: JevInputDecision;
	error?: string;
	cancelled: boolean;
}

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
	const jevEvaluation = await decideWithJev(input.jev, parsedPrompt.prompt, input.context, input.runtime?.signal);
	const jevDecision = jevEvaluation?.decision;
	const requestedProfile = resolveRequestedProfile(activeProfile, parsedPrompt, jevDecision);
	if (jevEvaluation?.cancelled || input.runtime?.signal?.aborted) {
		const result = profileApplicationFailureResult(parsedPrompt.prompt, "Jev decision cancelled");
		const details = createRouterDetailsEntry(createRouterMetadata({
			originalPrompt: input.prompt,
			result,
			routerModel: input.config.routerModel,
		}), input.workModel, activeProfile, {
			inputTranslationOutcome: "fallback",
			jevPolicyRevision: JEV_PROFILE_CRITERIA_VERSION,
			jevCatalogRevision: JEV_PROFILE_CATALOG_VERSION,
			jevFallbackReasons: ["decision cancelled"],
		});
		return {
			action: "handled",
			message: "Pi router Jev decision was cancelled; prompt was not dispatched.",
			details,
			result,
			profile: activeProfile,
		};
	}
	const jevFallbackReasons = collectJevFallbackReasons(jevEvaluation, Boolean(parsedPrompt.profile));
	const inputTranslationOutcome = jevDecision?.canBypassInputTranslation
		? "bypassed" as const
		: hasInputTranslationFallback(jevEvaluation) ? "fallback" as const : "performed" as const;
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
			...(inputTranslationOutcome ? { inputTranslationOutcome } : {}),
			jevInputRecommendation: formatJevInputRecommendation(jevDecision),
			jevPolicyRevision: JEV_PROFILE_CRITERIA_VERSION,
			jevCatalogRevision: JEV_PROFILE_CATALOG_VERSION,
			jevModel: jevDecision?.metadata.model,
			jevDurationMs: jevDecision?.metadata.durationMs,
			jevFallbackReasons: jevFallbackReasons.length > 0 ? jevFallbackReasons : undefined,
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
	const result = jevDecision?.canBypassInputTranslation
		? jevBypassResult(parsedPrompt.prompt, jevDecision)
		: await routePrompt(parsedPrompt.prompt, input.config.routerModel, input.context, input.runtime);
	const metadata = createRouterMetadata({
		originalPrompt: input.prompt,
		result,
		routerModel: input.config.routerModel,
	});
	const details = createRouterDetailsEntry(metadata, input.workModel, requestedProfile, {
		effectiveModel: application.effectiveModel,
		effectiveThinkingLevel: application.effectiveThinkingLevel,
		profileApplicationDeferred: application.deferred,
		...(inputTranslationOutcome ? { inputTranslationOutcome } : {}),
		jevInputRecommendation: formatJevInputRecommendation(jevDecision),
		jevPolicyRevision: JEV_PROFILE_CRITERIA_VERSION,
		jevCatalogRevision: JEV_PROFILE_CATALOG_VERSION,
		jevModel: jevDecision?.metadata.model,
		jevDurationMs: jevDecision?.metadata.durationMs,
		jevFallbackReasons: jevFallbackReasons.length > 0 ? jevFallbackReasons : undefined,
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

async function decideWithJev(
	client: JevDecisionClient | undefined,
	prompt: string,
	context: RouterContextOptions | undefined,
	signal: AbortSignal | undefined,
): Promise<JevInputEvaluation> {
	if (signal?.aborted) return { cancelled: true };
	if (!client) return { cancelled: false, error: "decision client unavailable" };
	try {
		return {
			decision: await client.decideInput({
				prompt,
				...(context?.conversationSummary?.trim() ? { conversationSummary: context.conversationSummary } : {}),
			}, { signal }),
			cancelled: false,
		};
	} catch (error) {
		if (signal?.aborted) return { cancelled: true };
		return { cancelled: false, error: sanitizeJevError(error) };
	}
}

function formatJevInputRecommendation(decision: JevInputDecision | undefined): string | undefined {
	if (!decision) return undefined;
	return `profile:${decision.profileKey ?? "rejected"} input:${decision.inputTranslation} language:${decision.sourceLanguage}`;
}

function hasInputTranslationFallback(evaluation: JevInputEvaluation | undefined): boolean {
	return Boolean(evaluation?.error || !evaluation?.decision || evaluation.decision.inputTranslation === "uncertain");
}

function collectJevFallbackReasons(evaluation: JevInputEvaluation | undefined, explicitProfile: boolean): string[] {
	if (!evaluation) return [];
	const reasons: string[] = [];
	if (evaluation.error) reasons.push(evaluation.error);
	if (!explicitProfile && !evaluation.decision?.profile) reasons.push("profile selection uncertain; using Luna fallback");
	if (evaluation.decision?.inputTranslation === "uncertain") reasons.push("input translation decision uncertain; retaining generative translation");
	return reasons;
}

function sanitizeJevError(error: unknown): string {
	const message = error instanceof Error ? error.message : String(error);
	const key = process.env.TYPESAFE_API_KEY;
	const redacted = key ? message.replaceAll(key, "[redacted]") : message;
	return redacted.replace(/\s+/g, " ").slice(0, 240) || "decision failed";
}

function resolveRequestedProfile(
	activeProfile: ModelProfileState,
	parsedPrompt: ReturnType<typeof parseModelProfilePrompt>,
	decision: JevInputDecision | undefined,
): ModelProfileState {
	if (parsedPrompt.profile) {
		return applyModelProfileDirective(activeProfile, parsedPrompt);
	}
	return decision?.profile ?? profileForJevKey("luna") ?? createDefaultModelProfileState();
}

function jevBypassResult(prompt: string, decision: JevInputDecision): RouterModelResult {
	return {
		englishPrompt: prompt,
		sourceLanguage: decision.sourceLanguage,
		thinkingLevel: "medium",
		translateFinalAnswer: decision.sourceLanguage !== "en",
		usedConversationContext: false,
		resolvedReferences: [],
		unresolvedReferences: [],
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
