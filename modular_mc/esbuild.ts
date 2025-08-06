import { ensureDirSync } from "@std/fs";
import * as esbuild from "esbuild";
import { denoPlugins } from "esbuild_deno_loader";
import { dirname, asPosix, join } from "./path-utils.ts";
import { toFileUrl } from "@std/path";
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
	rootDir: string,
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

	try {
		// Ensure output directory exists
		ensureDirSync(dirname(outfile));

		// Determine the final output path
		const esbuildOutFile = buildPath ? buildPath : outfile;

		// If deno.json exists, we use the Deno path resolver to enable the
		// usage of the dependencies specified in deno.json.
		const configPath = join(rootDir, "deno.json");
		const useDenoResolver = await Deno.stat(configPath)
			.then((s) => s.isFile)
			.catch(() => false);

		// TODO: Removing this comments would enable import maps.
		// let importMapURL: string | undefined;
		// try {
		// 	const mapPath = join(rootDir, "import_map.json");
		// 	await Deno.stat(mapPath);
		// 	importMapURL = mapPath;
		// } catch {
		// 	// No import map present – that's fine.
		// }

		// Function for resolving paths to a format that satisfies the resolver.
		let resolvePath = (path: string) => asPosix(path);
		const optionalConfig: esbuild.BuildOptions = {};
		if (useDenoResolver) {
			// The Deno path resolver treates the absolute plaths differently
			// than the default ESBuild resolver. For example:
			// "C:/path/to/file" must be changed to "file:///C:/path/to/file".

			resolvePath = (path: string) => toFileUrl(path).href;
			optionalConfig.plugins = denoPlugins({
				configPath,
				// importMapURL // TODO: Removing this comments would enable import maps.
			});
		}

		// Handle multiple entry points by creating a temporary entry file
		const tempEntryFile = join(
			Deno.cwd(),
			`.temp_esbuild_entry_${Date.now()}.ts`
		);
		// Create a temporary entry file that imports all the other files
		const imports = entryPoints
			.map((file) => {
				return `import "${resolvePath(file)}";`;
			})
			.join("\n");

		await Deno.writeTextFile(tempEntryFile, imports);

		// Build with esbuild
		const result = await esbuild.build({
			absWorkingDir: rootDir,
			entryPoints: [resolvePath(tempEntryFile)],
			bundle: true,
			minify: minify,
			format: "esm",
			target: "es2020",
			outfile: esbuildOutFile,
			sourcemap: sourcemap,
			external: externalPackages,
			dropLabels: dropLabels,
			...optionalConfig,
		});

		if (result.errors.length > 0) {
			const error = new ModularMcError(
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
