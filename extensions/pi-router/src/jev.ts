import { TypeSafeClient } from "@typesafe-ai/sdk";
import {
	eligibleJevProfileCandidates,
	selectJevProfile,
	type JevCostTier,
	type JevProfileKey,
} from "./jev-policy.ts";
import type { ModelProfileState } from "./model-profile.ts";

export type JevTranslationNeed = "required" | "not_required" | "uncertain";
export type JevSourceLanguage = "en" | "es" | "mixed" | "other" | "unknown";

export interface JevConfig {
	readonly model: string;
	readonly timeoutMs: number;
	readonly maxStateChars: number;
	readonly profileMinConfidence: number;
	readonly translationMinConfidence: number;
	readonly maxProfileCostTier: JevCostTier;
}

export const DEFAULT_JEV_CONFIG: JevConfig = Object.freeze({
	model: "jev-1.13.0",
	timeoutMs: 1000,
	maxStateChars: 12000,
	profileMinConfidence: 0.7,
	translationMinConfidence: 0.85,
	maxProfileCostTier: 3,
});

export interface JevInputState {
	readonly prompt: string;
	readonly conversationSummary?: string;
}

export interface JevRequestOptions {
	readonly signal?: AbortSignal;
	readonly timeoutMs?: number;
}

export interface JevChoiceQuestion {
	readonly type: "choice";
	readonly instructions: string;
	readonly criteria: Readonly<Record<string, string>>;
}

export interface JevSystemOneRequest {
	readonly model: string;
	readonly state: unknown;
	readonly questions: Readonly<Record<string, JevChoiceQuestion>>;
}

export interface JevChoiceAnswer {
	readonly type: "choice";
	readonly choice: string;
	readonly confidence: number;
	readonly probabilities: Readonly<Record<string, number>>;
}

export interface JevSystemOneResult {
	readonly model: string;
	readonly answers: Readonly<Record<string, JevChoiceAnswer>>;
	readonly usage: {
		readonly input_tokens: number;
		readonly output_tokens: number;
	};
}

export interface JevTransport {
	systemOne(request: JevSystemOneRequest, options?: JevRequestOptions): Promise<JevSystemOneResult>;
}

export interface JevDecisionMetadata {
	readonly model: string;
	readonly inputTokens: number;
	readonly outputTokens: number;
	readonly durationMs?: number;
}

export interface JevUsage {
	readonly input_tokens: number;
	readonly output_tokens: number;
}

export interface JevInputDecision {
	readonly model: string;
	readonly usage: JevUsage;
	readonly profile?: ModelProfileState;
	readonly profileKey?: JevProfileKey;
	readonly profileConfidence: number;
	readonly profileProbabilities: Readonly<Record<string, number>>;
	readonly inputTranslation: JevTranslationNeed;
	readonly inputTranslationConfidence: number;
	readonly sourceLanguage: JevSourceLanguage;
	readonly sourceLanguageConfidence: number;
	readonly canBypassInputTranslation: boolean;
	readonly metadata: JevDecisionMetadata;
}

export interface JevResponseDecision {
	readonly model: string;
	readonly usage: JevUsage;
	readonly translation: JevTranslationNeed;
	readonly confidence: number;
	readonly probabilities: Readonly<Record<string, number>>;
	readonly canBypass: boolean;
	readonly metadata: JevDecisionMetadata;
}

export interface JevDecisionClient {
	decideInput(state: JevInputState, options?: JevRequestOptions): Promise<JevInputDecision>;
	decideResponse(response: string, options?: JevRequestOptions): Promise<JevResponseDecision>;
}

export function buildJevInputRequest(state: JevInputState, config: JevConfig): JevSystemOneRequest {
	const boundedState = {
		task: state.prompt,
		...(state.conversationSummary?.trim() ? { conversationSummary: state.conversationSummary.trim() } : {}),
	};
	assertStateWithinLimit(boundedState, config.maxStateChars);
	return {
		model: config.model,
		state: boundedState,
		questions: {
			profile: {
				type: "choice",
				instructions: "Which approved work profile is the best fit for this task? Choose only the profile whose description matches the task's expected reasoning depth and cost sensitivity.",
				criteria: Object.fromEntries(eligibleJevProfileCandidates(undefined, config.maxProfileCostTier).map((candidate) => [candidate.key, candidate.description])),
			},
			inputTranslation: {
				type: "choice",
				instructions: "Does the task's natural-language instruction require translation into English before it is sent to the coding work model? Judge instructions, not quoted examples, code, commands, identifiers, or logs.",
				criteria: {
					required: "The task instructions contain Spanish or other non-English prose whose meaning should be translated into English.",
					not_required: "The task instructions are already English or contain only language-neutral technical content; forwarding unchanged is safe.",
					uncertain: "The task language or intent cannot be classified safely from the bounded state.",
				},
			},
			sourceLanguage: {
				type: "choice",
				instructions: "Classify the natural-language task instructions, ignoring protected code, commands, identifiers, logs, and quoted evidence.",
				criteria: {
					en: "The task instructions are English.",
					es: "The task instructions are Spanish.",
					mixed: "The task instructions contain meaningful English and Spanish prose.",
					other: "The task instructions primarily use another natural language.",
				},
			},
		},
	};
}

