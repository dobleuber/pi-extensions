import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function piRouterExtension(pi: ExtensionAPI) {
	pi.on("input", async (_event) => {
		return { action: "continue" };
	});
}
