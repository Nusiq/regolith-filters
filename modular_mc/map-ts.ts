import { walk } from "@std/fs/walk";
import {
	isAbsolute,
	normalize,
	resolve,
	toFileUrl,
	dirname,
	extname,
	relative,
} from "@std/path";
import { evaluate } from "./json-template.ts";
import { deepMergeObjects, ListMergePolicy } from "./json-merge.ts";

/**
 * Ensures a path uses forward slashes regardless of platform
 */
function asPosix(path: string): string {
	return path.replace(/\\/g, "/");
}

/**
 * Represents a single entry in a _map.ts file
 */
export class MapTsEntry {
	source: string;
	target: string;
	jsonTemplate: boolean;
	onConflict: string;
	fileType?: string;

	// Used for error reporting only!
	private readonly mapFilePath: string | undefined;

	/**
	 * Creates a new MapTsEntry without validation
	 * @param source Source path or content
	 * @param target Target path in the pack
	 * @param jsonTemplate Whether the source should be processed as a JSON template
	 * @param onConflict How to handle conflicts: "stop" (default), "skip", or "merge"
	 * @param fileType Optional file type override (e.g., "json", "material")
	 */
	constructor(
		source: string,
		target: string,
		jsonTemplate: boolean = false,
		onConflict: string = "stop",
		fileType?: string,
		mapFilePath?: string
	) {
		this.source = source;
		this.target = target;
		this.jsonTemplate = jsonTemplate;
		this.onConflict = onConflict;
		this.fileType = fileType;
		this.mapFilePath = mapFilePath;
	}

	/**
	 * Validates a raw object and returns a properly constructed MapTsEntry
	 */
	static fromObject(obj: unknown, mapFilePath: string): MapTsEntry {
		// First validate the object structure
		const validatedObj = MapTsEntry.validate(obj, mapFilePath);

		const source = validatedObj.source;
		const target = validatedObj.target;
		const jsonTemplate = validatedObj.jsonTemplate || false;
		const onConflict = validatedObj.onConflict || "stop";
		const fileType = validatedObj.fileType;

		// Create the entry
		return new MapTsEntry(
			resolve(dirname(mapFilePath), source),
			target,
			jsonTemplate,
			onConflict,
			fileType,
			mapFilePath
		);
	}

	/**
	 * Validates a raw object and returns it as a valid entry object
	 * Throws an error if validation fails
	 */
	private static validate(
		obj: unknown,
		mapFilePath: string
	): {
		source: string;
		target: string;
		jsonTemplate?: boolean;
		onConflict?: string;
		fileType?: string;
	} {
		// Check if entry is an object with required properties
		if (
			typeof obj !== "object" ||
			obj === null ||
			!("source" in obj) ||
			!("target" in obj) ||
			typeof obj.source !== "string" ||
			typeof obj.target !== "string"
		) {
			throw new Error(
				`Invalid MAP entry in ${mapFilePath}. Each entry must have source and target properties as strings.`
			);
		}

		// Extract values for additional validation
		const { source, target, jsonTemplate, onConflict, fileType } = obj as {
			source: string;
			target: string;
			jsonTemplate?: boolean;
			onConflict?: string;
			fileType?: string;
		};

		// Validate jsonTemplate if present
		if (jsonTemplate !== undefined && typeof jsonTemplate !== "boolean") {
			throw new Error(
				`Invalid jsonTemplate property in ${mapFilePath}. jsonTemplate must be a boolean.`
			);
		}

		// Validate onConflict if present
		if (onConflict !== undefined) {
			if (typeof onConflict !== "string") {
				throw new Error(
					`Invalid onConflict property in ${mapFilePath}. onConflict must be a string.`
				);
			}

			// Check if onConflict has valid value
			const validValues = ["stop", "skip", "merge"];
			if (!validValues.includes(onConflict)) {
				throw new Error(
					`Invalid onConflict value in ${mapFilePath}. Must be one of: ${validValues.join(
						", "
					)}. Got: ${onConflict}`
				);
			}
		}

		// Validate fileType if present
		if (fileType !== undefined && typeof fileType !== "string") {
			throw new Error(
				`Invalid fileType property in ${mapFilePath}. fileType must be a string.`
			);
		}

		// Normalize paths for consistent processing - ensure forward slashes
		const normalizedTarget = asPosix(normalize(target));

		// Validate target path starts with RP/, BP/, or data/
		if (
			!normalizedTarget.startsWith("RP/") &&
			!normalizedTarget.startsWith("BP/") &&
			!normalizedTarget.startsWith("data/")
		) {
			throw new Error(
				`Invalid target path in ${mapFilePath}. Target must start with RP/, BP/, or data/. Got: ${normalizedTarget}`
			);
		}

		// Validate source path is relative and doesn't contain parent directory references
		if (isAbsolute(source)) {
			throw new Error(
				`Invalid source path in ${mapFilePath}. Absolute paths are not allowed. Got: ${source}`
			);
		}

		// Normalize the source path for consistent analysis - ensure forward slashes
		const normalizedSource = asPosix(normalize(source));

		// Check if the normalized path contains parent directory references
		if (normalizedSource.includes("..")) {
			throw new Error(
				`Invalid source path in ${mapFilePath}. Paths cannot contain parent directory references (..). Got: ${source}`
			);
		}

		return {
			source,
			target,
			jsonTemplate,
			onConflict,
			fileType,
		};
	}