export function buildJevResponseRequest(response: string, config: JevConfig): JevSystemOneRequest {
	assertStateWithinLimit({ response }, config.maxStateChars);
	return {
		model: config.model,
		state: { response },
		questions: {
			responseTranslation: {
				type: "choice",
				instructions: "Does the final response contain natural-language prose that requires translation into Spanish? Ignore code, commands, paths, identifiers, logs, and language-neutral technical content.",
				criteria: {
					required: "The response contains English or other non-Spanish prose that should be translated into Spanish.",
					not_required: "The response prose is already Spanish or contains only language-neutral technical content.",
					uncertain: "The response language cannot be classified safely from the bounded response.",
				},
			},
		},
	};
}

export function createJevDecisionClient(config: JevConfig, transport?: JevTransport): JevDecisionClient {
	const activeTransport = transport ?? createTypeSafeTransport(config);
	return {
		async decideInput(state, options) {
			const started = Date.now();
			const result = await callWithDeadline(
				activeTransport,
				buildJevInputRequest(state, config),
				options,
				config,
			);
			return normalizeInputDecision(result, config, Date.now() - started);
		},
		async decideResponse(response, options) {
			const started = Date.now();
			const result = await callWithDeadline(
				activeTransport,
				buildJevResponseRequest(response, config),
				options,
				config,
			);
			return normalizeResponseDecision(result, config, Date.now() - started);
		},
	};
}

function createTypeSafeTransport(config: JevConfig): JevTransport {
	const client = new TypeSafeClient({
		apiKey: process.env.TYPESAFE_API_KEY,
		defaultModel: config.model,
		logLevel: "off",
		timeout: config.timeoutMs,
		retry: { maxRetries: 0 },
	});
	return {
		async systemOne(request, options) {
			const result = await client.systemOne(request as never, {
				signal: options?.signal,
				timeout: options?.timeoutMs ?? config.timeoutMs,
				retry: { maxRetries: 0 },
			});
			return result as unknown as JevSystemOneResult;
		},
	};
}

function normalizeInputDecision(result: JevSystemOneResult, config: JevConfig, durationMs?: number): JevInputDecision {
	const profile = readChoice(result, "profile", eligibleJevProfileCandidates(undefined, config.maxProfileCostTier).map((candidate) => candidate.key));
	const translation = readChoice(result, "inputTranslation", ["required", "not_required", "uncertain"]);
	const language = readChoice(result, "sourceLanguage", ["en", "es", "mixed", "other"]);
	const inputTranslation = normalizeTranslationNeed(translation.choice, translation.confidence, config.translationMinConfidence);
	const acceptedProfile = profile.confidence >= config.profileMinConfidence ? selectJevProfile(profile.choice, undefined, config.maxProfileCostTier) : undefined;
	return {
		model: decisionMetadata(result, durationMs).model,
		usage: normalizedUsage(result),
		...(acceptedProfile ? { profile: acceptedProfile, profileKey: profile.choice as JevProfileKey } : {}),
		profileConfidence: profile.confidence,
		profileProbabilities: profile.probabilities,
		inputTranslation,
		inputTranslationConfidence: translation.confidence,
		sourceLanguage: language.choice as JevSourceLanguage,
		sourceLanguageConfidence: language.confidence,
		canBypassInputTranslation: inputTranslation === "not_required" && language.choice !== "es" && language.choice !== "other",
		metadata: decisionMetadata(result, durationMs),
	};
}

function normalizeResponseDecision(result: JevSystemOneResult, config: JevConfig, durationMs?: number): JevResponseDecision {
	const translation = readChoice(result, "responseTranslation", ["required", "not_required", "uncertain"]);
	const need = normalizeTranslationNeed(translation.choice, translation.confidence, config.translationMinConfidence);
	return {
		model: decisionMetadata(result, durationMs).model,
		usage: normalizedUsage(result),
		translation: need,
		confidence: translation.confidence,
		probabilities: translation.probabilities,
		canBypass: need === "not_required",
		metadata: decisionMetadata(result, durationMs),
	};
}

