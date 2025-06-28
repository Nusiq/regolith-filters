import { dirname, join, resolve } from "./path-utils.ts";
import { basename, isAbsolute, toFileUrl } from "@std/path";

/**
 * Interface for the auto map entry with target and optional extension
 */
export interface AutoMapEntry {
	path: string;
	extension?: string;
}

/**
 * Type definition for the AUTO_MAP constant
 * Can be either a string (direct target) or an AutoMapEntry object
 */
export type AutoMapType = Record<string, string | AutoMapEntry>;

/**
 * Class responsible for resolving auto paths using the AUTO_MAP configuration
 */
export class AutoMapResolver {
	private autoMap: AutoMapType;

	/**
	 * Creates a new AutoMapResolver with the given AUTO_MAP configuration
	 * @param autoMap The AUTO_MAP configuration
	 */
	constructor(autoMap: AutoMapType) {
		this.autoMap = autoMap;
	}

	/**
	 * Loads the AUTO_MAP from the given path
	 * @param autoMapPath Path to the auto-map.ts file
	 * @returns Promise<AutoMapResolver> A promise that resolves to the AutoMapResolver
	 */
	static async fromFile(autoMapPath: string): Promise<AutoMapResolver> {
		try {
			// Ensure the path is absolute before converting to URL
			const absolutePath = isAbsolute(autoMapPath)
				? autoMapPath
				: resolve(Deno.cwd(), autoMapPath);

			// Import the auto-map.ts file using URL format
			const fileUrl = toFileUrl(absolutePath).href;
			const autoMapModule = await import(fileUrl);

			if (!autoMapModule.AUTO_MAP) {
				throw new Error(`AUTO_MAP not found in ${autoMapPath}`);
			}

			return new AutoMapResolver(autoMapModule.AUTO_MAP);
		} catch (error: unknown) {
			const errorMessage =
				error instanceof Error ? error.message : String(error);
			throw new Error(
				`Failed to load AUTO_MAP from ${autoMapPath}: ${errorMessage}`
			);
		}
	}

	/**
	 * Finds the matching pattern for a filename by checking endings
	 * @param filename The filename to check
	 * @returns The matching pattern or null if no match found
	 */
	private findMatchingPattern(filename: string): string | null {
		// Use the original order of keys in the autoMap
		const patterns = Object.keys(this.autoMap);

		for (const pattern of patterns) {
			if (filename.endsWith(pattern)) {
				return pattern;
			}
		}

		return null;
	}

	/**
	 * Resolves a source path to a target path using :auto or :autoFlat mode
	 * @param sourcePath The source file path
	 * @param isFlat Whether to use :autoFlat (true) or :auto (false)
	 * @returns The resolved target path or null if no match found
	 */
	resolveAutoPath(sourcePath: string, isFlat: boolean): string | null {
		const filename = basename(sourcePath);
		const matchingPattern = this.findMatchingPattern(filename);

		if (!matchingPattern) {
			return null;
		}

		const mapEntry = this.autoMap[matchingPattern];
		let targetDir: string;
		let targetExtension: string;

		// Determine target directory and extension
		if (typeof mapEntry === "string") {
			targetDir = mapEntry;
			targetExtension = ""; // Keep original extension
		} else {
			targetDir = mapEntry.path;
			targetExtension = mapEntry.extension || "";
		}

		// Get the base filename without the matching pattern
		let baseFilename = filename.slice(
			0,
			filename.length - matchingPattern.length
		);

		// Add the target extension if specified, otherwise keep original extension
		if (targetExtension) {
			baseFilename += targetExtension;
		} else {
			baseFilename += matchingPattern;
		}

		// For :auto mode, preserve the directory structure if it exists
		// For :autoFlat, put the file directly in the target directory
		if (!isFlat) {
			const sourceDir = dirname(sourcePath);
			// Only include the directory part if it's not empty and not the current directory
			if (sourceDir && sourceDir !== "." && sourceDir !== "./") {
				// If sourceDir contains '/./' or begins with './', normalize it
				const normalizedSourceDir = sourceDir
					.replace(/^\.\//g, "") // Remove leading ./
					.replace(/\/\.\//g, "/"); // Replace /./ with /

				return join(targetDir, normalizedSourceDir, baseFilename);
			}
		}

		return join(targetDir, baseFilename);
	}
}