	/**
	 * Gets the file type for a path, respecting fileType overrides
	 * @param path The file path
	 * @param typeOverride Optional type override
	 */
	private getFileType(path: string, typeOverride?: string): string {
		if (typeOverride) {
			return typeOverride;
		}

		// Extract extension without the dot
		const extension = extname(path).slice(1).toLowerCase();
		return extension;
	}

	/**
	 * Determines if a file is mergeable based on its type
	 * @param sourceType The source file type
	 * @param targetType The target file type
	 */
	private isMergeable(sourceType: string, targetType: string): boolean {
		// Currently only JSON and material files are mergeable
		const mergeableTypes = ["json", "material"];
		return (
			mergeableTypes.includes(sourceType) && mergeableTypes.includes(targetType)
		);
	}

	/**
	 * Checks if this entry can be safely run concurrently with other entries
	 * @returns true if the entry can be run concurrently, false otherwise
	 */
	canRunConcurrently(): boolean {
		// Files that need to be merged cannot run concurrently as they depend
		// on the previous files being created first.
		// Files that use JSON templates cannot run concurrently because they
		// may internally have dependencies on other files.
		return (
			this.onConflict !== "merge" &&
			this.onConflict !== "skip" &&
			!this.jsonTemplate
		);
	}

	/**
	 * Applies this entry by copying the source file to the target location.
	 * If jsonTemplate is true, processes the source as a JSON template.
	 * Handles conflicts according to onConflict setting.
	 * @param scope Optional scope to use for JSON template evaluation
	 */
	async apply(scope: Record<string, any> = {}): Promise<void> {
		// Get the full path to the source file
		const sourcePath = resolve(this.source);

		// Get the full path to the target file
		const targetPath = resolve(this.target);

		// Get file types
		const sourceType = this.getFileType(sourcePath, this.fileType);
		const targetType = this.getFileType(targetPath, this.fileType);

		// Check if target file exists
		const targetExists = await Deno.stat(targetPath).then(
			() => true,
			() => false
		);

		// Handle conflict if target exists
		if (targetExists) {
			if (this.onConflict === "stop") {
				throw new Error(
					`Target file already exists: ${targetPath}. Use onConflict: "skip" or "merge" to handle this.`
				);
			} else if (this.onConflict === "skip") {
				console.log(
					`Skipped exporting ${sourcePath} to ${targetPath}. Target already exists.`
				);
				return;
			} else if (this.onConflict === "merge") {
				// Check if files are mergeable
				if (!this.isMergeable(sourceType, targetType)) {
					throw new Error(
						`Cannot merge files with types ${sourceType} and ${targetType}. Only json and material files can be merged.`
					);
				}

				// Continue with merge operations below
			}
		}

		// Ensure the target directory exists
		await Deno.mkdir(dirname(targetPath), { recursive: true });

		// Read the source file content
		let sourceContent: string;
		try {
			sourceContent = await Deno.readTextFile(sourcePath);
		} catch (error) {
			if (error instanceof Deno.errors.NotFound) {
				// If we can we use relative path in the message
				const msgSource =
					this.mapFilePath === undefined
						? this.source
						: asPosix(relative(dirname(this.mapFilePath), sourcePath));
				throw new Error(`Missing file: ${msgSource}`);
			}
			throw error;
		}

		// Handle JSON files
		if (sourceType === "json" || targetType === "json") {
			// Parse the source content as JSON
			let sourceJSON;
			try {
				sourceJSON = JSON.parse(sourceContent);
			} catch (error: unknown) {
				throw new Error(`Failed to parse JSON at ${sourcePath}: ${error}`);
			}

			// Apply JSON template if enabled
			if (this.jsonTemplate) {
				sourceJSON = evaluate(sourceJSON, scope);
			}

			// Check if we need to merge with an existing file
			if (targetExists && this.onConflict === "merge") {
				try {
					// Read target file
					const targetContent = await Deno.readTextFile(targetPath);

					try {
						const targetJSON = JSON.parse(targetContent);

						// Merge the files using APPEND for lists
						sourceJSON = deepMergeObjects(
							targetJSON,
							sourceJSON,
							ListMergePolicy.APPEND
						);
					} catch (error: unknown) {
						throw new Error(
							`Failed to parse existing JSON at ${targetPath}: ${error}`
						);
					}
				} catch (error: unknown) {
					// If error is not related to file not existing, rethrow
					if (!(error instanceof Deno.errors.NotFound)) {
						throw error;
					}
				}
			}

			// Stringify the JSON with nice formatting
			const resultContent = JSON.stringify(sourceJSON, null, "\t");

			// Write the result to the target file
			await Deno.writeTextFile(targetPath, resultContent);
		} else {
			// For non-JSON files, just copy the file if it doesn't exist or onConflict is merge
			if (!targetExists || this.onConflict !== "merge") {
				await Deno.copyFile(sourcePath, targetPath);
			}
		}
	}
}

