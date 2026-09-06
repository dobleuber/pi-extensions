import { complete, type Api, type AssistantMessage, type Context, type Model, type ProviderHeaders, type UserMessage } from "@earendil-works/pi-ai/compat";
import type { RouterModelConfig } from "./config.ts";

/** The subset of Pi's host model registry needed by the router. */
export interface PiModelRegistryLike {
	find(provider: string, model: string): Model<Api> | undefined;
	getApiKeyAndHeaders(model: Model<Api>): Promise<{
		ok: true;
		apiKey?: string;
		headers?: ProviderHeaders;
	} | {
		ok: false;
		error: string;
	}>;
}

export type CompleteLike = typeof complete;

export interface PiAiRuntime {
	modelRegistry?: PiModelRegistryLike;
	complete?: CompleteLike;
	signal?: AbortSignal;
}

/**
 * Resolve the configured model and credentials through the host Pi registry,
 * then invoke the normal pi-ai provider adapter. The extension never builds an
 * endpoint URL or reads provider credentials itself.
 */
export async function completeWithPiRouterModel(
	config: RouterModelConfig,
	context: Context,
	runtime: PiAiRuntime = {},
): Promise<AssistantMessage> {
	const modelRegistry = runtime.modelRegistry;
	if (!modelRegistry) {
		throw new Error(`Pi model registry unavailable for ${config.provider}/${config.model}`);
	}

	const model = resolvePiRouterModel(config, modelRegistry);
	if (!model) {
		throw new Error(`Pi model not found: ${config.provider}/${config.model}`);
	}

	const auth = await modelRegistry.getApiKeyAndHeaders(model);
	if (!auth.ok) {
		throw new Error(auth.error);
	}

	return (runtime.complete ?? complete)(model, context, {
		apiKey: auth.apiKey,
		headers: auth.headers,
		...(runtime.signal ? { signal: runtime.signal } : {}),
		timeoutMs: config.timeoutMs,
		reasoningEffort: "none",
	});
}

export function resolvePiRouterModel(config: RouterModelConfig, modelRegistry: PiModelRegistryLike): Model<Api> | undefined {
	return modelRegistry.find(config.provider, config.model);
}

export function userMessage(text: string): UserMessage {
	return {
		role: "user",
		content: [{ type: "text", text }],
		timestamp: Date.now(),
	};
}

export function assistantText(response: AssistantMessage): string {
	if (response.stopReason === "error" || response.stopReason === "aborted") {
		throw new Error(response.errorMessage ?? `model stopped with ${response.stopReason}`);
	}
	return response.content
		.filter((content): content is { type: "text"; text: string } => content.type === "text")
		.map((content) => content.text)
		.join("\n");
}