function normalizeTranslationNeed(choice: string, confidence: number, minimumConfidence: number): JevTranslationNeed {
	if (choice === "not_required" && confidence < minimumConfidence) return "uncertain";
	return choice as JevTranslationNeed;
}

function readChoice(result: JevSystemOneResult, key: string, allowed: readonly string[]): JevChoiceAnswer {
	const answer = result.answers?.[key];
	if (!answer || answer.type !== "choice" || !allowed.includes(answer.choice)) {
		throw new Error(`invalid Jev choice answer: ${key}`);
	}
	if (!Number.isFinite(answer.confidence) || answer.confidence < 0 || answer.confidence > 1) {
		throw new Error(`invalid Jev confidence: ${key}`);
	}
	const probabilities = answer.probabilities;
	if (!probabilities || typeof probabilities !== "object" || Array.isArray(probabilities)) {
		throw new Error(`invalid Jev probabilities: ${key}`);
	}
	const probabilityKeys = Object.keys(probabilities);
	if (probabilityKeys.some((choice) => !allowed.includes(choice)) || allowed.some((choice) => !Object.prototype.hasOwnProperty.call(probabilities, choice))) {
		throw new Error(`incomplete Jev probabilities: ${key}`);
	}
	let total = 0;
	for (const value of Object.values(probabilities)) {
		if (!Number.isFinite(value) || value < 0 || value > 1) throw new Error(`invalid Jev probabilities: ${key}`);
		total += value;
	}
	if (Math.abs(total - 1) > 0.02) throw new Error(`invalid Jev probability distribution: ${key}`);
	return {
		type: "choice",
		choice: answer.choice,
		confidence: answer.confidence,
		probabilities: { ...probabilities },
	};
}

function normalizedUsage(result: JevSystemOneResult): JevUsage {
	const inputTokens = result.usage?.input_tokens;
	const outputTokens = result.usage?.output_tokens;
	if (!Number.isFinite(inputTokens) || !Number.isFinite(outputTokens) || inputTokens < 0 || outputTokens < 0) {
		throw new Error("invalid Jev usage metadata");
	}
	return { input_tokens: inputTokens, output_tokens: outputTokens };
}

function decisionMetadata(result: JevSystemOneResult, durationMs?: number): JevDecisionMetadata {
	const usage = normalizedUsage(result);
	if (typeof result.model !== "string" || !result.model.trim()) throw new Error("invalid Jev model metadata");
	return {
		model: result.model,
		inputTokens: usage.input_tokens,
		outputTokens: usage.output_tokens,
		...(durationMs !== undefined ? { durationMs } : {}),
	};
}

function callWithDeadline(
	transport: JevTransport,
	request: JevSystemOneRequest,
	options: JevRequestOptions | undefined,
	config: JevConfig,
): Promise<JevSystemOneResult> {
	const timeoutMs = typeof options?.timeoutMs === "number" && options.timeoutMs > 0 ? options.timeoutMs : config.timeoutMs;
	const controller = new AbortController();
	let timer: ReturnType<typeof setTimeout> | undefined;
	let removeExternalAbort: (() => void) | undefined;

	return new Promise<JevSystemOneResult>((resolve, reject) => {
		let settled = false;
		const finish = (callback: () => void) => {
			if (settled) return;
			settled = true;
			if (timer !== undefined) clearTimeout(timer);
			removeExternalAbort?.();
			callback();
		};
		const abort = (error: Error) => {
			if (!controller.signal.aborted) controller.abort(error);
			finish(() => reject(error));
		};
		const externalSignal = options?.signal;
		if (externalSignal?.aborted) {
			abort(new Error("Jev request aborted"));
			return;
		}
		if (externalSignal) {
			const onExternalAbort = () => abort(new Error("Jev request aborted"));
			externalSignal.addEventListener("abort", onExternalAbort, { once: true });
			removeExternalAbort = () => externalSignal.removeEventListener("abort", onExternalAbort);
		}
		timer = setTimeout(() => abort(new Error(`Jev request timed out after ${timeoutMs}ms`)), timeoutMs);
		Promise.resolve()
			.then(() => {
				if (controller.signal.aborted) throw new Error("Jev request aborted");
				return transport.systemOne(request, { ...options, signal: controller.signal, timeoutMs });
			})
			.then((result) => finish(() => resolve(result)), (error: unknown) => finish(() => reject(error instanceof Error ? error : new Error(String(error)))));
	});
}

function assertStateWithinLimit(state: Record<string, string>, maxStateChars: number): void {
	if (JSON.stringify(state).length > maxStateChars) {
		throw new Error(`Jev state exceeds configured limit: ${maxStateChars} characters`);
	}
}
