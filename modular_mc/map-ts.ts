import { walk, WalkEntry } from "@std/fs/walk";
import { expandGlobSync } from "@std/fs/expand-glob";
import { withWdSync } from "./wd-utils.ts";
import { isAbsolute, toFileUrl, extname } from "@std/path";
import { evaluate } from "./json-template.ts";
import { evaluate as evaluateText } from "./text-template.ts";
import { deepMergeObjects, ListMergePolicy } from "./json-merge.ts";
import {
	relative,
	asPosix,
	resolve,
	dirname,
	normalize,
	join,
	basename,
} from "./path-utils.ts";
import { AutoMapResolver } from "./auto-map-resolver.ts";
import * as JSONC from "@std/jsonc";
import { ModularMcError } from "./error.ts";
import dedent from "npm:dedent";

export type OnConflictStrategy =
	| "stop"
	| "skip"
	| "merge"
	| "overwrite"
	| "appendStart"
	| "appendEnd";

// New types for the target property
export interface MapTargetObject {
	path: string;
	subpath?: string;
	name: string;
}
export type MapTarget = string | MapTargetObject;

// The path to the auto-map.ts file - using a function to resolve it at runtime
function getAutoMapFilePath(): string {
	return resolve(Deno.cwd(), "data/modular_mc/auto-map.ts");
}

// Singleton instance of the AutoMapResolver
let autoMapResolver: AutoMapResolver | null = null;

/**
 * Initializes the AutoMapResolver if it hasn't been initialized already
 * @returns Promise<AutoMapResolver> A promise that resolves to the AutoMapResolver
 */
async function getAutoMapResolver(): Promise<AutoMapResolver> {
	if (!autoMapResolver) {
		try {
			autoMapResolver = await AutoMapResolver.fromFile(getAutoMapFilePath());
		} catch (error: unknown) {
			const errorMessage =
				error instanceof Error ? error.message : String(error);
			console.error(`Warning: Failed to load AUTO_MAP: ${errorMessage}`);
			// Create an empty resolver as fallback
			autoMapResolver = new AutoMapResolver({});
		}
	}
	return autoMapResolver;
}

/**
 * Represents a single entry in a _map.ts file
 */
export class MapTsEntry {
	source: string;
	target: MapTarget;
	jsonTemplate: boolean;
	textTemplate: boolean;
	onConflict: OnConflictStrategy;
	fileType?: string;
	scope: Record<string, any>;

	// Used for error reporting only!
	private readonly mapFilePath: string | undefined;

	// Special auto mapping keywords
	private static readonly AUTO_KEYWORD = ":auto";
	private static readonly AUTO_FLAT_KEYWORD = ":autoFlat";

	/**
	 * Creates a new MapTsEntry without validation
	 * @param source Source path or content
	 * @param target Target path in the pack
	 * @param jsonTemplate Whether the source should be processed as a JSON template
	 * @param onConflict How to handle conflicts: "stop" (default), "skip", "merge", or "overwrite"
	 * @param fileType Optional file type override (e.g., "json", "material")
	 * @param scope Optional scope to use for JSON template evaluation
	 * @param mapFilePath Path to the map file (for error reporting)
	 */
	constructor(
		source: string,
		target: MapTarget,
		jsonTemplate: boolean = false,
		textTemplate: boolean = false,
		onConflict: OnConflictStrategy = "stop",
		fileType?: string,
		scope?: Record<string, any>,
		mapFilePath?: string
	) {
		this.source = source;
		this.target = target;
		this.jsonTemplate = jsonTemplate;
		this.textTemplate = textTemplate;
		this.onConflict = onConflict;
		this.fileType = fileType;
		this.scope = scope || {};
		this.mapFilePath = mapFilePath;
	}

