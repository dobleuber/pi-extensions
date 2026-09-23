import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { DEFAULT_ROUTER_CONFIG, resolveJevConfig, routerStatusSummary, type RouterConfig, type RouterState } from "./config.ts";
import { extendRouterDetailsAfterCompletion, resolveDetailsShortcut, toggleRouterDetails, type RouterDetailsEntry } from "./details.ts";
import { translateFinalAnswerToSpanish, type FinalAnswerTranslationResult } from "./final-answer.ts";
import { createJevDecisionClient, type JevDecisionClient } from "./jev.ts";
import { maskProtectedSpans } from "./protected-text.ts";
import { shouldRouteInput } from "./input.ts";
import {
	applyModelProfileToRuntime,
	createDefaultModelProfileState,
	formatModelProfile,
	type ModelProfileApplicationResult,
	type ModelProfileRuntime,
	type ModelProfileState,
} from "./model-profile.ts";
import { prepareRoutedPrompt, type PrepareRoutedPromptInput } from "./pipeline.ts";
import { routePromptWithModel } from "./router-model.ts";
import { createFileRouterStateStore, type RouterStateStore } from "./state.ts";
import { selectedWorkModelFromPiContext } from "./work-model.ts";
import type { PiAiRuntime } from "./pi-ai-client.ts";

export interface PiRouterDependencies {
	config?: RouterConfig;
	routePrompt?: PrepareRoutedPromptInput["routePrompt"];
	translateFinalAnswer?: (answer: string, config: RouterConfig["routerModel"], runtime?: PiAiRuntime) => Promise<FinalAnswerTranslationResult>;
	applyModelProfile?: (profile: ModelProfileState, previous: ModelProfileState, ctx: any) => Promise<ModelProfileApplicationResult> | ModelProfileApplicationResult;
	jev?: JevDecisionClient;
	stateStore?: RouterStateStore;
}

type AssistantMessagePhase = "commentary" | "final_answer";

interface FinalTextBlock {
	index: number;
	text: string;
}

interface StoredAssistantAnswer {
	english: string;
	spanish: string;
	englishBlocks?: string[];
	spanishBlocks?: string[];
}

function phaseFromTextSignature(signature: unknown): AssistantMessagePhase | undefined {
	if (typeof signature !== "string") return undefined;
	try {
		const parsed = JSON.parse(signature);
		return parsed?.phase === "commentary" || parsed?.phase === "final_answer" ? parsed.phase : undefined;
	} catch {
		return undefined;
	}
}

function messagePhase(message: any): AssistantMessagePhase | undefined {
	return message?.phase === "commentary" || message?.phase === "final_answer" ? message.phase : undefined;
}

function hasToolCallContent(content: unknown): boolean {
	return Array.isArray(content) && content.some((part) => part && typeof part === "object" && (part as any).type === "toolCall");
}

function assistantMessagePhase(message: any): AssistantMessagePhase | undefined {
	if (!Array.isArray(message?.content)) return messagePhase(message);
	const phases = message.content
		.filter((part: any) => part?.type === "text")
		.map((part: any) => phaseFromTextSignature(part.textSignature))
		.filter((phase: AssistantMessagePhase | undefined): phase is AssistantMessagePhase => phase !== undefined);
	const hasCommentary = phases.includes("commentary");
	const hasFinalAnswer = phases.includes("final_answer");
	if (hasCommentary && hasFinalAnswer) return undefined;
	if (hasFinalAnswer) return "final_answer";
	if (hasCommentary) return "commentary";
	return messagePhase(message);
}

/** Return only text blocks that belong to the final answer, retaining their source indexes. */
function extractFinalTextBlocks(message: any): FinalTextBlock[] {
	const content = message?.content;
	if (typeof content === "string") return [{ index: -1, text: content }];
	if (!Array.isArray(content)) return [];

	const textBlocks = content
		.map((part: any, index: number) => ({ index, part, phase: part?.type === "text" ? phaseFromTextSignature(part.textSignature) : undefined }))
		.filter((entry: any): entry is { index: number; part: any; phase: AssistantMessagePhase | undefined } =>
			entry.part?.type === "text" && typeof entry.part.text === "string");
	if (textBlocks.length === 0) return [];

	const hasTaggedPhase = textBlocks.some((entry) => entry.phase !== undefined);
	if (hasTaggedPhase) {
		const finalBlocks = textBlocks.filter((entry) => entry.phase === "final_answer");
		if (finalBlocks.length > 0) return finalBlocks.map(({ index, part }) => ({ index, text: part.text }));
		// A top-level final phase can identify unsigned text alongside a signed
		// commentary block; never treat signed commentary as final content.
		if (messagePhase(message) === "final_answer") {
			return textBlocks
				.filter((entry) => entry.phase === undefined)
				.map(({ index, part }) => ({ index, text: part.text }));
		}
		return [];
	}
	if (messagePhase(message) === "commentary") return [];
	return textBlocks.map(({ index, part }) => ({ index, text: part.text }));
}

