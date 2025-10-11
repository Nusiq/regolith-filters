import { deepMergeObjects, ListMergePolicy } from "./json-merge.ts";
import { join, resolve, relative } from "./path-utils.ts";
import { toFileUrl } from "@std/path";
import * as JSONC from "@std/jsonc";
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
	let rootConfig: Record<string, any> = {};
	const rootDenoJsonPath = join(ROOT_DIR, "deno.json");
	try {
		console.log("Reading %ROOT_DIR%/deno.json...");
		rootConfig = JSON.parse(readFileSync(rootDenoJsonPath, "utf-8"));
	} catch {
		console.log("%ROOT_DIR%/deno.json not found, using empty config.");
	}

	// Read config.json to get dataPath
	const configPath = join(ROOT_DIR, "config.json");
	let dataPathAbs = "";
	let tempData = "";
	try {
		console.log("Reading %ROOT_DIR%/config.json for dataPath...");
		const config: any = JSONC.parse(readFileSync(configPath, "utf-8"));
		const dataPath = config.regolith?.dataPath;
		if (dataPath) {
			dataPathAbs = resolve(ROOT_DIR, dataPath);
			tempData = join(Deno.cwd(), "data");
			console.log("Data path mapping: %s -> %s", dataPathAbs, tempData);
		}
	} catch (error) {
		console.error("Failed to read or parse %ROOT_DIR%/config.json:", error);
		Deno.exit(1);
	}

	// Resolve relative imports in filterConfig to ROOT_DIR
	if (rootConfig.imports) {
		console.log("Resolving relative imports in %FILTER_DIR%/deno.json...");
		for (const [key, value] of Object.entries(rootConfig.imports)) {
			if (
				typeof value === "string" &&
				(value.startsWith("./") || value.startsWith("../"))
			) {
				let resolved = resolve(ROOT_DIR, value);
				// If within dataPath, swap to temp data
				if (dataPathAbs) {
					const relPath = relative(dataPathAbs, resolved);
					if (
						!relPath.startsWith("..") &&
						relPath !== "" &&
						!relPath.startsWith("/")
					) {
						resolved = join(tempData, relPath);
					}
				}
				rootConfig.imports[key] = toFileUrl(resolved).href;
				// Ensure file URL ends with / for directory mappings
				if (!rootConfig.imports[key].endsWith("/")) {
					rootConfig.imports[key] += "/";
				}
				console.log(`Resolved ${key}: ${value} -> ${rootConfig.imports[key]}`);
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
