export const MAP = [
	{
		source: "ordered_entry.behavior.json",
		target: ":autoFlat",
		jsonTemplate: true,
		onConflict: "merge",
		executionOrder: 2,
		scope: {
			input: "ENTRY 2",
		},
	},
	{
		source: "ordered_entry.behavior.json",
		target: ":autoFlat",
		jsonTemplate: true,
		onConflict: "merge",
		executionOrder: 1,
		scope: {
			input: "ENTRY 1",
		},
	},
	{
		source: "ordered_entry.behavior.json",
		target: ":autoFlat",
		jsonTemplate: true,
		onConflict: "merge",
		executionOrder: 4,
		scope: {
			input: "ENTRY 4",
		},
	},
	// ENTRY 3 is sent from another module
];