function replaceFinalTextBlocks(content: unknown, replacements: Map<number, string>): unknown {
	if (typeof content === "string") return replacements.has(-1) ? replacements.get(-1) : content;
	if (!Array.isArray(content)) return content;
	return content.map((part, index) => {
		if (!replacements.has(index)) return part;
		return { ...(part as any), text: replacements.get(index) };
	});
}

function isRogerSpeechRequest(event: any): boolean {
	const metadata = event?.metadata ?? event?.context ?? {};
	const speech = metadata?.speech ?? event?.speech;
	return (event?.source === "roger" || metadata?.source === "roger") && speech?.enabled === true;
}

function buildRogerSpeechResponse(displayText: string, speechText: string): string {
	return JSON.stringify({
		display_text: displayText,
		speech_text: speechText,
		speech_language: "es",
		speech_source: "pi-router",
	});
}

function isNativeModelControl(text: string): boolean {
	return /^\s*\/(?:model|thinking)(?:\s|$)/i.test(text);
}

function createPiModelProfileRuntime(pi: any, ctx: any): ModelProfileRuntime | undefined {
	if (!ctx?.modelRegistry || typeof pi?.setModel !== "function" || typeof pi?.setThinkingLevel !== "function") {
		return undefined;
	}
	return {
		resolveModel: (provider, model) => ctx.modelRegistry.find(provider, model),
		setModel: (model) => pi.setModel(model),
		setThinkingLevel: (level) => pi.setThinkingLevel(level),
		getEffectiveModel: () => selectedWorkModelFromPiContext(ctx),
		getEffectiveThinkingLevel: () => typeof pi.getThinkingLevel === "function" ? pi.getThinkingLevel() : ctx.thinkingLevel,
	};
}

async function applyPiModelProfile(
	pi: any,
	ctx: any,
	profile: ModelProfileState,
	dependencies: PiRouterDependencies,
	previous: ModelProfileState,
): Promise<ModelProfileApplicationResult> {
	if (dependencies.applyModelProfile) {
		return dependencies.applyModelProfile(profile, previous, ctx);
	}

	const runtime = createPiModelProfileRuntime(pi, ctx);
	if (!runtime) {
		// Test/RPC shims may not expose model APIs; the real Pi context always does.
		return {
			applied: true,
			effectiveModel: { provider: profile.provider, model: profile.model },
			effectiveThinkingLevel: profile.thinkingLevel,
		};
	}
	return applyModelProfileToRuntime(profile, runtime);
}

function replaceTextContent(content: unknown, text: string): unknown {
	if (typeof content === "string") return text;
	if (Array.isArray(content)) {
		let replaced = false;
		const replacedContent = content.map((part) => {
			if (!replaced && part && typeof part === "object" && (part as any).type === "text") {
				replaced = true;
				return { ...part, text };
			}
			return part;
		});
		return replaced ? replacedContent : [...replacedContent, { type: "text", text }];
	}
	return [{ type: "text", text }];
}

function restoreEnglishAssistantContext(messages: any[], branch: any[]): any[] {
	const answersByTimestamp = new Map<number, StoredAssistantAnswer[]>();
	const answersBySpanish = new Map<string, string[]>();
	for (const entry of branch) {
		if (entry?.type !== "custom" || entry.customType !== "pi-router-details" || entry.data?.phase !== "complete") continue;
		const details = entry.data.details;
		const english = details?.englishAnswer;
		const spanish = details?.spanishAnswer;
		const englishBlocks = Array.isArray(details?.englishAnswerBlocks)
			&& details.englishAnswerBlocks.every((block: unknown) => typeof block === "string")
			? details.englishAnswerBlocks as string[]
			: undefined;
		const spanishBlocks = Array.isArray(details?.spanishAnswerBlocks)
			&& details.spanishAnswerBlocks.every((block: unknown) => typeof block === "string")
			? details.spanishAnswerBlocks as string[]
			: undefined;
		if (typeof english !== "string" || typeof spanish !== "string") continue;
		const answer: StoredAssistantAnswer = { english, spanish, englishBlocks, spanishBlocks };
		const hasChangedBlock = englishBlocks && spanishBlocks && englishBlocks.length === spanishBlocks.length
			? englishBlocks.some((block, index) => block !== spanishBlocks[index])
			: false;
		if (english === spanish && !hasChangedBlock) continue;
		if (typeof details?.assistantTimestamp === "number") {
			const timestamp = details.assistantTimestamp;
			answersByTimestamp.set(timestamp, [...(answersByTimestamp.get(timestamp) ?? []), answer]);
		}
		if (englishBlocks && spanishBlocks && englishBlocks.length === spanishBlocks.length) {
			for (let index = 0; index < englishBlocks.length; index += 1) {
				const blockSpanish = spanishBlocks[index];
				const blockEnglish = englishBlocks[index];
				if (blockSpanish !== blockEnglish) {
					answersBySpanish.set(blockSpanish, [...(answersBySpanish.get(blockSpanish) ?? []), blockEnglish]);
				}
			}
		} else {
			answersBySpanish.set(spanish, [...(answersBySpanish.get(spanish) ?? []), english]);
		}
	}

	const assistantTextCounts = new Map<string, number>();
	const assistantTimestampCounts = new Map<number, number>();
	for (const message of messages) {
		if (message?.role !== "assistant") continue;
		for (const block of extractFinalTextBlocks(message)) {
			assistantTextCounts.set(block.text, (assistantTextCounts.get(block.text) ?? 0) + 1);
		}
		if (typeof message.timestamp === "number") {
			assistantTimestampCounts.set(message.timestamp, (assistantTimestampCounts.get(message.timestamp) ?? 0) + 1);
		}
	}

	return messages.map((message) => {
		if (message?.role !== "assistant") return message;
		if (typeof message.timestamp === "number" && assistantTimestampCounts.get(message.timestamp) === 1) {
			const timestampAnswers = answersByTimestamp.get(message.timestamp);
			if (timestampAnswers?.length === 1) {
				const restored = restoreStoredAssistantAnswer(message, timestampAnswers[0]);
				if (restored !== message) return restored;
			}
		}

		const replacements = new Map<number, string>();
		for (const block of extractFinalTextBlocks(message)) {
			if (assistantTextCounts.get(block.text) !== 1) continue;
			const englishAnswers = answersBySpanish.get(block.text);
			if (englishAnswers?.length === 1 && englishAnswers[0] !== block.text) {
				replacements.set(block.index, englishAnswers[0]);
			}
		}
		return replacements.size > 0 ? { ...message, content: replaceFinalTextBlocks(message.content, replacements) } : message;
	});
}