/**
 * Represents a single _map.ts file and its module.
 */
export class MapTs {
	path: string;
	entries: MapTsEntry[];

	constructor(path: string, entries: MapTsEntry[]) {
		this.path = path;
		this.entries = entries;
	}

	/**
	 * Creates a MapTs by evaluating the _map.ts file
	 */
	static async fromFile(mapFilePath: string): Promise<MapTs> {
		// Normalize the path to handle any platform-specific issues - ensure forward slashes
		const normalizedPath = asPosix(normalize(mapFilePath));

		// Ensure we have an absolute path by resolving relative to current working directory if needed
		const absolutePath = isAbsolute(normalizedPath)
			? normalizedPath
			: asPosix(resolve(Deno.cwd(), normalizedPath));

		// Convert to file URL for direct importing
		const fileUrl = toFileUrl(absolutePath).href;

		try {
			// Directly import the map file
			const mapModule = await import(fileUrl);

			// Check if MAP is exported
			if (!mapModule.MAP) {
				throw new Error(`${mapFilePath} must export a MAP array`);
			}

			const mapResult = mapModule.MAP;

			// Validate map structure
			if (!Array.isArray(mapResult)) {
				throw new Error(`MAP must be an array in ${mapFilePath}`);
			}

			// Validate and process each entry using the MapTsEntry class
			const validatedEntries: MapTsEntry[] = mapResult.map((entry) =>
				MapTsEntry.fromObject(entry, mapFilePath)
			);

			return new MapTs(mapFilePath, validatedEntries);
		} catch (error) {
			// Improve error message for import failures
			if (error instanceof TypeError || error instanceof SyntaxError) {
				throw new Error(`Failed to import ${mapFilePath}: ${error.message}`);
			}
			throw error;
		}
	}

	/**
	 * Applies the map by copying all source files to their target locations
	 * @param scope Optional scope to use for JSON template evaluation
	 */
	async apply(scope: Record<string, any> = {}): Promise<void> {
		// Process each entry
		// Split entries into those that can and cannot run concurrently
		const concurrentEntries: MapTsEntry[] = [];
		const sequentialEntries: MapTsEntry[] = [];

		for (const entry of this.entries) {
			if (entry.canRunConcurrently()) {
				concurrentEntries.push(entry);
			} else {
				sequentialEntries.push(entry);
			}
		}

		// Run concurrent entries in parallel
		if (concurrentEntries.length > 0) {
			try {
				await Promise.all(concurrentEntries.map((entry) => entry.apply(scope)));
			} catch (error: unknown) {
				const errorMessage =
					error instanceof Error ? error.message : String(error);
				const path = asPosix(relative("data/modular_mc", this.path));
				throw new Error(`Error in map file ${path}:\n` + `  ${errorMessage}`);
			}
		}

		// Run sequential entries one at a time
		for (const entry of sequentialEntries) {
			try {
				await entry.apply(scope);
			} catch (error: unknown) {
				const errorMessage =
					error instanceof Error ? error.message : String(error);
				throw new Error(
					`Error in map file ${this.path}:\n` + `  ${errorMessage}`
				);
			}
		}
	}
}

export async function findMapFiles(rootDir: string): Promise<string[]> {
	const mapFiles: string[] = [];
	try {
		const stat = await Deno.stat(rootDir);
		if (!stat.isDirectory) {
			return mapFiles;
		}
	} catch {
		// Directory doesn't exist
		return mapFiles;
	}
	for await (const entry of walk(rootDir, { includeDirs: false })) {
		if (entry.name === "_map.ts") {
			mapFiles.push(asPosix(entry.path));
		}
	}
	return mapFiles;
}

/**
 * Processes all _map.ts files in the given directory and returns a list of MapTs objects
 * @param rootDir The root directory to search for _map.ts files
 */
export async function processModule(
	rootDir: string = "data/modular_mc"
): Promise<MapTs[]> {
	// Normalize the root directory path - ensure forward slashes
	const normalizedRootDir = asPosix(normalize(rootDir));
	const mapFiles = await findMapFiles(normalizedRootDir);
	const modules: MapTs[] = [];

	for (const mapFile of mapFiles) {
		const module = await MapTs.fromFile(mapFile);
		modules.push(module);
	}

	return modules;
}
