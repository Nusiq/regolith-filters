export const MAP = [
	{
		source: "on_conflict_merge_1.json",
		target: "BP/on_conflict_merge.json",
		jsonTemplate: true,
	},
	{
		source: "on_conflict_merge_2.json",
		target: "BP/on_conflict_merge.json",
		jsonTemplate: true,
		onConflict: "merge",
	},
	{
		// This file won't be added because the target already exists
		// and onConflict is set to skip
		source: "on_conflict_merge_3.json",
		target: "BP/on_conflict_merge.json",
		jsonTemplate: true,
		onConflict: "skip",
	},
];
