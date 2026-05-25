import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { homedir } from "node:os";
import type { RouterState } from "./config.ts";

export interface RouterStateStore {
	loadState(): RouterState | undefined;
	saveState(state: RouterState): void;
}

export function createFileRouterStateStore(
	path = join(homedir(), ".pi", "agent", "extensions", "pi-router", "router-state.json"),
): RouterStateStore {
	return {
		loadState() {
			try {
				if (!existsSync(path)) return undefined;
				const payload = JSON.parse(readFileSync(path, "utf8"));
				return payload?.state === "on" || payload?.state === "off" ? payload.state : undefined;
			} catch {
				return undefined;
			}
		},
		saveState(state) {
			mkdirSync(dirname(path), { recursive: true });
			writeFileSync(path, JSON.stringify({ state }, null, 2) + "\n", "utf8");
		},
	};
}
