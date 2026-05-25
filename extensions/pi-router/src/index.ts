import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { DEFAULT_ROUTER_CONFIG, routerStatusSummary, type RouterConfig } from "./config.ts";
import { extendRouterDetailsAfterCompletion, resolveDetailsShortcut, toggleRouterDetails, type RouterDetailsEntry } from "./details.ts";
import { translateFinalAnswerToSpanish, type FinalAnswerTranslationResult } from "./final-answer.ts";
import { shouldRouteInput } from "./input.ts";
import { prepareRoutedPrompt, type PrepareRoutedPromptInput } from "./pipeline.ts";
import { createFileRouterStateStore, type RouterStateStore } from "./state.ts";
import { selectedWorkModelFromPiContext } from "./work-model.ts";

export interface PiRouterDependencies {
	config?: RouterConfig;
	routePrompt?: PrepareRoutedPromptInput["routePrompt"];
	translateFinalAnswer?: (answer: string, config: RouterConfig["routerModel"]) => Promise<FinalAnswerTranslationResult>;
	stateStore?: RouterStateStore;
}

function extractTextContent(content: unknown): string {
	if (typeof content === "string") return content;
	if (Array.isArray(content)) {
		return content
			.map((part) => part && typeof part === "object" && (part as any).type === "text" ? (part as any).text : "")
			.join("");
	}
	return "";
}

function replaceTextContent(content: unknown, text: string): unknown {
	if (typeof content === "string") return text;
	if (Array.isArray(content)) {
		let replaced = false;
		return content.map((part) => {
			if (!replaced && part && typeof part === "object" && (part as any).type === "text") {
				replaced = true;
				return { ...part, text };
			}
			return part;
		});
	}
	return [{ type: "text", text }];
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
		`thinking: ${entry.details.requestedThinkingLevel}`,
	];
	if (entry.details.effectiveThinkingLevel) lines.push(`effectiveThinking: ${entry.details.effectiveThinkingLevel}`);
	if (entry.details.englishAnswer) lines.push(`englishAnswer: ${entry.details.englishAnswer}`);
	if (entry.details.spanishAnswer) lines.push(`spanishAnswer: ${entry.details.spanishAnswer}`);
	if (entry.details.fallbackEvents?.length) lines.push(`fallback: ${entry.details.fallbackEvents.join("; ")}`);
	return lines.join("\n");
}

export default function piRouterExtension(pi: ExtensionAPI) {
	installPiRouter(pi, {});
}

export function installPiRouter(pi: ExtensionAPI, dependencies: PiRouterDependencies = {}) {
	const stateStore = dependencies.stateStore ?? createFileRouterStateStore();
	const persistedState = stateStore.loadState();
	let config: RouterConfig = { ...(dependencies.config ?? DEFAULT_ROUTER_CONFIG), ...(persistedState ? { state: persistedState } : {}) };
	let lastDetails: RouterDetailsEntry | undefined;

	function setRouterState(state: RouterConfig["state"], ctx: any) {
		config = { ...config, state };
		stateStore.saveState(state);
		ctx.ui.setStatus("pi-router", `router:${config.state}`);
	}

	function showRouterDetails(ctx: any) {
		if (!lastDetails) {
			ctx.ui.notify("No router details recorded yet", "info");
			return;
		}
		lastDetails = toggleRouterDetails(lastDetails);
		ctx.ui.notify(renderRouterDetails(lastDetails), "info");
	}

	pi.registerCommand("router", {
		description: "Show or change Pi router status: /router, /router on, /router off",
		handler: async (args, ctx) => {
			const command = args.trim().toLowerCase();
			if (command === "on") {
				setRouterState("on", ctx);
				ctx.ui.notify("Pi router enabled", "info");
				return;
			}
			if (command === "off") {
				setRouterState("off", ctx);
				ctx.ui.notify("Pi router disabled", "info");
				return;
			}
			ctx.ui.notify(routerStatusSummary({ config }), "info");
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

	pi.on("session_start", async (_event, ctx) => {
		ctx.ui.setStatus("pi-router", `router:${config.state}`);
	});

	pi.on("message_end", async (event, ctx) => {
		if (!lastDetails || event.message?.role !== "assistant") {
			return;
		}
		const englishAnswer = extractTextContent(event.message.content);
		if (!englishAnswer.trim()) {
			return;
		}
		const translate = dependencies.translateFinalAnswer
			?? ((answer: string, routerModel: RouterConfig["routerModel"]) => translateFinalAnswerToSpanish(answer, routerModel));
		const translated = await translate(englishAnswer, config.routerModel);
		lastDetails = extendRouterDetailsAfterCompletion(lastDetails, {
			englishAnswer: translated.englishAnswer,
			spanishAnswer: translated.spanishAnswer,
			effectiveThinkingLevel: typeof (pi as any).getThinkingLevel === "function" ? (pi as any).getThinkingLevel() : undefined,
			fallbackEvents: translated.degradedReason ? [translated.degradedReason] : undefined,
		});
		pi.appendEntry("pi-router-details", lastDetails);
		if (translated.degradedReason) {
			const warning = `Pi router warning: ${translated.degradedReason}; showing original answer.`;
			if (ctx?.ui?.notify) {
				ctx.ui.notify(warning, "warning");
			} else if (typeof (pi as any).notify === "function") {
				(pi as any).notify(warning, "warning");
			}
		}
		return {
			message: {
				...event.message,
				content: replaceTextContent(event.message.content, translated.spanishAnswer),
			},
		};
	});

	pi.on("input", async (event, ctx) => {
		if (!shouldRouteInput({ text: event.text, source: event.source })) {
			return { action: "continue" };
		}

		if (config.state === "on") {
			ctx.ui.setStatus("pi-router", "router:on routing...");
		}

		const prepared = await prepareRoutedPrompt({
			prompt: event.text,
			config,
			workModel: selectedWorkModelFromPiContext(ctx),
			routePrompt: dependencies.routePrompt,
		});

		if (prepared.action === "continue") {
			return { action: "continue" };
		}
		if (prepared.action === "handled") {
			lastDetails = prepared.details;
			pi.appendEntry("pi-router-details", prepared.details);
			ctx.ui.notify(prepared.message, "warning");
			ctx.ui.setStatus("pi-router", `router:${config.state} degraded`);
			return { action: "handled" };
		}

		pi.setThinkingLevel(prepared.result.thinkingLevel);
		lastDetails = prepared.details;
		pi.appendEntry("pi-router-details", prepared.details);
		if (prepared.warning) {
			ctx.ui.notify(prepared.warning, "warning");
		}
		ctx.ui.setStatus("pi-router", `router:${config.state} thinking:${prepared.result.thinkingLevel}${prepared.warning ? " degraded" : ""}`);
		return { action: "transform", text: prepared.prompt };
	});
}
