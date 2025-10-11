import { deepMergeObjects, ListMergePolicy } from "./json-merge.ts";
import { join, resolve } from "@std/path";
import { readFileSync, writeFileSync } from "node:fs";

function main() {
	const ROOT_DIR = Deno.env.get("ROOT_DIR");
	const FILTER_DIR = Deno.env.get("FILTER_DIR");

	if (!ROOT_DIR || !FILTER_DIR) {
		console.error("%ROOT_DIR% or %FILTER_DIR% not set");
		Deno.exit(1);
	}

	const filterDenoJsonPath = join(FILTER_DIR, "deno.json");

	// Check if FILTER_DIR/deno.json exists
	try {
		Deno.statSync(filterDenoJsonPath);
	} catch {
		console.log("%FILTER_DIR%/deno.json not found, skipping dependency sync.");
		return;
	}

	console.log("Reading %FILTER_DIR%/deno.json...");
	const filterConfig = JSON.parse(readFileSync(filterDenoJsonPath, "utf-8"));

	// Read ROOT_DIR/deno.json if exists
	let rootConfig = {};
	const rootDenoJsonPath = join(ROOT_DIR, "deno.json");
	try {
		console.log("Reading %ROOT_DIR%/deno.json...");
		rootConfig = JSON.parse(readFileSync(rootDenoJsonPath, "utf-8"));
	} catch {
		console.log("%ROOT_DIR%/deno.json not found, using empty config.");
	}

	// Resolve relative imports in filterConfig to ROOT_DIR
	if (filterConfig.imports) {
		console.log("Resolving relative imports in %FILTER_DIR%/deno.json...");
		for (const [key, value] of Object.entries(filterConfig.imports)) {
			if (
				typeof value === "string" &&
				(value.startsWith("./") || value.startsWith("../"))
			) {
				const resolved = resolve(ROOT_DIR, value);
				filterConfig.imports[key] = resolved;
			}
		}
	}

	// Merge filterConfig on top of rootConfig (filter overwrites)
	console.log("Merging configs...");
	const mergedConfig = deepMergeObjects(
		rootConfig,
		filterConfig,
		ListMergePolicy.APPEND
	);

	// Write to FILTER_DIR/deno.json
	console.log("Writing merged deno.json to %FILTER_DIR%...");
	writeFileSync(
		join(FILTER_DIR, "deno.json"),
		JSON.stringify(mergedConfig, null, "\t")
	);
	console.log(
		"Syncing deno.json files from %ROOT_DIR% to %FILTER_DIR% complete."
	);
}

if (import.meta.main) {
	main();
}
