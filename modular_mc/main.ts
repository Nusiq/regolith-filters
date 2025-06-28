import { isAbsolute } from "@std/path";
import { compileWithEsbuild } from "./esbuild.ts";
import { deepMergeObjects, ListMergePolicy } from "./json-merge.ts";
import { processModule } from "./map-ts.ts";
import { asPosix, join } from "./path-utils.ts";
import { getDataPath, getRootDir } from "./regolith.ts";
import * as JSONC from "@std/jsonc";

if (import.meta.main) {
	let scope: Record<string, any> = {};
	let esbuildOptions: Record<string, any> = {};
	let buildPath: string | undefined;

	// Get command line arguments
	const args = Deno.args;
	if (args.length > 0) {
		try {
			const input = JSON.parse(args[0]);

			// Handle scope property
			if (input.scope !== undefined) {
				scope = input.scope;
			}

			// Handle scopePath property
			if (input.scopePath !== undefined) {
				// Resolve the path - if not absolute, make it relative to ./data
				const scopePath = isAbsolute(input.scopePath)
					? asPosix(input.scopePath)
					: join("./data", input.scopePath);

				const scopePathContent = await Deno.readTextFile(scopePath);
				const scopePathData: any = JSONC.parse(scopePathContent);

				// Merge scopePath data into scope if both exist
				if (input.scope !== undefined) {
					scope = deepMergeObjects(
						scope,
						scopePathData,
						ListMergePolicy.APPEND
					);
				} else {
					scope = scopePathData;
				}
			}

			// Get esbuild options if provided
			if (input.esbuild !== undefined && typeof input.esbuild === "object") {
				esbuildOptions = input.esbuild.settings || {};
				buildPath = input.esbuild.buildPath;
			}
		} catch (error) {
			console.error("Error processing input:", error);
			Deno.exit(1);
		}
	}

	// Process and collect modules
	const modules = await processModule();

	// Collect all scripts from modules
	const allScripts: string[] = [];
	for (const module of modules) {
		allScripts.push(...module.scripts);
	}

	// If we have scripts defined in modules, run the compilation
	if (allScripts.length > 0) {
		try {
			const rootDir = getRootDir();
			const dataPath = await getDataPath(rootDir);

			// Resolve script paths to absolute paths pointing to original files
			const absoluteScriptPaths: string[] = [];
			for (const module of modules) {
				absoluteScriptPaths.push(
					...module.resolveScriptPaths(rootDir, dataPath)
				);
			}

			// Debug log to see the resolved paths
			console.log("Compiling scripts:");
			absoluteScriptPaths.forEach((path) => console.log(`  ${path}`));

			if (buildPath !== undefined) {
				buildPath = join(rootDir, buildPath);
			}

			// Run esbuild with the resolved script paths and buildPath
			await compileWithEsbuild(esbuildOptions, absoluteScriptPaths, buildPath);
		} catch (error) {
			console.error(
				"Error during script path resolution or compilation:",
				error
			);
			Deno.exit(1);
		}
	}

	// Apply all modules
	for (const module of modules) {
		await module.apply(scope);
	}
}