	/**
	 * Validates a raw object and returns a list of properly constructed MapTsEntries
	 * If source is a glob pattern, returns one entry per matching file
	 */
	static fromObject(obj: unknown, mapFilePath: string) {
		// First validate the object structure
		const validatedObj = MapTsEntry.validate(obj, mapFilePath);

		const source = validatedObj.source;
		const target = validatedObj.target;
		const jsonTemplate = validatedObj.jsonTemplate || false;
		const textTemplate = validatedObj.textTemplate || false;
		const onConflict = validatedObj.onConflict || "stop";
		const fileType = validatedObj.fileType;
		const scope = validatedObj.scope;

		// Check if source contains glob patterns
		const hasGlobPattern =
			source.includes("*") ||
			source.includes("?") ||
			source.includes("[") ||
			source.includes("{");

		if (hasGlobPattern) {
			// Handle glob pattern
			const entries: MapTsEntry[] = [];
			// const baseDir = dirname(mapFilePath);
			try {
				const resolvedSources: WalkEntry[] = [];
				withWdSync(dirname(mapFilePath), () => {
					for (const entry of expandGlobSync(source)) {
						resolvedSources.push(entry);
					}
				});
				for (const entry of resolvedSources) {
					if (entry.isFile) {
						entries.push(
							new MapTsEntry(
								entry.path,
								target,
								jsonTemplate,
								textTemplate,
								onConflict,
								fileType,
								scope,
								mapFilePath
							)
						);
					}
				}
			} catch (error) {
				throw new ModularMcError(
					dedent`
					Failed to expand glob pattern.
					File: ${mapFilePath}
					Pattern: ${source}`
				).moreInfo(error);
			}
			if (entries.length === 0) {
				console.warn(
					`Warning: Glob pattern '${source}' in ${mapFilePath} matched no files`
				);
			}
			return entries;
		} else {
			// Handle single file
			// If source is already absolute, use it as-is; otherwise resolve relative to map file
			const resolvedSource = isAbsolute(source)
				? source
				: resolve(dirname(mapFilePath), source);

			return [
				new MapTsEntry(
					resolvedSource,
					target,
					jsonTemplate,
					textTemplate,
					onConflict,
					fileType,
					scope,
					mapFilePath
				),
			];
		}
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
		target: MapTarget;
		jsonTemplate?: boolean;
		textTemplate?: boolean;
		onConflict?: OnConflictStrategy;
		fileType?: string;
		scope?: Record<string, any>;
	} {
		// Check if entry is an object with required properties
		if (
			typeof obj !== "object" ||
			obj === null ||
			!("source" in obj) ||
			!("target" in obj) ||
			typeof obj.source !== "string"
		) {
			throw new ModularMcError(
				`Invalid MAP entry. Each entry must have a 'source' (string) ` +
					`and a 'target' (string or object).\n` +
					`File: ${mapFilePath}`
			);
		}

		// Use a type assertion for the whole object
		const {
			source,
			target,
			jsonTemplate,
			textTemplate,
			onConflict,
			fileType,
			scope,
		} = obj as {
			source: string;
			target: MapTarget;
			jsonTemplate?: boolean;
			textTemplate?: boolean;
			onConflict?: OnConflictStrategy;
			fileType?: string;
			scope?: Record<string, any>;
		};

		// Validate target property
		if (typeof target !== "string" && typeof target !== "object") {
			throw new ModularMcError(
				dedent`
				Invalid MAP entry. Target must be a string or an object.
				File: ${mapFilePath}`
			);
		}

		if (typeof target === "object") {
			if (target === null || !("path" in target) || !("name" in target)) {
				throw new ModularMcError(
					dedent`
					Invalid MAP entry. Target object must have 'path' and 'name' properties.
					File: ${mapFilePath}`
				);
			}
			const targetObj = target as MapTargetObject;
			if (
				typeof targetObj.path !== "string" ||
				typeof targetObj.name !== "string"
			) {
				throw new ModularMcError(
					dedent`
					Invalid MAP entry. Target 'path' and 'name' must be strings.
					File: ${mapFilePath}`
				);
			}
			if (
				targetObj.subpath !== undefined &&
				typeof targetObj.subpath !== "string"
			) {
				throw new ModularMcError(
					dedent`
					Invalid MAP entry. Target 'subpath' must be a string.
					File: ${mapFilePath}`
				);
			}
		}

		// Validate jsonTemplate if present
		if (jsonTemplate !== undefined && typeof jsonTemplate !== "boolean") {
			throw new ModularMcError(
				dedent`
				Invalid jsonTemplate property. jsonTemplate must be a boolean.
				File: ${mapFilePath}`
			);
		}

		// Validate textTemplate if present
		if (textTemplate !== undefined && typeof textTemplate !== "boolean") {
			throw new ModularMcError(
				dedent`
				Invalid textTemplate property. textTemplate must be a boolean.
				File: ${mapFilePath}`
			);
		}

		// Validate that jsonTemplate and textTemplate are not both true
		if (jsonTemplate === true && textTemplate === true) {
			throw new ModularMcError(
				dedent`
				Invalid configuration. jsonTemplate and textTemplate cannot both be true.
				File: ${mapFilePath}`
			);
		}

		// Validate onConflict if present
		if (onConflict !== undefined) {
			if (typeof onConflict !== "string") {
				throw new ModularMcError(
					dedent`
					Invalid onConflict property. onConflict must be a string.
					File: ${mapFilePath}`
				);
			}

			// Check if onConflict has valid value
			const validValues = [
				"stop",
				"skip",
				"merge",
				"overwrite",
				"appendStart",
				"appendEnd",
			];
			if (!validValues.includes(onConflict)) {
				throw new ModularMcError(
					dedent`
					Invalid onConflict value.
					Accepted values: ${validValues.join(", ")}
					File: ${mapFilePath}`
				);
			}
		}

		// Validate fileType if present
		if (fileType !== undefined && typeof fileType !== "string") {
			throw new ModularMcError(
				dedent`
				Invalid fileType property. fileType must be a string.
				File: ${mapFilePath}`
			);
		}

		// Validate scope if present
		if (scope !== undefined && typeof scope !== "object") {
			throw new ModularMcError(
				dedent`
				Invalid scope property. scope must be an object.
				File: ${mapFilePath}`
			);
		}

		// If target is a special auto-mapping keyword, it's valid.
		if (
			target === MapTsEntry.AUTO_KEYWORD ||
			target === MapTsEntry.AUTO_FLAT_KEYWORD
		) {
			return {
				source,
				target,
				jsonTemplate,
				textTemplate,
				onConflict,
				fileType,
				scope,
			};
		}

		if (typeof target === "string") {
			// Normalize paths for consistent processing - ensure forward slashes
			const normalizedTarget = asPosix(normalize(target));

			// Validate target path starts with RP/, BP/, or data/
			if (
				!normalizedTarget.startsWith("RP/") &&
				!normalizedTarget.startsWith("BP/") &&
				!normalizedTarget.startsWith("data/")
			) {
				throw new ModularMcError(
					dedent`
					Invalid target path. Target must start with RP/, BP/, or data/.
					Got: ${normalizedTarget}
					File: ${mapFilePath}`
				);
			}
		}

		// Validate source path based on target type and working directory constraints
		if (isAbsolute(source)) {
			// Check if target uses ":auto" (either as string or in object path property)
			const usesAuto =
				target === MapTsEntry.AUTO_KEYWORD ||
				(typeof target === "object" && target.path === MapTsEntry.AUTO_KEYWORD);

			if (usesAuto) {
				throw new ModularMcError(
					dedent`
					Invalid source path. Absolute paths are not allowed when target uses ":auto".
					Got: ${source}
					File: ${mapFilePath}`
				);
			}

			// Ensure absolute path is within the program's working directory
			const workingDir = asPosix(resolve(Deno.cwd()));
			const absoluteSource = asPosix(resolve(source));

			if (
				!absoluteSource.startsWith(workingDir + "/") &&
				absoluteSource !== workingDir
			) {
				throw new ModularMcError(
					`Invalid source path. Absolute paths must be within the ` +
						`filter's working directory.\n` +
						dedent`
					Working directory: ${workingDir}
					Got: ${source}
					File: ${mapFilePath}`
				);
			}
		} else {
			// For relative paths, normalize and check for parent directory references
			const normalizedSource = asPosix(normalize(source));

			// Check if the normalized path contains parent directory references
			if (normalizedSource.includes("..")) {
				throw new ModularMcError(
					dedent`
					Invalid source path. Paths cannot contain parent directory references (..).
					Got: ${source}
					File: ${mapFilePath}`
				);
			}
		}

		return {
			source,
			target,
			jsonTemplate,
			textTemplate,
			onConflict,
			fileType,
			scope,
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
	private isJsonMergeable(sourceType: string, targetType: string): boolean {
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
			this.onConflict !== "overwrite" &&
			this.onConflict !== "appendStart" &&
			this.onConflict !== "appendEnd" &&
			!this.jsonTemplate
		);
	}

	/**
	 * Resolves auto mapping target path if the target is an auto keyword
	 * @returns Promise<string> A promise that resolves to the actual target path
	 * @throws Error if auto mapping fails
	 */
	private async resolveTargetPath(): Promise<string> {
		const resolver = await getAutoMapResolver();
		const sourcePath = this.mapFilePath
			? relative(dirname(this.mapFilePath), this.source)
			: this.source;

		if (typeof this.target === "string") {
			if (
				this.target === MapTsEntry.AUTO_KEYWORD ||
				this.target === MapTsEntry.AUTO_FLAT_KEYWORD
			) {
				const isFlat = this.target === MapTsEntry.AUTO_FLAT_KEYWORD;
				const resolvedPath = resolver.resolveAutoPath(sourcePath, isFlat);
				if (!resolvedPath) {
					throw new ModularMcError(
						dedent`
						Failed to auto-map.
						Source path: ${sourcePath}
						File: ${this.mapFilePath}`
					);
				}
				return resolvedPath;
			}
			//if target is pointing to a directory (using "/" or special
			// ending - '..' or '.'), we need to append the filename
			else if (
				this.target.endsWith("/") ||
				["..", "."].includes(basename(this.target))
			) {
				const filename = basename(this.source);
				return join(this.target, filename);
			}
			return this.target;
		}

		// Handle MapTargetObject
		const { path, subpath, name } = this.target;
		let resolvedPath = path;
		if (
			path === MapTsEntry.AUTO_KEYWORD ||
			path === MapTsEntry.AUTO_FLAT_KEYWORD
		) {
			const isFlat = path === MapTsEntry.AUTO_FLAT_KEYWORD;
			const autoPath = resolver.resolveAutoPath(sourcePath, isFlat);
			if (!autoPath) {
				throw new ModularMcError(
					dedent`
					Failed to auto-map path.
					Source path: ${sourcePath}
					File: ${this.mapFilePath}`
				);
			}
			resolvedPath = dirname(autoPath); // We only need the directory part
		}

		let resolvedName = name;
		if (name === MapTsEntry.AUTO_KEYWORD) {
			const autoName = resolver.resolveAutoPath(sourcePath, false); // Not flat
			if (!autoName) {
				throw new ModularMcError(
					dedent`
					Failed to auto-map name.
					Source path: ${sourcePath}
					File: ${this.mapFilePath}`
				);
			}
			resolvedName = basename(autoName);
		}

		const finalPath = join(resolvedPath, subpath || "", resolvedName);
		return finalPath;
	}

	/**
	 * Applies this entry by copying the source file to the target location.
	 * If jsonTemplate is true, processes the source as a JSON template.
	 * Handles conflicts according to onConflict setting.
	 */
	async apply(): Promise<void> {
		// Get the full path to the source file
		// If source is already absolute, use it as-is; otherwise resolve it
		const sourcePath = isAbsolute(this.source)
			? this.source
			: resolve(this.source);

		// Resolve auto target if needed
		const resolvedTarget = await this.resolveTargetPath();

		// Get the full path to the target file
		const targetPath = resolve(resolvedTarget);

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
			// Check if target is a directory
			const targetStat = await Deno.stat(targetPath);
			if (targetStat.isDirectory) {
				throw new ModularMcError(
					dedent`
					Target path is a directory and cannot be overwritten.
					Path: ${targetPath}
					File: ${this.mapFilePath}`
				);
			}
		}

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
				throw new ModularMcError(`Missing file: ${msgSource}`);
			}
			throw error;
		}

		// For non-JSON files, handle different conflict strategies
		if (!targetExists || this.onConflict === "overwrite") {
			if (this.textTemplate) {
				if (this.isJsonMergeable(sourceType, targetType)) {
					throw new ModularMcError(
						`Cannot use "${this.onConflict}" with JSON files. JSON files ` +
							`can be merged using "merge" option.\n` +
							`File: ${this.mapFilePath}`
					);
				}
				const sourceContent = await Deno.readTextFile(sourcePath);
				const resultContent = evaluateText(sourceContent, this.scope);

				await Deno.mkdir(dirname(targetPath), { recursive: true });
				await Deno.writeTextFile(targetPath, resultContent);
			} else if (this.jsonTemplate) {
				let sourceJSON: any;
				try {
					sourceJSON = JSONC.parse(sourceContent);
				} catch (error: unknown) {
					throw new ModularMcError(
						dedent`
						Failed to parse JSON.
						File: ${sourcePath}`
					).moreInfo(error);
				}
				sourceJSON = evaluate(sourceJSON, this.scope);

				// Write the result to the target file
				await Deno.mkdir(dirname(targetPath), { recursive: true });
				await Deno.writeTextFile(
					targetPath,
					JSON.stringify(sourceJSON, null, "\t")
				);
			} else {
				// Simple copy for new files or overwrite
				await Deno.mkdir(dirname(targetPath), { recursive: true });
				await Deno.copyFile(sourcePath, targetPath);
			}
		} else if (this.onConflict === "appendStart") {
			if (this.isJsonMergeable(sourceType, targetType)) {
				throw new ModularMcError(
					`Cannot use "${this.onConflict}" with JSON files. JSON files ` +
						`can be merged using "merge" option.\n` +
						`File: ${this.mapFilePath}`
				);
			}
			// Read existing target content
			const targetContent = await Deno.readTextFile(targetPath);

			// Process source content if textTemplate is enabled
			let processedSourceContent = sourceContent;
			if (this.textTemplate) {
				processedSourceContent = evaluateText(sourceContent, this.scope);
			}

			// Append source content at the start of target content
			const resultContent = processedSourceContent + targetContent;

			// Write the combined content
			await Deno.mkdir(dirname(targetPath), { recursive: true });
			await Deno.writeTextFile(targetPath, resultContent);
		} else if (this.onConflict === "appendEnd") {
			if (this.isJsonMergeable(sourceType, targetType)) {
				throw new ModularMcError(
					`Cannot use "${this.onConflict}" with JSON files. JSON files ` +
						`can be merged using "merge" option.\n` +
						`File: ${this.mapFilePath}`
				);
			}
			// Read existing target content
			const targetContent = await Deno.readTextFile(targetPath);

			// Process source content if textTemplate is enabled
			let processedSourceContent = sourceContent;
			if (this.textTemplate) {
				processedSourceContent = evaluateText(sourceContent, this.scope);
			}

			// Append source content at the end of target content
			const resultContent = targetContent + processedSourceContent;

			// Write the combined content
			await Deno.mkdir(dirname(targetPath), { recursive: true });
			await Deno.writeTextFile(targetPath, resultContent);
		} else if (this.onConflict === "merge") {
			if (!this.isJsonMergeable(sourceType, targetType)) {
				throw new ModularMcError(
					dedent`
					Cannot merge files with types because of incompatible types.
					Source type: ${sourceType}
					Target type: ${targetType}
					Types that can be merged: json, material
					File: ${this.mapFilePath}`
				);
			}
			// targetExists is ture
			// isJsonMergeable is true
			// Parse the source content as JSON
			let sourceJSON: any;
			try {
				sourceJSON = JSONC.parse(sourceContent);
			} catch (error: unknown) {
				throw new ModularMcError(
					dedent`
					Failed to parse JSON.
					File: ${sourcePath}`
				).moreInfo(error);
			}

			// Apply JSON template if enabled
			if (this.jsonTemplate) {
				sourceJSON = evaluate(sourceJSON, this.scope);
			}

			// Merge with an existing file
			try {
				// Read target file
				const targetContent = await Deno.readTextFile(targetPath);

				try {
					const targetJSON: any = JSONC.parse(targetContent);

					// Merge the files using APPEND for lists
					sourceJSON = deepMergeObjects(
						targetJSON,
						sourceJSON,
						ListMergePolicy.APPEND
					);
				} catch (error: unknown) {
					throw new ModularMcError(
						dedent`
						Failed to parse existing JSON.
						File: ${targetPath}`
					).moreInfo(error);
				}
			} catch (error: unknown) {
				// If error is not related to file not existing, rethrow
				if (!(error instanceof Deno.errors.NotFound)) {
					throw error;
				}
			}

			// Stringify the JSON with nice formatting
			const resultContent = JSON.stringify(sourceJSON, null, "\t");

			// Write the result to the target file
			await Deno.mkdir(dirname(targetPath), { recursive: true });
			await Deno.writeTextFile(targetPath, resultContent);
		} else if (this.onConflict === "stop") {
			throw new ModularMcError(
				`Target file already exists. Use onConflict: "skip", "merge", ` +
					`"overwrite", "appendStart", or "appendEnd" to handle this.\n` +
					`Path: ${targetPath}`
			);
		} else if (this.onConflict === "skip") {
			console.log(
				`Skipped exporting ${sourcePath} to ${targetPath}. Target already exists.`
			);
		} else {
			// Hopefully should never happen, this would be embarassing if it did.

			// TypeScript exhaustive check
			this.onConflict satisfies never;

			throw new ModularMcError(
				dedent`
				Unexpected error. Please report this issue:
				onConflict: ${this.onConflict}
				textTemplate: ${this.textTemplate}
				jsonTemplate: ${this.jsonTemplate}
				targetExists: ${targetExists}
				File: ${this.mapFilePath}`
			);
		}
	}
}

