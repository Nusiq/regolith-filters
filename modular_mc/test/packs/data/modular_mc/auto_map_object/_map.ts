// Exports following files
// -> BP/features/auto_map_object_1.json
// -> BP/features/subdir/auto_map_object_1.json
// -> BP/features/auto_map_object_2.json
// -> BP/features_custom/auto_map_object_1.json
// -> BP/features/subdir/custom/auto_map_object_1.json
// -> BP/features/subdir/auto_map_object_custom_name.json
// -> BP/features_custom/custom/auto_map_object_custom_name.json
export const MAP = [
	// Examples equivalent to regular auto mapping
	{
		source: "subdir/auto_map_object_1.feature.json",
		target: {
			// -> BP/features/auto_map_object_1.json
			path: ":autoFlat",
			name: ":auto"
		}
	},
	{
		source: "subdir/auto_map_object_1.feature.json",
		target: {
			// -> BP/features/subdir/auto_map_object_1.json
			path: ":auto",
			name: ":auto"
		}
	},
	{
		source: "auto_map_object_2.feature.json",
		target: {
			// -> BP/features/auto_map_object_2.json
			path: ":auto",
			name: ":auto"
		}
	},
	// Custom path
	{
		source: "subdir/auto_map_object_1.feature.json",
		target: {
			// -> BP/features_custom/auto_map_object_1.json
			path: "BP/features_custom",
			name: ":auto"
		}
	},
	// Custom subpath
	{
		source: "subdir/auto_map_object_1.feature.json",
		target: {
			// -> BP/features/subdir/custom/auto_map_object_1.json
			path: ":auto",
			subpath: "custom",
			name: ":auto"
		}
	},
	// Custom name
	{
		source: "subdir/auto_map_object_1.feature.json",
		target: {
			// -> BP/features/subdir/auto_map_object_custom_name.json
			path: ":auto",
			name: "auto_map_object_custom_name.json"
		}
	},
	// Custom everything
	{
		source: "subdir/auto_map_object_1.feature.json",
		target: {
			// -> BP/features_custom/custom/auto_map_object_custom_name.json
			path: "BP/features_custom",
			subpath: "custom",
			name: "auto_map_object_custom_name.json"
		}
	},
];
