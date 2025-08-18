export const MAP = [
	// With new line at the end of the file
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
	// Without new line at the end of the file
	{
		source: "on_conflict_no_new_line_append_base.txt",
		target: "BP/on_conflict_no_new_line_append.txt",
	},
	{
		source: "on_conflict_no_new_line_append_start.txt",
		target: "BP/on_conflict_no_new_line_append.txt",
		onConflict: "appendStart",
	},
	{
		source: "on_conflict_no_new_line__append_end.txt",
		target: "BP/on_conflict_no_new_line_append.txt",
		onConflict: "appendEnd",
	},
];
