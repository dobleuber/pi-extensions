import type { WorkModelInfo } from "./config.ts";

export interface WorkModelFailureClassification {
	type: "router" | "work-model";
	message: string;
}

export function selectedWorkModelFromPiContext(ctx: { model?: { provider?: string; id?: string; model?: string } | null }): WorkModelInfo {
	return {
		provider: ctx.model?.provider,
		model: ctx.model?.id ?? ctx.model?.model,
	};
}

export function formatWorkModel(workModel?: WorkModelInfo): string {
	if (!workModel?.provider && !workModel?.model) return "unknown";
	if (!workModel.provider) return workModel.model ?? "unknown";
	if (!workModel.model) return workModel.provider;
	return `${workModel.provider}/${workModel.model}`;
}

export function classifyWorkModelFailure(error: unknown): WorkModelFailureClassification {
	const message = error instanceof Error ? error.message : String(error);
	return {
		type: message.toLowerCase().includes("router model") ? "router" : "work-model",
		message,
	};
}
