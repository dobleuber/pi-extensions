import {
	ASTRA_LOW_PROFILE,
	ASTRA_MEDIUM_PROFILE,
	DEFAULT_MODEL_PROFILE,
	TERRA_MEDIUM_PROFILE,
	type ModelProfile,
	type ModelProfileState,
} from "./model-profile.ts";

export type JevProfileKey = "luna" | "terra" | "vega" | "astra";
export type JevCostTier = 1 | 2 | 3;

export const JEV_PROFILE_CRITERIA_VERSION = "jev-router-profile-rubric-v2" as const;
export const JEV_PROFILE_CATALOG_VERSION = "jev-router-profile-catalog-v2" as const;

export interface JevProfileCandidate {
	readonly key: JevProfileKey;
	readonly profile: ModelProfile;
	readonly description: string;
	readonly costTier: JevCostTier;
}

export const JEV_PROFILE_CANDIDATES: readonly JevProfileCandidate[] = Object.freeze([
	{
		key: "luna",
		profile: DEFAULT_MODEL_PROFILE,
		description: "Clearly scoped implementation, bug fixes, tests, documentation, code review, bounded refactors, and moderately complex work with clear acceptance criteria. Prefer this category when the task follows established patterns, even across multiple files; do not restrict it to trivial edits.",
		costTier: 1,
	},
	{
		key: "terra",
		profile: TERRA_MEDIUM_PROFILE,
		description: "Multi-step work with meaningful ambiguity: cross-file features requiring integration decisions, debugging with several plausible causes, dependency or API migrations, and design trade-offs within a bounded subsystem. Choose when resolving those uncertainties is central, not merely because several files are involved.",
		costTier: 2,
	},
	{
		key: "vega",
		profile: ASTRA_LOW_PROFILE,
		description: "Focused difficult bugs, subtle localized correctness changes, and constrained tool-assisted investigations where the scope and success condition are precise. Requires careful judgment but not sustained exploration, broad planning, or architectural redesign.",
		costTier: 2,
	},
	{
		key: "astra",
		profile: ASTRA_MEDIUM_PROFILE,
		description: "Hard end-to-end work requiring sustained planning and verification: novel architecture, broad migrations, cross-subsystem debugging, complex research or tool workflows, and ambiguous requirements with interacting constraints.",
		costTier: 3,
	},
]);

const PROFILE_BY_KEY: Readonly<Record<JevProfileKey, ModelProfile>> = Object.freeze(
	Object.fromEntries(JEV_PROFILE_CANDIDATES.map((candidate) => [candidate.key, candidate.profile])) as Record<JevProfileKey, ModelProfile>,
);

export function profileForJevKey(key: string): ModelProfileState | undefined {
	if (!Object.prototype.hasOwnProperty.call(PROFILE_BY_KEY, key)) return undefined;
	const profile = PROFILE_BY_KEY[key as JevProfileKey];
	return { ...profile, source: "automatic" };
}

export function eligibleJevProfileCandidates(
	eligibleKeys: readonly string[] = JEV_PROFILE_CANDIDATES.map((candidate) => candidate.key),
	maxCostTier: JevCostTier = 3,
): readonly JevProfileCandidate[] {
	const allowed = new Set(eligibleKeys.map((key) => key.trim().toLowerCase()));
	return JEV_PROFILE_CANDIDATES.filter((candidate) => allowed.has(candidate.key) && candidate.costTier <= maxCostTier);
}

export function selectJevProfile(key: string, eligibleKeys?: readonly string[], maxCostTier: JevCostTier = 3): ModelProfileState | undefined {
	const normalized = key.trim().toLowerCase();
	if (!eligibleJevProfileCandidates(eligibleKeys, maxCostTier).some((candidate) => candidate.key === normalized)) return undefined;
	return profileForJevKey(normalized);
}
