import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { DEFAULT_ROUTER_CONFIG } from "../src/config.ts";
import piRouterExtension, { installPiRouter } from "../src/index.ts";

const DEFAULT_TEST_CONFIG = DEFAULT_ROUTER_CONFIG;

describe("pi-router extension entrypoint", () => {
	it("registers a router status command and session status indicator", async () => {
		const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<void> | void>>();
		const statuses: Array<[string, string | undefined]> = [];
		const notifications: string[] = [];
		const pi = {
			registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) {
				commands.set(name, command);
			},
			on(event: string, handler: (event: any, ctx: any) => Promise<void> | void) {
				handlers.set(event, [...(handlers.get(event) ?? []), handler]);
			},
		};

		installPiRouter(pi as any, { stateStore: { loadState: () => undefined, saveState() {} } });

		assert.ok(commands.has("router"));
		assert.equal(handlers.get("session_start")?.length, 1);
		assert.equal(handlers.get("input")?.length, 1);

		const ctx = {
			ui: {
				notify(message: string) {
					notifications.push(message);
				},
				setStatus(name: string, value: string | undefined) {
					statuses.push([name, value]);
				},
			},
		};
		await handlers.get("session_start")![0]({}, ctx);
		const inputResult = await handlers.get("input")![0]({ text: "/model", source: "interactive" }, ctx);
		await commands.get("router")!.handler("", ctx);

		assert.deepEqual(inputResult, { action: "continue" });
		assert.deepEqual(statuses, [["pi-router", "router:off"]]);
		assert.deepEqual(notifications, [
			"router:off profile:Luna Max profileSource:default profileModel:openai-codex/gpt-5.6-luna profileThinking:max routerModel:openai-codex/gpt-5.6-luna workModel:unknown",
		]);
	});

	it("registers a configurable router-details shortcut and command", async () => {
		const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
		const shortcuts = new Map<string, { handler: (ctx: any) => Promise<void> }>();
		const notifications: string[] = [];
		const pi = {
			registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) {
				commands.set(name, command);
			},
			on() {},
			registerShortcut(shortcut: string, options: { handler: (ctx: any) => Promise<void> }) {
				shortcuts.set(shortcut, options);
			},
		};
		const ctx = { ui: { notify(message: string) { notifications.push(message); }, setStatus() {} } };

		installPiRouter(pi as any, { config: { ...DEFAULT_TEST_CONFIG, detailsShortcut: "ctrl+alt+r" } as any });
		await commands.get("router-details")!.handler("", ctx);
		await shortcuts.get("ctrl+alt+r")!.handler(ctx);

		assert.ok(commands.has("router-details"));
		assert.ok(shortcuts.has("ctrl+alt+r"));
		assert.deepEqual(notifications, ["No router details recorded yet", "No router details recorded yet"]);
	});

	it("returns structured display and speech text for Roger speech requests", async () => {
		const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
		const pi = {
			registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) { commands.set(name, command); },
			on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
			setThinkingLevel() {},
			appendEntry() {},
		};
		const ctx = { ui: { notify() {}, setStatus() {} } };

		installPiRouter(pi as any, {
			routePrompt: async () => ({
				englishPrompt: "What time is it?",
				sourceLanguage: "es",
				thinkingLevel: "medium",
				translateFinalAnswer: true,
			}),
			translateFinalAnswer: async (answer: string) => ({
				englishAnswer: answer,
				spanishAnswer: "Son las ocho treinta y nueve y nueve cinco.",
			}),
		});
		await commands.get("router")!.handler("on", ctx);
		await handlers.get("input")![0]({
			text: "qué hora es",
			source: "roger",
			metadata: { source: "roger", speech: { enabled: true, language: "es" } },
		}, ctx);

		const result = await handlers.get("message_end")![0]({
			message: { role: "assistant", content: [{ type: "text", text: "It's 8:39 and 9:05." }] },
		}, ctx);

		const structured = JSON.parse(result.message.content[0].text);
		assert.deepEqual(structured, {
			display_text: "It's 8:39 and 9:05.",
			speech_text: "Son las ocho treinta y nueve y nueve cinco.",
			speech_language: "es",
			speech_source: "pi-router",
		});
	});

	it("naturalizes Roger speech responses even when prompt routing is off", async () => {
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
		const pi = {
			registerCommand() {},
			on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
			appendEntry() {},
			setThinkingLevel() {},
		};
		const ctx = { ui: { notify() {}, setStatus() {} } };
		let translatedInput = "";

		installPiRouter(pi as any, {
			stateStore: { loadState: () => "off", saveState() {} },
			translateFinalAnswer: async (answer: string) => {
				translatedInput = answer;
				return { englishAnswer: answer, spanishAnswer: "Son las diez y treinta." };
			},
		});
		await handlers.get("input")![0]({
			text: "qué hora es",
			source: "roger",
			metadata: { source: "roger", speech: { enabled: true, language: "es" } },
		}, ctx);

		const result = await handlers.get("message_end")![0]({
			message: { role: "assistant", content: [{ type: "text", text: "It's 10:30." }] },
		}, ctx);

		assert.equal(translatedInput, "It's 10:30.");
		assert.deepEqual(JSON.parse(result.message.content[0].text), {
			display_text: "It's 10:30.",
			speech_text: "Son las diez y treinta.",
			speech_language: "es",
			speech_source: "pi-router",
		});
	});

	it("translates final assistant messages and updates latest router details", async () => {
		const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
		const appended: Array<[string, any]> = [];
		const pi = {
			registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) { commands.set(name, command); },
			on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
			setThinkingLevel() {},
			appendEntry(type: string, data: any) { appended.push([type, data]); },
		};
		const ctx = { ui: { notify() {}, setStatus() {} } };

		installPiRouter(pi as any, {
			routePrompt: async () => ({
				englishPrompt: "Improve the router.",
				sourceLanguage: "es",
				thinkingLevel: "medium",
				translateFinalAnswer: true,
			}),
			translateFinalAnswer: async (answer: string) => ({
				englishAnswer: answer,
				spanishAnswer: "Listo.",
			}),
		});
		await commands.get("router")!.handler("on", ctx);
		await handlers.get("input")![0]({ text: "mejora el router", source: "interactive" }, ctx);

		const result = await handlers.get("message_end")![0]({ message: { role: "assistant", content: [{ type: "text", text: "Done." }] } }, ctx);

		assert.deepEqual(result.message.content, [{ type: "text", text: "Listo." }]);
		assert.equal(appended.at(-1)![0], "pi-router-details");
		assert.equal(appended.at(-1)![1].phase, "complete");
		assert.equal(appended.at(-1)![1].details.englishAnswer, "Done.");
		assert.equal(appended.at(-1)![1].details.spanishAnswer, "Listo.");
	});

	it("translates only final Codex text blocks and restores them in transient context", async () => {
		const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
		const appended: Array<[string, any]> = [];
		const translatedInputs: string[] = [];
		const pi = {
			registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) { commands.set(name, command); },
			on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
			setThinkingLevel() {},
			appendEntry(type: string, data: any) { appended.push([type, data]); },
		};
		const ctx = { ui: { notify() {}, setStatus() {} } };
		const signature = (id: string, phase: "commentary" | "final_answer") => JSON.stringify({ v: 1, id, phase });

		installPiRouter(pi as any, {
			routePrompt: async () => ({
				englishPrompt: "Improve the router.",
				sourceLanguage: "es",
				thinkingLevel: "medium",
				translateFinalAnswer: true,
			}),
			translateFinalAnswer: async (answer: string) => {
				translatedInputs.push(answer);
				return { englishAnswer: answer, spanishAnswer: "Listo." };
			},
		});
		await commands.get("router")!.handler("on", ctx);
		await handlers.get("input")![0]({ text: "mejora el router", source: "interactive" }, ctx);

		const message = {
			role: "assistant",
			phase: "final_answer",
			timestamp: 42,
			content: [
				{ type: "text", text: "I am checking the change.", textSignature: signature("commentary-1", "commentary") },
				{ type: "thinking", thinking: "internal reasoning" },
				{ type: "text", text: "Done.", textSignature: signature("final-1", "final_answer") },
			],
		};
		const result = await handlers.get("message_end")![0]({ message }, ctx);

		assert.deepEqual(translatedInputs, ["Done."]);
		assert.deepEqual(result.message.content, [
			{ type: "text", text: "I am checking the change.", textSignature: signature("commentary-1", "commentary") },
			{ type: "thinking", thinking: "internal reasoning" },
			{ type: "text", text: "Listo.", textSignature: signature("final-1", "final_answer") },
		]);
		assert.equal(appended.at(-1)![1].details.englishAnswer, "Done.");

		const branch = appended
			.filter(([type]) => type === "pi-router-details")
			.map(([, data]) => ({ type: "custom", customType: "pi-router-details", data }));
		const contextResult = await handlers.get("context")![0]({ messages: [result.message] }, {
			sessionManager: { getBranch: () => branch },
		});
		assert.deepEqual(contextResult.messages[0].content, message.content);
	});

	it("translates multiple final blocks without unsupported-content replacement", async () => {
		const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
		const translatedInputs: string[] = [];
		const pi = {
			registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) { commands.set(name, command); },
			on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
			setThinkingLevel() {},
			appendEntry() {},
		};
		const ctx = { ui: { notify() {}, setStatus() {} } };
		const signature = (id: string, phase: "commentary" | "final_answer") => JSON.stringify({ v: 1, id, phase });

		installPiRouter(pi as any, {
			routePrompt: async () => ({ englishPrompt: "Do it.", sourceLanguage: "es", thinkingLevel: "medium", translateFinalAnswer: true }),
			translateFinalAnswer: async (answer: string) => {
				translatedInputs.push(answer);
				return { englishAnswer: answer, spanishAnswer: answer === "First." ? "Primero." : "Segundo." };
			},
		});
		await commands.get("router")!.handler("on", ctx);
		await handlers.get("input")![0]({ text: "hazlo", source: "interactive" }, ctx);

		const result = await handlers.get("message_end")![0]({
			message: {
				role: "assistant",
				phase: "final_answer",
				timestamp: 43,
				content: [
					{ type: "text", text: "Progress note.", textSignature: signature("commentary-2", "commentary") },
					{ type: "image", source: "unchanged" },
					{ type: "text", text: "First.", textSignature: signature("final-2a", "final_answer") },
					{ type: "thinking", thinking: "keep me" },
					{ type: "text", text: "Second.", textSignature: signature("final-2b", "final_answer") },
					{ type: "text", text: "unsigned unrelated text" },
				],
			},
		}, ctx);

		assert.deepEqual(translatedInputs, ["First.", "Second."]);
		assert.deepEqual(result.message.content, [
			{ type: "text", text: "Progress note.", textSignature: signature("commentary-2", "commentary") },
			{ type: "image", source: "unchanged" },
			{ type: "text", text: "Primero.", textSignature: signature("final-2a", "final_answer") },
			{ type: "thinking", thinking: "keep me" },
			{ type: "text", text: "Segundo.", textSignature: signature("final-2b", "final_answer") },
			{ type: "text", text: "unsigned unrelated text" },
		]);
		assert.ok(!JSON.stringify(result.message.content).includes("unsupported content"));
	});

	it("keeps tool-call assistant messages untouched until their final response", async () => {
		const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
		const translatedInputs: string[] = [];
		const pi = {
			registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) { commands.set(name, command); },
			on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
			setThinkingLevel() {},
			appendEntry() {},
		};
		const ctx = { ui: { notify() {}, setStatus() {} } };

		installPiRouter(pi as any, {
			routePrompt: async () => ({ englishPrompt: "Use the tool.", sourceLanguage: "es", thinkingLevel: "medium", translateFinalAnswer: true }),
			translateFinalAnswer: async (answer: string) => {
				translatedInputs.push(answer);
				return { englishAnswer: answer, spanishAnswer: "Hecho." };
			},
		});
		await commands.get("router")!.handler("on", ctx);
		await handlers.get("input")![0]({ text: "usa la herramienta", source: "interactive" }, ctx);

		const toolMessage = { role: "assistant", content: [
			{ type: "text", text: "Calling the tool." },
			{ type: "toolCall", id: "call-1", name: "read", arguments: {} },
		] };
		assert.equal(await handlers.get("message_end")![0]({ message: toolMessage }, ctx), undefined);
		const finalResult = await handlers.get("message_end")![0]({
			message: { role: "assistant", content: [{ type: "text", text: "Done." }] },
		}, ctx);

		assert.deepEqual(translatedInputs, ["Done."]);
		assert.deepEqual(finalResult.message.content, [{ type: "text", text: "Hecho." }]);
	});

	it("keeps simple string assistant content compatible with unsigned text", async () => {
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
		const pi = {
			registerCommand() {},
			on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
			appendEntry() {},
			setThinkingLevel() {},
		};
		const ctx = { ui: { notify() {}, setStatus() {} } };
		installPiRouter(pi as any, {
			stateStore: { loadState: () => "off", saveState() {} },
			translateFinalAnswer: async (answer: string) => ({ englishAnswer: answer, spanishAnswer: "Listo." }),
		});
		await handlers.get("input")![0]({
			text: "hola",
			source: "roger",
			metadata: { source: "roger", speech: { enabled: true, language: "es" } },
		}, ctx);

		const result = await handlers.get("message_end")![0]({ message: { role: "assistant", content: "Done." } }, ctx);
		assert.deepEqual(JSON.parse(result.message.content), {
			display_text: "Done.",
			speech_text: "Listo.",
			speech_language: "es",
			speech_source: "pi-router",
		});
	});

	it("does not leave a Roger marker after a handled native command", async () => {
		const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
		let translationCalls = 0;
		const pi = {
			registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) { commands.set(name, command); },
			on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
			appendEntry() {},
			setThinkingLevel() {},
		};
		const ctx = { ui: { notify() {}, setStatus() {} } };
		installPiRouter(pi as any, {
			translateFinalAnswer: async (answer: string) => {
				translationCalls += 1;
				return { englishAnswer: answer, spanishAnswer: "No debe aparecer." };
			},
		});
		await commands.get("router")!.handler("on", ctx);

		assert.deepEqual(await handlers.get("input")![0]({
			text: "/model",
			source: "roger",
			metadata: { source: "roger", speech: { enabled: true } },
		}, ctx), { action: "handled" });
		assert.equal(await handlers.get("message_end")![0]({
			message: { role: "assistant", content: [{ type: "text", text: "Unrelated answer." }] },
		}, ctx), undefined);
		assert.equal(translationCalls, 0);
	});

	it("clears an aborted turn marker without consuming a future queued Roger turn", async () => {
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
		const translatedInputs: string[] = [];
		const pi = {
			registerCommand() {},
			on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
			appendEntry() {},
			setThinkingLevel() {},
		};
		const ctx = { ui: { notify() {}, setStatus() {} } };
		installPiRouter(pi as any, {
			stateStore: { loadState: () => "off", saveState() {} },
			translateFinalAnswer: async (answer: string) => {
				translatedInputs.push(answer);
				return { englishAnswer: answer, spanishAnswer: "Segundo." };
			},
		});
		const rogerInput = (text: string) => handlers.get("input")![0]({
			text,
			source: "roger",
			metadata: { source: "roger", speech: { enabled: true, language: "es" } },
		}, ctx);

		await rogerInput("primero");
		await handlers.get("turn_start")![0]({}, ctx);
		await handlers.get("message_start")![0]({ message: { role: "user", content: [{ type: "text", text: "primero" }] } }, ctx);
		await rogerInput("segundo");
		const aborted = { role: "assistant", stopReason: "aborted", content: [{ type: "text", text: "" }] };
		assert.equal(await handlers.get("message_end")![0]({ message: aborted }, ctx), undefined);
		await handlers.get("turn_end")![0]({ message: aborted, toolResults: [] }, ctx);
		await handlers.get("agent_end")![0]({ messages: [aborted] }, ctx);

		await handlers.get("turn_start")![0]({}, ctx);
		await handlers.get("message_start")![0]({ message: { role: "user", content: [{ type: "text", text: "segundo" }] } }, ctx);
		const result = await handlers.get("message_end")![0]({
			message: { role: "assistant", content: [{ type: "text", text: "Second answer." }] },
		}, ctx);

		assert.deepEqual(translatedInputs, ["Second answer."]);
		assert.deepEqual(JSON.parse(result.message.content[0].text), {
			display_text: "Second answer.",
			speech_text: "Segundo.",
			speech_language: "es",
			speech_source: "pi-router",
		});
	});

	it("clears a normally ended turn with no final answer before the next Roger turn", async () => {
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
		const translatedInputs: string[] = [];
		const pi = {
			registerCommand() {},
			on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
			appendEntry() {},
			setThinkingLevel() {},
		};
		const ctx = { ui: { notify() {}, setStatus() {} } };
		installPiRouter(pi as any, {
			stateStore: { loadState: () => "off", saveState() {} },
			translateFinalAnswer: async (answer: string) => {
				translatedInputs.push(answer);
				return { englishAnswer: answer, spanishAnswer: "Hecho." };
			},
		});
		const rogerInput = (text: string) => handlers.get("input")![0]({
			text,
			source: "roger",
			metadata: { source: "roger", speech: { enabled: true, language: "es" } },
		}, ctx);

		await rogerInput("primero");
		await handlers.get("turn_start")![0]({}, ctx);
		await handlers.get("message_start")![0]({ message: { role: "user", content: [{ type: "text", text: "primero" }] } }, ctx);
		await rogerInput("segundo");
		const commentary = {
			role: "assistant",
			content: [{ type: "text", text: "Only commentary.", textSignature: JSON.stringify({ v: 1, id: "commentary-only", phase: "commentary" }) }],
		};
		assert.equal(await handlers.get("message_end")![0]({ message: commentary }, ctx), undefined);
		await handlers.get("turn_end")![0]({ message: commentary, toolResults: [] }, ctx);
		await handlers.get("agent_end")![0]({ messages: [commentary] }, ctx);

		await handlers.get("turn_start")![0]({}, ctx);
		await handlers.get("message_start")![0]({ message: { role: "user", content: [{ type: "text", text: "segundo" }] } }, ctx);
		const result = await handlers.get("message_end")![0]({
			message: { role: "assistant", content: [{ type: "text", text: "Next answer." }] },
		}, ctx);

		assert.deepEqual(translatedInputs, ["Next answer."]);
		assert.deepEqual(JSON.parse(result.message.content[0].text), {
			display_text: "Next answer.",
			speech_text: "Hecho.",
			speech_language: "es",
			speech_source: "pi-router",
		});
	});

	it("warns and dispatches the original prompt when router model fallback occurs", async () => {
		const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
		const notifications: string[] = [];
		const pi = {
			registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) { commands.set(name, command); },
			on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
			appendEntry() {},
			setThinkingLevel() {},
		};
		const ctx = { ui: { notify(message: string) { notifications.push(message); }, setStatus() {} } };

		installPiRouter(pi as any, {
			routePrompt: async (prompt: string) => ({
				englishPrompt: prompt,
				sourceLanguage: "unknown",
				thinkingLevel: "medium",
				translateFinalAnswer: false,
				degradedReason: "router model unavailable: timeout",
			}),
		});
		await commands.get("router")!.handler("on", ctx);

		const result = await handlers.get("input")![0]({ text: "Dame el estado actual del router", source: "interactive" }, ctx);

		assert.deepEqual(result, { action: "transform", text: "Dame el estado actual del router" });
		assert.match(notifications.at(-1)!, /translation unavailable; dispatching original prompt/);
	});

	it("handles strict router model failure without dispatching the original Spanish prompt", async () => {
		const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
		const notifications: string[] = [];
		const pi = {
			registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) { commands.set(name, command); },
			on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
			appendEntry() {},
			setThinkingLevel() {},
		};
		const ctx = { ui: { notify(message: string) { notifications.push(message); }, setStatus() {} } };

		installPiRouter(pi as any, {
			config: { ...DEFAULT_TEST_CONFIG, routerModel: { ...DEFAULT_TEST_CONFIG.routerModel, fallbackMode: "error" } },
			routePrompt: async (prompt: string) => ({
				englishPrompt: prompt,
				sourceLanguage: "unknown",
				thinkingLevel: "medium",
				translateFinalAnswer: false,
				degradedReason: "router model unavailable: timeout",
			}),
		});
		await commands.get("router")!.handler("on", ctx);

		const result = await handlers.get("input")![0]({ text: "Dame el estado actual del router", source: "interactive" }, ctx);

		assert.deepEqual(result, { action: "handled" });
		assert.match(notifications.at(-1)!, /router model unavailable: timeout/);
	});

	it("shows immediate routing feedback before waiting for the router model", async () => {
		const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
		const statuses: Array<[string, string]> = [];
		let resolveRoute!: (value: any) => void;
		const routeStarted = new Promise<void>((resolve) => {
			const pi = {
				registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) { commands.set(name, command); },
				on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
				setThinkingLevel() {},
				appendEntry() {},
			};
			installPiRouter(pi as any, {
				routePrompt: async () => {
					resolve();
					return await new Promise((routeResolve) => { resolveRoute = routeResolve; });
				},
			});
		});
		const ctx = { ui: { notify() {}, setStatus(name: string, value: string) { statuses.push([name, value]); } } };
		await commands.get("router")!.handler("on", ctx);

		const pending = handlers.get("input")![0]({ text: "mejora el router", source: "interactive" }, ctx);
		await routeStarted;

		assert.deepEqual(statuses.at(-1), ["pi-router", "router:on routing..."]);

		resolveRoute({
			englishPrompt: "Improve the router.",
			sourceLanguage: "es",
			thinkingLevel: "medium",
			translateFinalAnswer: true,
		});
		const result = await pending;

		assert.deepEqual(result, { action: "transform", text: "Improve the router." });
		assert.deepEqual(statuses.at(-1), ["pi-router", "router:on profile:Luna Max thinking:max"]);
	});

	it("persists router state changes and restores them in new sessions", async () => {
		const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<void> | void>>();
		const savedStates: string[] = [];
		const statuses: Array<[string, string | undefined]> = [];
		const notifications: string[] = [];
		const pi = {
			registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) { commands.set(name, command); },
			on(event: string, handler: (event: any, ctx: any) => Promise<void> | void) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
		};
		const ctx = {
			ui: {
				notify(message: string) { notifications.push(message); },
				setStatus(name: string, value: string | undefined) { statuses.push([name, value]); },
			},
		};

		installPiRouter(pi as any, {
			stateStore: {
				loadState: () => "on",
				saveState: (state) => { savedStates.push(state); },
			},
		});

		await handlers.get("session_start")![0]({}, ctx);
		await commands.get("router")!.handler("off", ctx);
		await commands.get("router")!.handler("on", ctx);

		assert.deepEqual(statuses[0], ["pi-router", "router:on"]);
		assert.deepEqual(savedStates, ["off", "on"]);
		assert.deepEqual(notifications, ["Pi router disabled", "Pi router enabled"]);
	});

	it("can turn routing on and transform normal input while keeping commands untouched", async () => {
		const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
		const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
		const appended: Array<[string, any]> = [];
		const pi = {
			registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) {
				commands.set(name, command);
			},
			on(event: string, handler: (event: any, ctx: any) => Promise<any>) {
				handlers.set(event, [...(handlers.get(event) ?? []), handler]);
			},
			setThinkingLevel(_level: string) {},
			getThinkingLevel() { return "medium"; },
			appendEntry(type: string, data: any) { appended.push([type, data]); },
		};
		const notifications: string[] = [];
		const ctx = {
			ui: {
				notify(message: string) { notifications.push(message); },
				setStatus() {},
			},
		};

		installPiRouter(pi as any, {
			routePrompt: async () => ({
				englishPrompt: "Improve the router.",
				sourceLanguage: "es",
				thinkingLevel: "medium",
				translateFinalAnswer: true,
			}),
		});
		await commands.get("router")!.handler("on", ctx);

		const commandResult = await handlers.get("input")![0]({ text: "/model", source: "interactive" }, ctx);
		const routedResult = await handlers.get("input")![0]({ text: "mejora el router", source: "interactive" }, ctx);

		assert.deepEqual(commandResult, { action: "handled" });
		assert.deepEqual(routedResult, { action: "transform", text: "Improve the router." });
		assert.equal(appended[0][0], "pi-router-details");
		assert.equal(appended[0][1].expanded, false);
		assert.deepEqual(notifications, [
			"Pi router enabled",
			"Pi router controls the work model while enabled; use Use Astra: or Use Default:, or turn the router off.",
		]);
	});

	describe("session-scoped model profiles", () => {
		it("applies explicit Astra, retains it across prompts and router toggles, and resets to Luna", async () => {
			const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
			const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
			const routedPrompts: string[] = [];
			let currentModel: any = { provider: "openai-codex", id: "gpt-5.6-luna" };
			let currentThinking = "max";
			const pi = {
				registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) { commands.set(name, command); },
				on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
				setModel(model: any) { currentModel = model; return Promise.resolve(true); },
				getThinkingLevel() { return currentThinking; },
				setThinkingLevel(level: string) { currentThinking = level; },
				appendEntry() {},
			};
			const ctx: any = {
				get model() { return currentModel; },
				modelRegistry: {
					find(provider: string, model: string) {
						return { provider, id: model };
					},
				},
				ui: { notify() {}, setStatus() {} },
			};

			installPiRouter(pi as any, {
				stateStore: { loadState: () => undefined, saveState() {} },
				routePrompt: async (prompt: string) => {
					routedPrompts.push(prompt);
					return {
						englishPrompt: `English: ${prompt}`,
						sourceLanguage: "es",
						thinkingLevel: "low",
						translateFinalAnswer: true,
					};
				},
			});
			await commands.get("router")!.handler("on", ctx);

			const first = await handlers.get("input")![0]({ text: "Use Astra: arregla esto", source: "interactive" }, ctx);
			assert.deepEqual(first, { action: "transform", text: "English: arregla esto" });
			assert.deepEqual(currentModel, { provider: "openai-codex", id: "gpt-6-astra" });
			assert.equal(currentThinking, "high");

			await handlers.get("input")![0]({ text: "continúa la investigación", source: "interactive" }, ctx);
			assert.deepEqual(currentModel, { provider: "openai-codex", id: "gpt-6-astra" });
			assert.equal(currentThinking, "high");

			await commands.get("router")!.handler("off", ctx);
			currentModel = { provider: "native", id: "native-model" };
			currentThinking = "low";
			await commands.get("router")!.handler("on", ctx);
			assert.deepEqual(currentModel, { provider: "openai-codex", id: "gpt-6-astra" });
			assert.equal(currentThinking, "high");
			await handlers.get("input")![0]({ text: "sigue con eso", source: "interactive" }, ctx);
			assert.deepEqual(currentModel, { provider: "openai-codex", id: "gpt-6-astra" });
			assert.equal(currentThinking, "high");

			const reset = await handlers.get("input")![0]({ text: "Usa el modelo predeterminado: termina", source: "interactive" }, ctx);
			assert.deepEqual(reset, { action: "transform", text: "English: termina" });
			assert.deepEqual(currentModel, { provider: "openai-codex", id: "gpt-5.6-luna" });
			assert.equal(currentThinking, "max");
			assert.deepEqual(routedPrompts, ["arregla esto", "continúa la investigación", "sigue con eso", "termina"]);
		});

		it("applies model profiles without reading or writing global settings", async () => {
			const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
			const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
			let settingsReads = 0;
			let settingsWrites = 0;
			let currentModel: any = { provider: "openai-codex", id: "gpt-5.6-luna" };
			let currentThinking = "max";
			const pi = {
				registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) { commands.set(name, command); },
				on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
				getSettings() { settingsReads += 1; return { model: "global-model", thinkingLevel: "minimal" }; },
				setSettings() { settingsWrites += 1; },
				setModel(model: any) { currentModel = model; return true; },
				getThinkingLevel() { return currentThinking; },
				setThinkingLevel(level: string) { currentThinking = level; },
				appendEntry() {},
			};
			const ctx: any = {
				get model() { return currentModel; },
				modelRegistry: { find(provider: string, model: string) { return { provider, id: model }; } },
				ui: { notify() {}, setStatus() {} },
			};

			installPiRouter(pi as any, {
				stateStore: { loadState: () => "on", saveState() {} },
				routePrompt: async (prompt: string) => ({ englishPrompt: prompt, sourceLanguage: "unknown", thinkingLevel: "high", translateFinalAnswer: false }),
			});
			await handlers.get("session_start")![0]({ reason: "new" }, ctx);
			await handlers.get("input")![0]({ text: "Use Astra: hazlo", source: "interactive" }, ctx);
			await commands.get("router")!.handler("off", ctx);

			assert.equal(settingsReads, 0);
			assert.equal(settingsWrites, 0);
		});

		it("restores a selected profile when resuming the same session", async () => {
			const sessionEntries: any[] = [];
			const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
			const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
			let currentModel: any = { provider: "openai-codex", id: "gpt-5.6-luna" };
			let currentThinking = "max";
			const makePi = () => ({
				registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) { commands.set(name, command); },
				on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
				setModel(model: any) { currentModel = model; return Promise.resolve(true); },
				getThinkingLevel() { return currentThinking; },
				setThinkingLevel(level: string) { currentThinking = level; },
				appendEntry(type: string, data: any) {
					if (type === "pi-router-profile") sessionEntries.push({ type: "custom", customType: type, data });
				},
			});
			const makeContext = (sessionId: string) => ({
				get model() { return currentModel; },
				modelRegistry: { find(provider: string, model: string) { return { provider, id: model }; } },
				sessionManager: { getSessionId: () => sessionId, getEntries: () => sessionEntries },
				ui: { notify() {}, setStatus() {} },
			});
			const dependencies = {
				stateStore: { loadState: () => "on" as const, saveState() {} },
				routePrompt: async (prompt: string) => ({ englishPrompt: prompt, sourceLanguage: "unknown" as const, thinkingLevel: "low" as const, translateFinalAnswer: false }),
			};

			installPiRouter(makePi() as any, dependencies);
			const firstContext = makeContext("session-1");
			await handlers.get("session_start")![0]({ reason: "new" }, firstContext);
			await handlers.get("input")![0]({ text: "Use Astra: investiga esto", source: "interactive" }, firstContext);
			assert.equal(sessionEntries.length, 1);

			installPiRouter(makePi() as any, dependencies);
			const resumedContext = makeContext("session-1");
			await handlers.get("session_start")![1]({ reason: "resume" }, resumedContext);
			assert.deepEqual(currentModel, { provider: "openai-codex", id: "gpt-6-astra" });
			assert.equal(currentThinking, "high");
		});

		it("gates native model commands only while routing is enabled", async () => {
			const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
			const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
			const pi = {
				registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) { commands.set(name, command); },
				on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
				appendEntry() {},
			};
			const ctx = { ui: { notify() {}, setStatus() {} } };
			installPiRouter(pi as any, { stateStore: { loadState: () => undefined, saveState() {} } });
			await commands.get("router")!.handler("on", ctx);

			assert.deepEqual(await handlers.get("input")![0]({ text: "/model", source: "interactive" }, ctx), { action: "handled" });
			assert.deepEqual(await handlers.get("input")![0]({ text: "/thinking high", source: "interactive" }, ctx), { action: "handled" });
			assert.deepEqual(await handlers.get("input")![0]({ text: "/model", source: "extension" }, ctx), { action: "continue" });

			await commands.get("router")!.handler("off", ctx);
			assert.deepEqual(await handlers.get("input")![0]({ text: "/model", source: "interactive" }, ctx), { action: "continue" });
			assert.deepEqual(await handlers.get("input")![0]({ text: "/thinking high", source: "interactive" }, ctx), { action: "continue" });
		});

		it("does not fall back to another profile when Astra cannot be resolved", async () => {
			const handlers = new Map<string, Array<(event: any, ctx: any) => Promise<any>>>();
			const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
			const notifications: string[] = [];
			let routeCalls = 0;
			let currentModel: any = { provider: "openai-codex", id: "gpt-5.6-luna" };
			const pi = {
				registerCommand(name: string, command: { handler: (args: string, ctx: any) => Promise<void> }) { commands.set(name, command); },
				on(event: string, handler: (event: any, ctx: any) => Promise<any>) { handlers.set(event, [...(handlers.get(event) ?? []), handler]); },
				setModel(model: any) { currentModel = model; return Promise.resolve(true); },
				setThinkingLevel() {},
				getThinkingLevel() { return "max"; },
				appendEntry() {},
			};
			const ctx: any = {
				get model() { return currentModel; },
				modelRegistry: {
					find(provider: string, model: string) {
						return provider === "openai-codex" && model === "gpt-5.6-luna" ? { provider, id: model } : undefined;
					},
				},
				ui: { notify(message: string) { notifications.push(message); }, setStatus() {} },
			};

			installPiRouter(pi as any, {
				stateStore: { loadState: () => undefined, saveState() {} },
				routePrompt: async (prompt: string) => {
					routeCalls += 1;
					return { englishPrompt: prompt, sourceLanguage: "unknown", thinkingLevel: "high", translateFinalAnswer: false };
				},
			});
			await commands.get("router")!.handler("on", ctx);

			const failed = await handlers.get("input")![0]({ text: "Use Astra: hazlo", source: "interactive" }, ctx);
			assert.deepEqual(failed, { action: "handled" });
			assert.equal(routeCalls, 0);
			assert.match(notifications.at(-1)!, /gpt-6-astra/);

			const retry = await handlers.get("input")![0]({ text: "hazlo", source: "interactive" }, ctx);
			assert.deepEqual(retry, { action: "transform", text: "hazlo" });
			assert.equal(routeCalls, 1);
			assert.deepEqual(currentModel, { provider: "openai-codex", id: "gpt-5.6-luna" });
		});
	});
});