/**
 * Represents a single _map.ts file and its module.
 */
export class MapTs {
	path: string;
	entries: MapTsEntry[];
	scripts: string[] = [];

	private constructor(
		path: string,
		entries: MapTsEntry[],
		scripts: string[] = []
	) {
		this.path = path;
		this.entries = entries;
		this.scripts = scripts;
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

			// Initialize arrays for entries and scripts
			const validatedEntries: MapTsEntry[] = [];
			const scripts: string[] = [];

			// Process MAP if it exists
			if (mapModule.MAP !== undefined) {
				const mapResult = mapModule.MAP;

				// Validate map structure
				if (!Array.isArray(mapResult)) {
					throw new ModularMcError(
						dedent`
						MAP must be an array.
						File: ${mapFilePath}`
					);
				}
				// Validate and process each entry using the MapTsEntry class
				for (const entry of mapResult) {
					validatedEntries.push(...MapTsEntry.fromObject(entry, mapFilePath));
				}
			}

			// Process SCRIPTS if it exists
			if (mapModule.SCRIPTS !== undefined) {
				if (!Array.isArray(mapModule.SCRIPTS)) {
					throw new ModularMcError(
						dedent`
						SCRIPTS must be an array.
						File: ${mapFilePath}`
					);
				}

				// Validate each script is a string and store it directly
				for (const script of mapModule.SCRIPTS) {
					if (typeof script !== "string") {
						throw new ModularMcError(
							dedent`
							Each script in SCRIPTS must be a string.
							File: ${mapFilePath}`
						);
					}

					// Store the path without resolving it
					scripts.push(script);
				}
			}

			// Ensure at least one of MAP or SCRIPTS is present
			if (validatedEntries.length === 0 && scripts.length === 0) {
				console.warn(
					`Warning: ${mapFilePath} does not export either MAP or SCRIPTS`
				);
			}

			return new MapTs(mapFilePath, validatedEntries, scripts);
		} catch (error) {
			// Improve error message for import failures
			if (error instanceof TypeError || error instanceof SyntaxError) {
				throw new ModularMcError(
					dedent`
					Failed to open _map.ts file.
					File: ${mapFilePath}`
				).moreInfo(error);
			}
			throw error;
		}
	}

	/**
	 * Applies the map by copying all source files to their target locations
`	 */
	async apply(): Promise<void> {
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
				await Promise.all(concurrentEntries.map((entry) => entry.apply()));
			} catch (error: unknown) {
				const errorPath = isAbsolute(this.path)
					? this.path
					: asPosix(relative("data/modular_mc", this.path));
				throw new ModularMcError(
					dedent`
					Failed to apply some of the MAP entries.
					File: ${errorPath}`
				).moreInfo(error);
			}
		}

		// Run sequential entries one at a time
		for (const entry of sequentialEntries) {
			try {
				await entry.apply();
			} catch (error: unknown) {
				throw new ModularMcError(
					dedent`
					Failed to apply MAP entry.
					File: ${this.path}`
				).moreInfo(error);
			}
		}
	}

	/**
	 * Resolves script paths to absolute paths based on provided ROOT_DIR and data path from
	 * config.json. These paths lead to the original script files, not temporary files used
	 * during regolith compilation.
	 *
	 * @param rootDir The ROOT_DIR value
	 * @param configJsonDataPath The original data path
	 * @returns Array of absolute paths to the original script files
	 */
	resolveScriptPaths(rootDir: string, configJsonDataPath: string): string[] {
		// Resolve all script paths from all modules
		const resolvedScripts: string[] = [];

		// Get the directory of the _map.ts file
		const mapDir = dirname(this.path);

		// Process each script in the module
		for (const scriptRelativePath of this.scripts) {
			// 1. Resolve the script path relative to the _map.ts file
			const scriptPath = join(mapDir, scriptRelativePath);

			// 2. Get the path relative to the working directory
			// For example, if scriptPath is '/path/to/tmp/data/modules/example/_map.ts',
			// we need to extract the part after 'data/'

			// Find the position of 'data/' in the path
			const dataPrefixIndex = scriptPath.indexOf("data/");
			let moduleRelativePath: string;

			if (dataPrefixIndex !== -1) {
				// Extract the part after 'data/'
				moduleRelativePath = scriptPath.substring(dataPrefixIndex + 5); // 'data/'.length = 5
			} else {
				// If 'data/' is not found, use the relative path as is
				// This shouldn't happen in normal operation, but we'll handle it gracefully
				moduleRelativePath = scriptRelativePath;
				console.warn(
					`Warning: Could not find 'data/' prefix in path: ${scriptPath}`
				);
			}

			// 3. Combine ROOT_DIR + dataPath + moduleRelativePath to get the absolute path to the original file
			const absolutePath = join(
				rootDir,
				configJsonDataPath,
				moduleRelativePath
			);
			resolvedScripts.push(absolutePath);
		}

		return resolvedScripts;
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
	return mapFiles.sort();
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
