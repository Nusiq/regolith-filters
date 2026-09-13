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

	// Write an empty deno.json to the working directory (Regolith's temporary
	// directory). Starting from Deno 2.6, Deno searches outwards through the
	// parent paths looking for deno.json files when resolving the config for
	// dynamically imported modules. Without this file Deno would find the
	// deno.json of the Regolith project and use it for the files that the main
	// script imports from the working directory. The empty file stops that
	// search, so the config of the entry point (the filter's deno.json with
	// the "imports" synced below) keeps being used instead.
	console.log("Writing empty deno.json to the working directory...");
	writeFileSync(join(Deno.cwd(), "deno.json"), "{}");

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

	// Preserve original FILTER_DIR/deno.json
	const oldDenoJsonPath = join(FILTER_DIR, "old_deno.json");
	try {
		Deno.statSync(oldDenoJsonPath);
		// old_deno.json exists, restore original
		console.log("Restoring original %FILTER_DIR%/deno.json from old_deno.json...");
		Deno.copyFileSync(oldDenoJsonPath, filterDenoJsonPath);
	} catch {
		// old_deno.json doesn't exist, backup current
		console.log("Backing up original %FILTER_DIR%/deno.json to old_deno.json...");
		Deno.copyFileSync(filterDenoJsonPath, oldDenoJsonPath);
	}

	// Read ROOT_DIR/deno.json if exists
	let rootImports: Record<string, any> = {};
	const rootDenoJsonPath = join(ROOT_DIR, "deno.json");
	try {
		console.log("Reading %ROOT_DIR%/deno.json...");
		const rootConfig: any = JSON.parse(readFileSync(rootDenoJsonPath, "utf-8"));
		if (
			rootConfig.imports &&
			typeof rootConfig.imports === "object" &&
			!Array.isArray(rootConfig.imports)
		) {
			rootImports = rootConfig.imports;
		}
	} catch {
		console.log("%ROOT_DIR%/deno.json not found, skipping.");
		return;
	}

	if (Object.keys(rootImports).length === 0) {
		console.log("No imports to sync from %ROOT_DIR%, skipping.");
		return;
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

	// Resolve relative imports in rootImports
	console.log("Resolving relative imports from %ROOT_DIR%/deno.json...");
	for (const [key, value] of Object.entries(rootImports)) {
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
			rootImports[key] = toFileUrl(resolved).href;
			// Ensure file URL ends with / for directory mappings
			if (!rootImports[key].endsWith("/")) {
				rootImports[key] += "/";
			}
			console.log(`Resolved ${key}: ${value} -> ${rootImports[key]}`);
		} else if (typeof value !== "string") {
			console.warn(`Skipping non-string import ${key}: ${value}`);
			delete rootImports[key];
		}
	}

	// Merge imports: rootImports + filterConfig.imports
	console.log("Merging imports...");
	const mergedImports = deepMergeObjects(
		rootImports,
		filterConfig.imports || {},
		ListMergePolicy.APPEND
	);

	// Create final config: filterConfig with merged imports
	const mergedConfig = { ...filterConfig, imports: mergedImports };

	// Write to FILTER_DIR/deno.json
	console.log("Writing merged deno.json to %FILTER_DIR%...");
	writeFileSync(
		join(FILTER_DIR, "deno.json"),
		JSON.stringify(mergedConfig, null, "\t")
	);
	console.log("Syncing deno.json files from %ROOT_DIR% to %FILTER_DIR% complete.");
}

if (import.meta.main) {
	main();
}
