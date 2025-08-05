import { ensureDirSync } from "@std/fs";
import * as esbuild from "esbuild";
import { dirname, asPosix } from "./path-utils.ts";
import { ModularMcError } from "./error.ts";
import dedent from "npm:dedent";

export interface CompileOptions {
	/**
	 * Whether to minify the output
	 * @default false
	 */
	minify?: boolean;

	/**
	 * The output file path (relative to the filter's working directory)
	 * @default "BP/scripts/main.js"
	 */
	outfile?: string;

	/**
	 * Packages to mark as external
	 * @default ["@minecraft/server"]
	 */
	external?: string[];

	/**
	 * Whether to generate source maps
	 * @default false
	 */
	sourcemap?: boolean;

	/**
	 * Labels to drop during compilation
	 * @default []
	 */
	dropLabels?: string[];
}

/**
 * Compiles TypeScript files using esbuild
 * @param options Compilation options
 * @param entryPoints List of entry points to compile
 * @param buildPath Optional build path
 */
export async function compileWithEsbuild(
	options: CompileOptions | undefined,
	entryPoints: string[] = [],
	buildPath?: string
): Promise<void> {
	if (options === undefined) {
		options = {};
	}

	// Set default options
	const {
		minify = false,
		outfile = "BP/scripts/main.js",
		external = ["@minecraft/server"],
		sourcemap = false,
		dropLabels = [],
	} = options;

	// Make sure @minecraft/server is in the external list
	const externalPackages = [...external];
	if (!externalPackages.includes("@minecraft/server")) {
		externalPackages.push("@minecraft/server");
	}

	let tempEntryFile: string | undefined;

	try {
		// Ensure output directory exists
		ensureDirSync(dirname(outfile));

		// Determine the final output path
		const esbuildOutFile = buildPath ? buildPath : outfile;

		// Handle multiple entry points by creating a temporary entry file
		let finalEntryPoints: string[];
		if (entryPoints.length > 1) {
			// Create a temporary entry file that imports all the other files
			tempEntryFile = `.temp_esbuild_entry_${Date.now()}.ts`;
			const imports = entryPoints.map((file) => {
				return `import "${asPosix(file)}";`;
			}).join('\n');
			
			await Deno.writeTextFile(tempEntryFile, imports);
			finalEntryPoints = [tempEntryFile];
		} else {
			finalEntryPoints = entryPoints;
		}

		// Build with esbuild
		const result = await esbuild.build({
			entryPoints: finalEntryPoints,
			bundle: true,
			minify: minify,
			format: "esm",
			target: "es2020",
			outfile: esbuildOutFile,
			sourcemap: sourcemap,
			external: externalPackages,
			dropLabels: dropLabels,
		});

		if (result.errors.length > 0) {
			const error =  new ModularMcError(
				dedent`
				Build failed with errors.
				Errors:`
			);
			for (const e of result.errors) {
				error.moreInfo(e);
			}
			throw error;
		}

		console.log(`Compiled ${entryPoints.join(", ")} to ${esbuildOutFile}`);

		// If buildPath is specified, copy the compiled file to the final outfile
		if (buildPath) {
			await Deno.copyFile(esbuildOutFile, outfile);
			console.log(`Copied compiled file to ${outfile}`);
		}
	} finally {
		// We don't need to clean up the temporary entry file because it's created
		// in Regolith's temporary directory and Regolith will handle it.

		// Stop esbuild service. This is helpful to stop the child process when
		// running with Deno.
		esbuild.stop();
	}
}
