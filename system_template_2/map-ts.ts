import { walk } from "@std/fs/walk";
import { isAbsolute, normalize, resolve, toFileUrl, dirname } from "@std/path";

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

	/**
	 * Creates a new MapTsEntry without validation
	 * @param source Source path or content
	 * @param target Target path in the pack
	 */
	constructor(source: string, target: string) {
		this.source = source;
		this.target = target;
	}

	/**
	 * Validates a raw object and returns a properly constructed MapTsEntry
	 */
	static fromObject(obj: unknown, mapFilePath: string): MapTsEntry {
		// First validate the object structure
		const validatedObj = MapTsEntry.validate(obj, mapFilePath);

		const source = validatedObj.source;
		const target = validatedObj.target;

		// Create the entry
		return new MapTsEntry(resolve(dirname(mapFilePath), source), target);
	}

	/**
	 * Validates a raw object and returns it as a valid entry object
	 * Throws an error if validation fails
	 */
	private static validate(
		obj: unknown,
		mapFilePath: string
	): { source: string; target: string } {
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
		const { source, target } = obj as { source: string; target: string };

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

		return { source, target };
	}

	/**
	 * Checks if this entry can be safely run concurrently with other entries
	 * @returns true if the entry can be run concurrently, false otherwise
	 */
	canRunConcurrently(): boolean {
		// For now, all entries can run concurrently
		return true;
	}

	/**
	 * Applies this entry by copying the source file to the target location.
	 */
	async apply(): Promise<void> {
		// Get the full path to the source file
		const sourcePath = resolve(this.source);

		// Get the full path to the target file
		const targetPath = resolve(this.target);

		// Ensure the target directory exists
		await Deno.mkdir(dirname(targetPath), { recursive: true });

		// Copy the file
		await Deno.copyFile(sourcePath, targetPath);
	}
}

/**
 * Represents a single _map.ts file as a system
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
	 * @param outputDir The root directory where the files should be copied to
	 */
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
			const copyPromises = concurrentEntries.map((entry) => entry.apply());
			await Promise.all(copyPromises);
		}

		// Run sequential entries one at a time
		for (const entry of sequentialEntries) {
			await entry.apply();
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
 */
export async function processSystemTemplate(
	rootDir: string = "data/system_template_2"
): Promise<MapTs[]> {
	// Normalize the root directory path - ensure forward slashes
	const normalizedRootDir = asPosix(normalize(rootDir));
	const mapFiles = await findMapFiles(normalizedRootDir);
	const systems: MapTs[] = [];

	for (const mapFile of mapFiles) {
		const system = await MapTs.fromFile(mapFile);
		systems.push(system);
	}

	return systems;
}
