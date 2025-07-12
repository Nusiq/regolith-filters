import { compileWithEsbuild } from "./esbuild.ts";
import { processModule } from "./map-ts.ts";
import { join } from "./path-utils.ts";
import { getDataPath, getRootDir } from "./regolith.ts";
import dedent from "npm:dedent";

if (import.meta.main) {
	let esbuildOptions: Record<string, any> = {};
	let buildPath: string | undefined;

	// Get command line arguments
	const args = Deno.args;
	if (args.length > 0) {
		try {
			const input = JSON.parse(args[0]);

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
				"Error during script path resolution or compilation:\n",
				error
			);
			Deno.exit(1);
		}
	}

	// Apply all modules
	for (const module of modules) {
		try {
			await module.apply();
		} catch (error) {
			const errorMessage =
				error instanceof Error ? error.message : String(error);
			console.error(
				dedent`
				Error during evaluation of the MAP files:
				${errorMessage}`
			);
			Deno.exit(1);
		}
	}
}
