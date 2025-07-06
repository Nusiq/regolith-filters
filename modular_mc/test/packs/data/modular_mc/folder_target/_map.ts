export const MAP = [
	// Moving [ folder_target.json ]
	// to     [ BP/features_custom/folder_target/subfolder/folder_target.json ]
	{
		source: "**/*.json",
		target: "BP/features_custom/folder_target/subfolder1", // Note: No trailing slash here
	},
	{
		source: "**/*.json",
		target: "BP/features_custom/folder_target/subfolder2/", // Note: Trailing slash here
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
