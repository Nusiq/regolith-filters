// @ts-check
import {
	readFileSync,
	copyFileSync,
	existsSync,
	mkdirSync,
	writeFileSync,
	rmSync,
	readdirSync,
	statSync,
} from "node:fs";
import { join, dirname } from "node:path";
import { buildSync } from "esbuild";
import { parse } from "jsonc-parser";

const REGOLITH_ROOT_DIR = process.env.ROOT_DIR;
if (REGOLITH_ROOT_DIR === undefined) {
	// This should never happen
	console.error("The ROOT_DIR environment variable is not set");
	process.exit(1);
}

const defaultSettings = {
	minify: false,
	/** @type {null | string} */
	working_dir: null,
	outfile: "BP/scripts/main.js",
	external: ["@minecraft/server"],
	/** @type {null | string} */
	scope_path: null,
	sourcemap: false,
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
let {
	minify,
	outfile,
	external,
	scope_path,
	sourcemap,
	working_dir: working_dir,
} = settings;

if (typeof minify !== "boolean") {
	console.error("The 'minify' setting must be a boolean");
	process.exit(1);
}
if (typeof outfile !== "string") {
	console.error("The 'outfile' setting must be a string");
	process.exit(1);
}
if (!Array.isArray(external)) {
	console.error("The 'external' setting must be an array");
	process.exit(1);
} else {
	for (let ext of external) {
		if (typeof ext !== "string") {
			console.error("The 'external' setting must be an array of strings");
			process.exit(1);
		}
	}
}
if (scope_path !== null && typeof scope_path !== "string") {
	console.error("The 'scope_path' setting must be a string or null");
	process.exit(1);
}
if (typeof sourcemap !== "boolean") {
	console.error("The 'sourcemap' setting must be a boolean");
	process.exit(1);
}
if (working_dir !== null && typeof working_dir !== "string") {
	console.error("The 'working_dir' setting must be a string or null");
	process.exit(1);
}
// Append @minecraft/server to the external array if it's not already there
if (!external.includes("@minecraft/server")) {
	external.push("@minecraft/server");
}

// Load the scope from the scope file
let scope = {};
if (scope_path !== null) {
	scope = parse(readFileSync(join("data", scope_path), "utf8"));
}

// Evaluate the settings with the scope
outfile = evalString(outfile, scope);

// Build the project.
if (working_dir === null) {
	// Build into the data/system_template_esbuild/main.js file
	const buildResult = buildSync({
		external: external,
		entryPoints: ["data/system_template_esbuild/main.ts"],
		target: "es2020",
		format: "esm",
		bundle: true,
		minify: minify,
		outfile: "data/system_template_esbuild/main.js",
		sourcemap: sourcemap,
	});
	if (buildResult.errors.length > 0) {
		console.error(buildResult.errors);
		process.exit(1);
	}

	// Copy the generated main.js file to the 'outfile' location
	mkdirSync(dirname(outfile), { recursive: true });
	copyFileSync("data/system_template_esbuild/main.js", outfile);
} else {
	const dotSystemTemplateEsbuildText =
		"This file marks the directory as safe for deletion by " +
		"system_template_esbuild filter.";

	// Resolve the working directory
	working_dir = join(REGOLITH_ROOT_DIR, working_dir);
	// Check if the working directory exists, if it does, try to clean it safely
	// by checking if it's empty or marked with a .system_template_esbuild file
	if (existsSync(working_dir)) {
		// Make sure it's a directory
		if (!statSync(working_dir).isDirectory()) {
			console.error(
				"The working directory path is not a directory.\n" +
					`Path: ${working_dir}`
			);
			process.exit(1);
		}

		// Check if empty or marked with .system_template_esbuild file
		if (readdirSync(working_dir).length !== 0) {
			if (existsSync(join(working_dir, ".system_template_esbuild"))) {
				rmSync(working_dir, { recursive: true, force: true });
				mkdirSync(working_dir, { recursive: true });
			} else {
				console.error(
					"The working directory couldn't be safely cleaned. It's not empty " +
						"and doesn't seem to be created by system_template_esbuild.\n" +
						`Path: ${working_dir}`
				);
				process.exit(1);
			}
		}
	} else {
		mkdirSync(working_dir, { recursive: true });
	}

	// Copy the files form data/system_template_esbuild to the working directory
	const files = /** @type {string[]} */ (
		readdirSync("data/system_template_esbuild", {
			recursive: true,
		})
	);
	for (const file of files) {
		const srcPath = join("data/system_template_esbuild", file);
		const destPath = join(working_dir, file);

		// Create parent directories if they don't exist
		mkdirSync(dirname(destPath), { recursive: true });

		// Copy
		if (!statSync(srcPath).isDirectory()) {
			copyFileSync(srcPath, destPath);
		}
	}

	// Create marker file
	writeFileSync(
		join(working_dir, ".system_template_esbuild"),
		dotSystemTemplateEsbuildText
	);

	// Build in the working directory
	const buildResult = buildSync({
		external: external,
		entryPoints: [join(working_dir, "main.ts")],
		target: "es2020",
		format: "esm",
		bundle: true,
		minify: minify,
		outfile: join(working_dir, "main.js"),
		sourcemap: sourcemap,
	});
	if (buildResult.errors.length > 0) {
		console.error(buildResult.errors);
		process.exit(1);
	}
	// Copy the generated main.js file to the 'outfile' location
	mkdirSync(dirname(outfile), { recursive: true });
	copyFileSync(join(working_dir, "main.js"), outfile);
}