function restoreStoredAssistantAnswer(message: any, answer: StoredAssistantAnswer): any {
	const finalBlocks = extractFinalTextBlocks(message);
	if (finalBlocks.length === 0) return message;
	if (answer.englishBlocks && answer.spanishBlocks
		&& answer.englishBlocks.length === finalBlocks.length
		&& answer.spanishBlocks.length === finalBlocks.length) {
		const replacements = new Map<number, string>();
		for (let index = 0; index < finalBlocks.length; index += 1) {
			const block = finalBlocks[index];
			const english = answer.englishBlocks[index];
			if (block.text !== english) replacements.set(block.index, english);
		}
		return replacements.size > 0 ? { ...message, content: replaceFinalTextBlocks(message.content, replacements) } : message;
	}
	if (finalBlocks.length !== 1 || finalBlocks[0].text === answer.english) return message;
	return { ...message, content: replaceFinalTextBlocks(message.content, new Map([[finalBlocks[0].index, answer.english]])) };
}

function buildRecentConversationSummary(ctx: any, maxStateChars: number): string | undefined {
	const branch = ctx?.sessionManager?.getBranch?.() ?? ctx?.sessionManager?.getEntries?.();
	if (!Array.isArray(branch)) return undefined;
	const messages = branch
		.map((entry: any) => entry?.message ?? (entry?.type === "message" ? entry : undefined))
		.filter((message: any) => message?.role === "user" || message?.role === "assistant")
		.slice(-6)
		.map((message: any) => {
			const content = typeof message.content === "string"
				? message.content
				: Array.isArray(message.content)
					? message.content.filter((part: any) => part?.type === "text" && typeof part.text === "string").map((part: any) => part.text).join("")
					: "";
			return content.trim() ? `${message.role}: ${content.trim().slice(0, 1200)}` : "";
		})
		.filter(Boolean);
	if (messages.length === 0) return undefined;
	const available = Math.max(0, maxStateChars - 32);
	if (available === 0) return undefined;
	const summary = messages.join("\n");
	return summary.length > available ? summary.slice(-available) : summary;
}

