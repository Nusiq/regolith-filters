export const MAP = [
	// No extension replacement
	{
		source: "subdir/auto_map_1.behavior.json",
		target: ":autoFlat",
	},
	{
		source: "subdir/auto_map_1.behavior.json",
		target: ":auto",
	},
	{
		source: "auto_map_2.behavior.json",
		target: ":auto",
	},
	// Extension replacement
	{
		source: "subdir/auto_map_3.feature.json",
		target: ":autoFlat",
	},
	{
		source: "subdir/auto_map_3.feature.json",
		target: ":auto",
	},
	{
		source: "auto_map_4.feature.json",
		target: ":auto",
	},
];
