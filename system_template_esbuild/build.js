// @ts-check
const fs = require("fs");

const defaultSettings = {
	minify: false,
	entryPoint: "data/system_template_esbuild/main.ts",
	outfile: "BP/scripts/main.js",
	external: ["@minecraft/server"],
	scope_path: null,
};

/**
 * Evaluates a string with the given scope. If string is not a template string, it is
 * returned as is. A template string must start and end with a backtick (`). Variables
 * are denoted by curly braces and their value is looked up in the scope. Performing
 * operations in the template string is not supported (just variable substitution).
 * @param {string} str
 * @param {Object} scope
 * @returns {string}
 */
function evalString(str, scope) {
	// Check if the string is a template string.
	if (!str.startsWith("`") || !str.endsWith("`")) {
		return str;
	}
	// If it is, remove the backticks and replace the variables.
	str = str.slice(1, -1);
	return str.replace(/\{([a-zA-Z_]+[a-zA-Z_0-9]*)\}/g, function (_, key) {
		return scope[key];
	});
}

// SCRIPT BODY

// Load the settings (JSON) from the first command line argument.
const args = process.argv[2];
let settings = defaultSettings;
if (args !== undefined) {
	settings = { ...settings, ...JSON.parse(args) };
}

// Extract the settings and check the types
let { minify, entryPoint, outfile, external, scope_path } = settings;

if (typeof minify !== "boolean") {
	throw new Error("The 'minify' setting must be a boolean");
}
if (typeof entryPoint !== "string") {
	throw new Error("The 'entryPoint' setting must be a string");
}
if (typeof outfile !== "string") {
	throw new Error("The 'outfile' setting must be a string");
}
if (!Array.isArray(external)) {
	throw new Error("The 'external' setting must be an array");
} else {
	for (let ext of external) {
		if (typeof ext !== "string") {
			throw new Error("The 'external' setting must be an array of strings");
		}
	}
}
if (scope_path !== null && typeof scope_path !== "string") {
	throw new Error("The 'scope_path' setting must be a string or null");
}

// Append @minecraft/server to the external array if it's not already there
if (!external.includes("@minecraft/server")) {
	external.push("@minecraft/server");
}

// Load the scope from the scope file
let scope = {};
if (scope_path !== null) {
	const jsoncParser = require("jsonc-parser");
	scope = jsoncParser.parse(fs.readFileSync("data/" + scope_path, "utf8"));
}

// Evaluate the settings with the scope
entryPoint = evalString(entryPoint, scope);
outfile = evalString(outfile, scope);

// Build the project.
require("esbuild")
	.build({
		external: external,
		entryPoints: [entryPoint],
		target: "es2023",
		format: "esm",
		bundle: true,
		minify: minify,
		outfile: outfile,
	})
	.catch((err) => {
		console.error(err.message);
		process.exit(1);
	});