function buildJevResponseState(response: string): string {
	const withoutCode = response
		.replace(/```[\s\S]*?```/g, " __PI_ROUTER_PROTECTED_CODE__ ")
		.replace(/`[^`\n]+`/g, " __PI_ROUTER_PROTECTED_INLINE__ ");
	return maskProtectedSpans(withoutCode).text;
}

function describeJevError(error: unknown): string {
	const message = error instanceof Error ? error.message : String(error);
	const key = process.env.TYPESAFE_API_KEY;
	const redacted = key ? message.replaceAll(key, "[redacted]") : message;
	return redacted.replace(/\s+/g, " ").slice(0, 240) || "decision failed";
}

function renderRouterDetails(entry: RouterDetailsEntry): string {
	if (!entry.expanded) {
		return entry.summary;
	}
	const lines = [
		entry.summary,
		`original: ${entry.details.originalPrompt}`,
		`translated: ${entry.details.transformedPrompt}`,
		`routerModel: ${entry.details.routerModel}`,
		`workModel: ${entry.details.workModel}`,
		`profile: ${entry.details.profile} (${entry.details.profileSource})`,
		`profileModel: ${entry.details.profileModel}`,
		`thinking: ${entry.details.profileThinkingLevel}`,
	];
	if (entry.details.requestedProfile) lines.push(`requestedProfile: ${entry.details.requestedProfile}`);
	if (entry.details.requestedProfileModel) lines.push(`requestedProfileModel: ${entry.details.requestedProfileModel}`);
	if (entry.details.requestedProfileThinkingLevel) lines.push(`requestedThinking: ${entry.details.requestedProfileThinkingLevel}`);
	if (entry.details.effectiveModel) lines.push(`effectiveModel: ${entry.details.effectiveModel}`);
	if (entry.details.profileApplicationError) lines.push(`profileError: ${entry.details.profileApplicationError}`);
	if (entry.details.profileApplicationDeferred) lines.push("profileApplication: deferred to receiving turn");
	if (entry.details.inputTranslationOutcome) lines.push(`inputTranslation: ${entry.details.inputTranslationOutcome}`);
	if (entry.details.responseTranslationOutcome) lines.push(`responseTranslation: ${entry.details.responseTranslationOutcome}`);
	if (entry.details.jevInputRecommendation) lines.push(`jevInputRecommendation: ${entry.details.jevInputRecommendation}`);
	if (entry.details.jevResponseRecommendation) lines.push(`jevResponseRecommendation: ${entry.details.jevResponseRecommendation}`);
	if (entry.details.jevModel) lines.push(`jevModel: ${entry.details.jevModel}`);
	if (entry.details.jevDurationMs !== undefined) lines.push(`jevDurationMs: ${entry.details.jevDurationMs}`);
	if (entry.details.jevPolicyRevision) lines.push(`jevPolicy: ${entry.details.jevPolicyRevision}`);
	if (entry.details.jevCatalogRevision) lines.push(`jevCatalog: ${entry.details.jevCatalogRevision}`);
	if (entry.details.jevFallbackReasons?.length) lines.push(`jevFallback: ${entry.details.jevFallbackReasons.join("; ")}`);
	if (entry.details.effectiveThinkingLevel) lines.push(`effectiveThinking: ${entry.details.effectiveThinkingLevel}`);
	if (entry.details.englishAnswer) lines.push(`englishAnswer: ${entry.details.englishAnswer}`);
	if (entry.details.spanishAnswer) lines.push(`spanishAnswer: ${entry.details.spanishAnswer}`);
	if (entry.details.fallbackEvents?.length) lines.push(`fallback: ${entry.details.fallbackEvents.join("; ")}`);
	return lines.join("\n");
}

export default function piRouterExtension(pi: ExtensionAPI) {
	installPiRouter(pi, {});
}

interface PendingRoutedTurn {
	details?: RouterDetailsEntry;
	shouldTranslateFinalAnswer: boolean;
	rogerSpeech: boolean;
	jev?: JevDecisionClient;
}

interface ActiveAgentTurn {
	profileBoundaryHandled?: boolean;
	profileBoundaryFailed?: boolean;
	pending?: PendingRoutedTurn;
	carryPendingToNextTurn: boolean;
}

interface DeferredProfileApplication {
	profile: ModelProfileState;
	previous: ModelProfileState;
	ctx: any;
}

export function installPiRouter(pi: ExtensionAPI, dependencies: PiRouterDependencies = {}) {
	const stateStore = dependencies.stateStore ?? createFileRouterStateStore();
	const initialConfig = dependencies.config ?? DEFAULT_ROUTER_CONFIG;
	const pendingRoutedTurns: PendingRoutedTurn[] = [];
	const deferredProfileApplications: DeferredProfileApplication[] = [];
	let inputTail: Promise<void> | null = null;
	let messageEndTail: Promise<void> | null = null;
	let activeProfile = createDefaultModelProfileState();
	let lastDetails: RouterDetailsEntry | undefined;
	let activeAgentTurn: ActiveAgentTurn | undefined;
	let sawTurnLifecycleEvent = false;

	function serialize<T>(tail: "input" | "messageEnd", work: () => Promise<T>): Promise<T> {
		const previous = tail === "input" ? inputTail : messageEndTail;
		const result = previous ? previous.then(work) : work();
		const settled = result.then(() => undefined, () => undefined);
		if (tail === "input") {
			inputTail = settled;
			void settled.then(() => { if (inputTail === settled) inputTail = null; });
		} else {
			messageEndTail = settled;
			void settled.then(() => { if (messageEndTail === settled) messageEndTail = null; });
		}
		return result;
	}

	function readPersistedState(): RouterState | undefined {
		const persisted = stateStore.loadState() as RouterState | { state?: RouterState } | undefined;
		if (persisted === "on" || persisted === "off") return persisted;
		if (persisted?.state === "on" || persisted?.state === "off") return persisted.state;
		return undefined;
	}

	function refreshRouterSettingsFromStore(): RouterConfig {
		const persistedState = readPersistedState();
		if (persistedState !== undefined) config = { ...config, state: persistedState };
		return config;
	}

	const initialPersistedState = readPersistedState();
	let config: RouterConfig = { ...initialConfig, ...(initialPersistedState !== undefined ? { state: initialPersistedState } : {}) };
	let jevClient: JevDecisionClient | undefined = dependencies.jev;

	function configuredJevClient(): JevDecisionClient | undefined {
		const jevConfig = resolveJevConfig(config.jev);
		if (dependencies.jev) return dependencies.jev;
		if (!jevClient) {
			try {
				jevClient = createJevDecisionClient(jevConfig);
			} catch {
				return undefined;
			}
		}
		return jevClient;
	}

	function appendEntry(type: string, data: unknown): void {
		if (typeof (pi as any).appendEntry === "function") (pi as any).appendEntry(type, data);
	}

	function notify(ctx: any, message: string, level: "info" | "warning" | "error"): void {
		if (typeof ctx?.ui?.notify === "function") ctx.ui.notify(message, level);
		else if (typeof (pi as any).notify === "function") (pi as any).notify(message, level);
	}

	function clearAbandonedPendingTurn(): void {
		if (activeAgentTurn?.pending) {
			activeAgentTurn.pending = undefined;
			activeAgentTurn.carryPendingToNextTurn = false;
			return;
		}
		// Unit/RPC shims may omit turn lifecycle events. In that compatibility
		// mode, the oldest marker is the only marker that can represent this end.
		if (!sawTurnLifecycleEvent) pendingRoutedTurns.shift();
	}

	function markPendingTurnConsumed(pendingTurn: PendingRoutedTurn): void {
		if (activeAgentTurn?.pending === pendingTurn) {
			activeAgentTurn.pending = undefined;
			activeAgentTurn.carryPendingToNextTurn = false;
		}
	}

	function discardDeferredProfile(profile: ModelProfileState, ctx: any): void {
		for (let index = deferredProfileApplications.length - 1; index >= 0; index -= 1) {
			const deferred = deferredProfileApplications[index];
			if (deferred.ctx === ctx && deferred.profile.id === profile.id) {
				deferredProfileApplications.splice(index, 1);
				return;
			}
		}
	}

	async function applyNextDeferredProfile(ctx: any): Promise<boolean> {
		const deferred = deferredProfileApplications.shift();
		if (!deferred) return true;
		const application = await applyPiModelProfile(pi, ctx ?? deferred.ctx, deferred.profile, dependencies, deferred.previous);
		if (application.applied) return true;
		const message = `Pi router profile ${formatModelProfile(deferred.profile)} could not be applied at the receiving-turn boundary: ${application.error ?? "unknown error"}`;
		notify(ctx ?? deferred.ctx, message, "warning");
		(ctx ?? deferred.ctx)?.ui?.setStatus?.("pi-router", `router:${config.state} degraded`);
		(ctx ?? deferred.ctx)?.abort?.();
		(pi as any).abort?.();
		// The transformed prompt is already queued by the host, so remove its
		// marker and abort before the provider can receive it. Never substitute a
		// different profile after an explicit or automatic application failure.
		pendingRoutedTurns.shift();
		return false;
	}

	async function setRouterState(state: RouterConfig["state"], ctx: any): Promise<void> {
		refreshRouterSettingsFromStore();
		config = { ...config, state };
		stateStore.saveState(state);
		ctx?.ui?.setStatus?.("pi-router", `router:${config.state}`);
		if (state !== "on") return;
		activeProfile = createDefaultModelProfileState();

		const application = await applyPiModelProfile(pi, ctx, activeProfile, dependencies, activeProfile);
		if (!application.applied) {
			notify(ctx, `Pi router profile ${formatModelProfile(activeProfile)} could not be reapplied: ${application.error ?? "unknown error"}`, "warning");
			ctx?.ui?.setStatus?.("pi-router", `router:${config.state} degraded`);
		}
	}

	function showRouterDetails(ctx: any): void {
		if (!lastDetails) {
			notify(ctx, "No router details recorded yet", "info");
			return;
		}
		lastDetails = toggleRouterDetails(lastDetails);
		notify(ctx, renderRouterDetails(lastDetails), "info");
	}

	pi.registerCommand("router", {
		description: "Show or change Pi router status: /router, /router on, /router off",
		handler: async (args, ctx) => {
			refreshRouterSettingsFromStore();
			const command = args.trim().toLowerCase();
			if (command === "on") {
				await setRouterState("on", ctx);
				notify(ctx, "Pi router enabled", "info");
				return;
			}
			if (command === "off") {
				await setRouterState("off", ctx);
				notify(ctx, "Pi router disabled", "info");
				return;
			}
			if (command === "local" || command.startsWith("local ")) {
				notify(ctx, "Local router mode has been removed; Pi Router always uses the remote GPT mini model.", "warning");
				return;
			}
			notify(ctx, routerStatusSummary({ config, profile: activeProfile, workModel: selectedWorkModelFromPiContext(ctx) }), "info");
		},
	});

	pi.registerCommand("router-details", {
		description: "Expand or collapse Pi router details for the latest routed prompt",
		handler: async (_args, ctx) => showRouterDetails(ctx),
	});

	const shortcut = resolveDetailsShortcut(config.detailsShortcut).shortcut;
	if (typeof (pi as any).registerShortcut === "function") {
		(pi as any).registerShortcut(shortcut, {
			description: "Expand or collapse Pi router details",
			handler: async (ctx: any) => showRouterDetails(ctx),
		});
	}

	pi.on("session_start", async (event: any, ctx) => {
		refreshRouterSettingsFromStore();
		pendingRoutedTurns.length = 0;
		deferredProfileApplications.length = 0;
		activeAgentTurn = undefined;
		sawTurnLifecycleEvent = false;
		lastDetails = undefined;
		activeProfile = createDefaultModelProfileState();
		ctx?.ui?.setStatus?.("pi-router", `router:${config.state}`);
		if (config.state === "on") {
			const application = await applyPiModelProfile(pi, ctx, activeProfile, dependencies, activeProfile);
			if (!application.applied) {
				notify(ctx, `Pi router profile ${formatModelProfile(activeProfile)} could not be applied: ${application.error ?? "unknown error"}`, "warning");
				ctx?.ui?.setStatus?.("pi-router", `router:${config.state} degraded`);
			}
		}
	});

	// Markers are assigned to the host turn that actually receives the user
	// message. This keeps queued Roger markers from being consumed by an older
	// tool turn or by an unrelated assistant response.
	pi.on("turn_start", async (_event, ctx) => {
		sawTurnLifecycleEvent = true;
		const carriedPending = activeAgentTurn?.carryPendingToNextTurn ? activeAgentTurn.pending : undefined;
		activeAgentTurn = { pending: carriedPending, carryPendingToNextTurn: false };
		// A tool continuation keeps the originating turn's model. A queued
		// future prompt is applied only once that continuation has settled.
		if (!carriedPending) {
			activeAgentTurn.profileBoundaryHandled = true;
			activeAgentTurn.profileBoundaryFailed = !await applyNextDeferredProfile(ctx);
		}
	});

	pi.on("message_start", async (event: any, ctx) => {
		if (event.message?.role !== "user") return;
		sawTurnLifecycleEvent = true;
		if (!activeAgentTurn) activeAgentTurn = { carryPendingToNextTurn: false };
		if (activeAgentTurn.profileBoundaryFailed) return;
		if (!activeAgentTurn.pending && !activeAgentTurn.profileBoundaryHandled) {
			activeAgentTurn.profileBoundaryHandled = true;
			activeAgentTurn.profileBoundaryFailed = !await applyNextDeferredProfile(ctx);
			if (activeAgentTurn.profileBoundaryFailed) return;
		}
		if (!activeAgentTurn.pending) activeAgentTurn.pending = pendingRoutedTurns.shift();
	});

	pi.on("turn_end", async (event: any) => {
		const stopReason = event.message?.stopReason;
		if (stopReason === "aborted" || stopReason === "error") {
			clearAbandonedPendingTurn();
			return;
		}
		if (!activeAgentTurn) return;
		const hasToolResults = Array.isArray(event.toolResults) && event.toolResults.length > 0;
		if (hasToolResults) {
			activeAgentTurn.carryPendingToNextTurn = activeAgentTurn.pending !== undefined;
			return;
		}
		// A turn with no tool continuation ended without a routed final answer.
		// Clear only its assigned marker; queued future turns stay untouched.
		activeAgentTurn.pending = undefined;
		activeAgentTurn.carryPendingToNextTurn = false;
	});

	pi.on("agent_end", async (event: any) => {
		const stopReason = [...(Array.isArray(event.messages) ? event.messages : [])]
			.reverse()
			.find((message: any) => message?.role === "assistant")?.stopReason;
		if (activeAgentTurn?.pending) {
			clearAbandonedPendingTurn();
		} else if ((stopReason === "aborted" || stopReason === "error") && !sawTurnLifecycleEvent) {
			// Compatibility shims may expose only agent_end. Remove one marker for
			// that ended run while preserving any later queued markers.
			pendingRoutedTurns.shift();
		}
		activeAgentTurn = undefined;
	});

	// The visible final answer is Spanish, but the work model must receive the
	// original English assistant text on the next turn. Restore that text only
	// in the transient context payload; never mutate the visible session entry.
	pi.on("context", async (event: any, ctx: any) => {
		const branch = ctx?.sessionManager?.getBranch?.() ?? [];
		return { messages: restoreEnglishAssistantContext(event.messages, branch) };
	});

	pi.on("message_end", async (event, ctx) => serialize("messageEnd", async () => {
		if (event.message?.role !== "assistant") return;
		const stopReason = event.message.stopReason;
		if (stopReason === "aborted" || stopReason === "error") {
			clearAbandonedPendingTurn();
			return;
		}
		if (hasToolCallContent(event.message.content)) return;
		const phase = assistantMessagePhase(event.message);
		if (phase === "commentary") return;

		const pendingTurn = activeAgentTurn ? activeAgentTurn.pending : pendingRoutedTurns.shift();
		if (!pendingTurn) return;
		const detailsForTurn = pendingTurn.details;
		const finalBlocks = extractFinalTextBlocks(event.message);
		const finishDetails = (
			english: string,
			spanish: string,
			fallbackEvents?: string[],
			answerBlocks?: { english: string[]; spanish: string[] },
			responseTranslationOutcome?: "bypassed" | "performed" | "fallback",
			responseTranslationRecommendation?: string,
		) => {
			if (!detailsForTurn) return;
			const completed = extendRouterDetailsAfterCompletion(detailsForTurn, {
				englishAnswer: english,
				spanishAnswer: spanish,
				...(answerBlocks ? {
					englishAnswerBlocks: answerBlocks.english,
					spanishAnswerBlocks: answerBlocks.spanish,
				} : {}),
				assistantTimestamp: event.message.timestamp,
				effectiveThinkingLevel: typeof (pi as any).getThinkingLevel === "function" ? (pi as any).getThinkingLevel() : undefined,
				fallbackEvents,
				responseTranslationOutcome,
				jevResponseRecommendation: responseTranslationRecommendation,
			});
			if (lastDetails === detailsForTurn) lastDetails = completed;
			appendEntry("pi-router-details", completed);
		};

		if (finalBlocks.length === 0) {
			const diagnostic = "Pi router: final answer had unsupported content.";
			finishDetails(diagnostic, diagnostic, ["final answer translation skipped: unsupported message content"], undefined, "fallback");
			markPendingTurnConsumed(pendingTurn);
			return detailsForTurn ? { message: { ...event.message, content: replaceTextContent(event.message.content, diagnostic) } as typeof event.message } : undefined;
		}

		const englishBlocks = finalBlocks.map((block) => block.text);
		const englishAnswer = englishBlocks.join("");
		if (!englishAnswer.trim()) {
			const diagnostic = "Pi router: final answer was empty.";
			finishDetails(diagnostic, diagnostic, ["final answer translation skipped: empty answer"], englishBlocks.length > 1 ? { english: [diagnostic], spanish: [diagnostic] } : undefined, "fallback");
			markPendingTurnConsumed(pendingTurn);
			const replacements = new Map<number, string>(finalBlocks.map((block) => [block.index, diagnostic]));
			return detailsForTurn ? { message: { ...event.message, content: replaceFinalTextBlocks(event.message.content, replacements) } as typeof event.message } : undefined;
		}

		if (!pendingTurn.shouldTranslateFinalAnswer) {
			finishDetails(englishAnswer, englishAnswer, undefined, englishBlocks.length > 1 ? { english: englishBlocks, spanish: englishBlocks } : undefined, "bypassed");
			markPendingTurnConsumed(pendingTurn);
			return undefined;
		}

		let jevResponseBypass = false;
		let responseTranslationOutcome: "bypassed" | "performed" | "fallback" = "performed";
		let responseFallbackReason: string | undefined;
		let responseRecommendation: string | undefined;
		let responseCancelled = false;
		{
			if (!pendingTurn.jev) {
				responseFallbackReason = "response decision client unavailable";
				responseTranslationOutcome = "fallback";
			} else {
				try {
					const decision = await pendingTurn.jev.decideResponse(buildJevResponseState(englishAnswer), { signal: ctx?.signal });
					responseRecommendation = decision.translation;
					if (decision.translation === "not_required" && decision.canBypass) {
						jevResponseBypass = true;
						responseTranslationOutcome = "bypassed";
					} else if (decision.translation === "uncertain") {
						responseTranslationOutcome = "fallback";
						responseFallbackReason = "response translation decision uncertain";
					}
				} catch (error) {
					if (ctx?.signal?.aborted) {
						responseCancelled = true;
						responseTranslationOutcome = "fallback";
						responseFallbackReason = "response decision cancelled";
					} else {
						responseTranslationOutcome = "fallback";
						responseFallbackReason = `response decision failed: ${describeJevError(error)}`;
					}
				}
			}
		}
		if (responseCancelled) {
			finishDetails(englishAnswer, englishAnswer, responseFallbackReason ? [responseFallbackReason] : undefined, englishBlocks.length > 1 ? { english: englishBlocks, spanish: englishBlocks } : undefined, "fallback", responseRecommendation);
			markPendingTurnConsumed(pendingTurn);
			return undefined;
		}
		if (jevResponseBypass) {
			finishDetails(englishAnswer, englishAnswer, undefined, englishBlocks.length > 1 ? { english: englishBlocks, spanish: englishBlocks } : undefined, "bypassed", responseRecommendation);
			markPendingTurnConsumed(pendingTurn);
			if (!pendingTurn.rogerSpeech) return undefined;
			const replacements = new Map<number, string>();
			finalBlocks.forEach((block) => replacements.set(block.index, buildRogerSpeechResponse(block.text, block.text)));
			return { message: { ...event.message, content: replaceFinalTextBlocks(event.message.content, replacements) as any } };
		}

		const translate = dependencies.translateFinalAnswer
			?? ((answer: string, routerModel: RouterConfig["routerModel"], runtime: PiAiRuntime) => translateFinalAnswerToSpanish(answer, routerModel, runtime));
		const translatedBlocks: FinalAnswerTranslationResult[] = [];
		for (const block of finalBlocks) {
			translatedBlocks.push(await translate(block.text, config.routerModel, {
				modelRegistry: ctx?.modelRegistry,
				signal: ctx?.signal,
			}));
		}
		const translatedEnglishBlocks = translatedBlocks.map((translated) => translated.englishAnswer);
		const translatedSpanishBlocks = translatedBlocks.map((translated) => translated.spanishAnswer);
		const fallbackEvents = [
			...(responseFallbackReason ? [responseFallbackReason] : []),
			...translatedBlocks.flatMap((translated, index) => translated.degradedReason
				? [translatedBlocks.length > 1 ? `block ${index + 1}: ${translated.degradedReason}` : translated.degradedReason]
				: []),
		];
		finishDetails(
			translatedEnglishBlocks.join(""),
			translatedSpanishBlocks.join(""),
			fallbackEvents.length > 0 ? fallbackEvents : undefined,
			translatedBlocks.length > 1 ? { english: translatedEnglishBlocks, spanish: translatedSpanishBlocks } : undefined,
			responseTranslationOutcome,
			responseRecommendation,
		);
		if (translatedBlocks.some((translated) => translated.degradedReason)) {
			notify(ctx, `Pi router warning: ${fallbackEvents.join("; ")}; showing original or partially translated answer.`, "warning");
		}
		const replacements = new Map<number, string>();
		translatedBlocks.forEach((translated, index) => {
			const replacementText = pendingTurn.rogerSpeech
				? buildRogerSpeechResponse(translated.englishAnswer, translated.spanishAnswer)
				: translated.spanishAnswer;
			replacements.set(finalBlocks[index].index, replacementText);
		});
		markPendingTurnConsumed(pendingTurn);
		return {
			message: {
				...event.message,
				content: replaceFinalTextBlocks(event.message.content, replacements) as any,
			},
		};
	}));

	pi.on("input", async (event, ctx) => serialize("input", async () => {
		refreshRouterSettingsFromStore();
		const rogerSpeech = isRogerSpeechRequest(event);

		if (config.state === "on" && event.source !== "extension" && isNativeModelControl(event.text)) {
			notify(ctx, "Pi router controls the work model while enabled; use Use Astra: or Use Default:, or turn the router off.", "info");
			return { action: "handled" };
		}
		if (!shouldRouteInput({ text: event.text, source: event.source })) {
			return { action: "continue" };
		}

		if (config.state === "off") {
			if (rogerSpeech) pendingRoutedTurns.push({ shouldTranslateFinalAnswer: true, rogerSpeech: true, jev: configuredJevClient() });
			return { action: "continue" };
		}

		ctx?.ui?.setStatus?.("pi-router", "router:on routing...");
		const jevConfig = resolveJevConfig(config.jev);
		const recentConversationSummary = buildRecentConversationSummary(ctx, jevConfig.maxStateChars);
		const prepared = await prepareRoutedPrompt({
			prompt: event.text,
			config,
			context: recentConversationSummary ? { conversationSummary: recentConversationSummary } : undefined,
			workModel: selectedWorkModelFromPiContext(ctx),
			profileState: activeProfile,
			jev: configuredJevClient(),
			runtime: { modelRegistry: ctx?.modelRegistry, signal: ctx?.signal },
			routePrompt: dependencies.routePrompt
				?? ((prompt, routerModel, context, runtime) => routePromptWithModel(prompt, routerModel, context, runtime)),
			applyModelProfile: (profile, previous) => {
				if (activeAgentTurn && sawTurnLifecycleEvent) {
					deferredProfileApplications.push({ profile, previous, ctx });
					return { applied: true, deferred: true };
				}
				return applyPiModelProfile(pi, ctx, profile, dependencies, previous);
			},
		});

		if (prepared.action === "continue") {
			if (rogerSpeech) pendingRoutedTurns.push({ shouldTranslateFinalAnswer: true, rogerSpeech: true });
			return prepared.bypassed
				? { action: "transform", text: prepared.prompt }
				: { action: "continue" };
		}
		if (prepared.action === "handled") {
			discardDeferredProfile(prepared.profile, ctx);
			activeProfile = prepared.profile;
			lastDetails = prepared.details;
			appendEntry("pi-router-details", prepared.details);
			notify(ctx, prepared.message, "warning");
			ctx?.ui?.setStatus?.("pi-router", `router:${config.state} degraded`);
			return { action: "handled" };
		}

		activeProfile = prepared.profile;
		lastDetails = prepared.details;
		appendEntry("pi-router-details", prepared.details);
		pendingRoutedTurns.push({
			details: prepared.details,
			shouldTranslateFinalAnswer: rogerSpeech || prepared.result.sourceLanguage === "es" || prepared.result.sourceLanguage === "mixed"
				? true
				: prepared.result.translateFinalAnswer,
			rogerSpeech,
			jev: configuredJevClient(),
		});
		if (prepared.warning) notify(ctx, prepared.warning, "warning");
		ctx?.ui?.setStatus?.("pi-router", `router:${config.state} profile:${prepared.profile.label} thinking:${prepared.profile.thinkingLevel}${prepared.warning ? " degraded" : ""}`);
		return { action: "transform", text: prepared.prompt };
	}));
}
