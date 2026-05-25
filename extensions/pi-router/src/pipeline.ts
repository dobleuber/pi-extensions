import type { RouterConfig, WorkModelInfo } from "./config.ts";
import { resolveRouterState } from "./config.ts";
import { createRouterDetailsEntry, parseSinglePromptBypass, type RouterDetailsEntry } from "./details.ts";
import { createRouterMetadata, routePromptWithModel, type RouterContextOptions, type RouterModelResult } from "./router-model.ts";

export interface PrepareRoutedPromptInput {
	prompt: string;
	config: RouterConfig;
	workModel?: WorkModelInfo;
	context?: RouterContextOptions;
	routePrompt?: (prompt: string, config: RouterConfig["routerModel"], context?: RouterContextOptions) => Promise<RouterModelResult>;
}

export type PreparedRoutedPrompt =
	| { action: "continue"; prompt: string; bypassed?: boolean }
	| { action: "handled"; message: string; details: RouterDetailsEntry; result: RouterModelResult }
	| { action: "transform"; prompt: string; details: RouterDetailsEntry; result: RouterModelResult; warning?: string };

export async function prepareRoutedPrompt(input: PrepareRoutedPromptInput): Promise<PreparedRoutedPrompt> {
	const bypass = parseSinglePromptBypass(input.prompt);
	if (bypass.bypass) {
		return { action: "continue", prompt: bypass.prompt, bypassed: true };
	}

	const state = resolveRouterState(input.config);
	if (state.state === "off") {
		return { action: "continue", prompt: input.prompt };
	}

	const routePrompt = input.routePrompt ?? ((prompt, routerModel, context) => routePromptWithModel(prompt, routerModel, fetch as any, context));
	const result = await routePrompt(input.prompt, input.config.routerModel, input.context);
	const metadata = createRouterMetadata({
		originalPrompt: input.prompt,
		result,
		routerModel: input.config.routerModel,
	});
	const details = createRouterDetailsEntry(metadata, input.workModel);
	if (result.degradedReason) {
		if (input.config.routerModel.fallbackMode === "error") {
			return {
				action: "handled",
				message: `Pi router unavailable; prompt was not dispatched: ${result.degradedReason}`,
				details,
				result,
			};
		}
		if (input.config.routerModel.fallbackMode === "passthrough-with-warning") {
			return {
				action: "transform",
				prompt: input.prompt,
				warning: `Pi router warning: translation unavailable; dispatching original prompt. ${result.degradedReason}`,
				details,
				result,
			};
		}
	}

	return {
		action: "transform",
		prompt: result.englishPrompt,
		details,
		result,
	};
}
