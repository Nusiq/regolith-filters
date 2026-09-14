export const MAP = [
	{
		source: "ordered_entry.behavior.json",
		target: ":autoFlat",
		jsonTemplate: true,
		onConflict: "merge",
		executionOrder: 3,
		scope: {
			input: "ENTRY 3",
		},
	},
];
