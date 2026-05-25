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
			"router:off routerModel:llama-cpp/gemma4 workModel:unknown",
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
		assert.deepEqual(statuses.at(-1), ["pi-router", "router:on thinking:medium"]);
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

		assert.deepEqual(commandResult, { action: "continue" });
		assert.deepEqual(routedResult, { action: "transform", text: "Improve the router." });
		assert.equal(appended[0][0], "pi-router-details");
		assert.equal(appended[0][1].expanded, false);
		assert.deepEqual(notifications, ["Pi router enabled"]);
	});
});
