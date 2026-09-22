import {
	ASTRA_MEDIUM_PROFILE,
	DEFAULT_MODEL_PROFILE,
	SOL_PROFILE,
	type ModelProfile,
	type ModelProfileState,
} from "./model-profile.ts";

export type JevProfileKey = "luna" | "sol" | "astra";
export type JevCostTier = 1 | 2 | 3;

export const JEV_PROFILE_CRITERIA_VERSION = "jev-router-profile-rubric-v3" as const;
export const JEV_PROFILE_CATALOG_VERSION = "jev-router-profile-catalog-v4" as const;

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
		key: "sol",
		profile: SOL_PROFILE,
		description: "Demanding programming tasks and multi-step agentic workflows—complex implementations, difficult debugging, and work requiring sustained tool use—when Sol offers better performance per cost than Astra Low.",
		costTier: 2,
	},
	{
		key: "astra",
		profile: ASTRA_MEDIUM_PROFILE,
		description: "Reserve for cases where choosing Astra over Sol is justified by novel architecture, deeply ambiguous requirements, or interacting cross-system constraints requiring exceptional reasoning and judgment. Complex implementation, difficult debugging, or sustained tool use alone should favor Sol, not trigger escalation to Astra.",
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
