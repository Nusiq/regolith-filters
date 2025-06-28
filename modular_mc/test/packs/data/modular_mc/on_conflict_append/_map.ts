export const MAP = [
	{
		source: "on_conflict_append_base.txt",
		target: "BP/on_conflict_append.txt",
	},
	{
		source: "on_conflict_append_start.txt",
		target: "BP/on_conflict_append.txt",
		onConflict: "appendStart",
	},
	{
		source: "on_conflict_append_end.txt",
		target: "BP/on_conflict_append.txt",
		onConflict: "appendEnd",
	},
];
