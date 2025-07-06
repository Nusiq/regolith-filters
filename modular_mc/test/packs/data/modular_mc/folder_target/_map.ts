export const MAP = [
	// Moving [ folder_target.json ]
	// to     [ BP/features_custom/folder_target/subfolder/folder_target.json ]
	{
		//THIS IS NOT ALLOWED. ADDING THIS WOULD MEAN THAT YOU CAN'T EXPORT
		// FILES WITHOUT EXTENSION.
		source: "folder_target.json",
		target: "BP/features_custom/folder_target/not_a_subfolder", // No trailing slash here
	},
	{
		// Note that the paths in the source get flattened.
		source: "**/*.json",
		target: "BP/features_custom/folder_target/subfolder2/", // Trailing slash here
	},
	// Edge cases
	{
		source: "**/*.json",
		target: "BP/features_custom/folder_target/subfolder3/fake_subpath/..", 
	},
	{
		source: "**/*.json",
		target: "BP/features_custom/folder_target/subfolder4/.",
	},
];
