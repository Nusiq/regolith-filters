import * as JSONC from "@std/jsonc";
import { join, resolve, relative } from "./path-utils.ts";
import { toFileUrl } from "@std/path";
import { readFileSync, writeFileSync } from "node:fs";

function main() {
	const ROOT_DIR = Deno.env.get("ROOT_DIR");

	if (!ROOT_DIR) {
		console.error("%ROOT_DIR% not set");
		Deno.exit(1);
	}

	// Read ROOT_DIR/deno.json if exists
	let rootConfig: any = {};
	let rootImports: Record<string, any> = {};
	const rootDenoJsonPath = join(ROOT_DIR, "deno.json");
	try {
		console.log("Reading %ROOT_DIR%/deno.json...");
		rootConfig = JSON.parse(readFileSync(rootDenoJsonPath, "utf-8"));
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

	// Write a modified copy of ROOT_DIR/deno.json to the working directory.
	// The copy keeps the original config content but the relative import paths
	// are resolved to absolute paths. Since Deno 2.6, dynamically imported
	// modules resolve their config by walking up their own directory tree, so
	// this copy is the config that gets applied to the files imported by
	// main.ts from the working directory.
	console.log("Writing deno.json to the working directory...");
	writeFileSync(
		join(Deno.cwd(), "deno.json"),
		JSON.stringify({ ...rootConfig, imports: rootImports }, null, "\t")
	);
	console.log(
		"Syncing deno.json from %ROOT_DIR% to the working directory complete."
	);
}

if (import.meta.main) {
	main();
}
