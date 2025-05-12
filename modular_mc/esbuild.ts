import { ensureDirSync } from "@std/fs";
import * as esbuild from "esbuild";
import { dirname } from "./path-utils.ts";

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
	} = options;

	// Make sure @minecraft/server is in the external list
	const externalPackages = [...external];
	if (!externalPackages.includes("@minecraft/server")) {
		externalPackages.push("@minecraft/server");
	}

	try {
		// Ensure output directory exists
		ensureDirSync(dirname(outfile));

		// Determine the final output path
		const esbuildOutFile = buildPath ? buildPath : outfile;

		// Build with esbuild
		const result = await esbuild.build({
			entryPoints: entryPoints,
			bundle: true,
			minify: minify,
			format: "esm",
			target: "es2020",
			outfile: esbuildOutFile,
			sourcemap: sourcemap,
			external: externalPackages,
		});

		if (result.errors.length > 0) {
			console.error("Build failed with errors:", result.errors);
			Deno.exit(1);
		}

		console.log(`Compiled ${entryPoints.join(", ")} to ${esbuildOutFile}`);

		// If buildPath is specified, copy the compiled file to the final outfile
		if (buildPath) {
			await Deno.copyFile(esbuildOutFile, outfile);
			console.log(`Copied compiled file to ${outfile}`);
		}
	} finally {
		// Stop esbuild service. This is helpful to stop the child process when
		// running with Deno.
		esbuild.stop();
	}
}
