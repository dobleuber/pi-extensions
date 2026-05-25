export type InputSource = "interactive" | "rpc" | "extension" | string;

export interface InputRoutingCandidate {
	text: string;
	source: InputSource;
}

export function shouldRouteInput(input: InputRoutingCandidate): boolean {
	if (input.source === "extension") return false;

	const text = input.text.trim();
	if (text.length === 0) return false;
	if (text.startsWith("/")) return false;
	if (text.startsWith("!")) return false;

	return true;
}
