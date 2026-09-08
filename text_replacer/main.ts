/**
 * A Regolith filter that replaces all occurrences of a string with another
 * string in the text files of the behavior and the resource packs.
 *
 * The filter walks the pack folders asynchronously (subdirectories are
 * traversed and files are processed in parallel) which makes it much faster
 * than a sequential implementation on big projects.
 *
 * Files that aren't valid UTF-8 (e.g. textures, sounds) are skipped, so the
 * filter never corrupts binary files.
 *
 * The settings are passed by Regolith as a JSON string in the first command
 * line argument. They should contain the following properties:
 * - `replace_from` (required string) - the text to search for.
 * - `replace_to` (required string) - the text to replace it with.
 * - `paths` (optional array of strings) - folders to process, relative to the
 *   working directory of the filter. Defaults to `["RP", "BP"]`.
 */

/** Folders scanned by the filter when the `paths` setting is not provided. */
const DEFAULT_PATHS = ["RP", "BP"];

/** Maximum number of files processed in parallel at the same time. */
const MAX_CONCURRENT_FILES = 64;

export interface TextReplacerSettings {
	replace_from: string;
	replace_to: string;
	paths: string[];
}

/**
 * Decodes with `fatal: true` so that invalid UTF-8 bytes (binary files) throw,
 * just like reading with Python's `UnicodeDecodeError` handling. The BOM is
 * preserved (`ignoreBOM: true`) so it isn't lost when the file is written back.
 */
const utf8Decoder = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true });
const utf8Encoder = new TextEncoder();

/** Prints an error message and stops the filter with a non-zero exit code. */
function fail(message: string): never {
	console.error(message);
	Deno.exit(1);
}

/** Normalizes a user provided folder path to POSIX style without a trailing slash. */
function normalizeDirPath(path: string): string {
	return path.replaceAll("\\", "/").replace(/\/+$/, "");
}

/**
 * Parses and validates the settings of the filter.
 * @param args Command line arguments received from Regolith.
 * @returns The parsed settings.
 */
export function parseSettings(args: string[]): TextReplacerSettings {
	const invalidSettingsMessage =
		"The filter requires providing settings with replace_from and " +
		"replace_to properties.";
	if (args.length === 0) {
		fail(invalidSettingsMessage);
	}
	let input: unknown;
	try {
		input = JSON.parse(args[0]);
	} catch (error) {
		fail(
			`${invalidSettingsMessage}\nFailed to parse the settings as JSON: ${
				error instanceof Error ? error.message : String(error)
			}`
		);
	}
	if (typeof input !== "object" || input === null || Array.isArray(input)) {
		fail(invalidSettingsMessage);
	}
	const settings = input as Record<string, unknown>;
	const replaceFrom = settings["replace_from"];
	const replaceTo = settings["replace_to"];
	if (typeof replaceFrom !== "string") {
		fail("The replace_from property must be a string.");
	}
	if (typeof replaceTo !== "string") {
		fail("The replace_to property must be a string.");
	}
	let paths = DEFAULT_PATHS;
	if (settings["paths"] !== undefined) {
		const rawPaths = settings["paths"];
		if (
			!Array.isArray(rawPaths) ||
			rawPaths.some((path) => typeof path !== "string")
		) {
			fail("The paths property must be an array of strings.");
		}
		paths = (rawPaths as string[]).map(normalizeDirPath);
	}
	return { replace_from: replaceFrom, replace_to: replaceTo, paths };
}

/**
 * Recursively collects the paths of all files inside the given directory.
 * Subdirectories are traversed concurrently. Symlinks are skipped to avoid
 * infinite recursion.
 * @param dir Path of the directory to scan.
 * @param files List that the found file paths are appended to.
 */
export async function collectFiles(dir: string, files: string[]): Promise<void> {
	const subdirTasks: Promise<void>[] = [];
	for await (const entry of Deno.readDir(dir)) {
		const entryPath = `${dir}/${entry.name}`;
		if (entry.isDirectory) {
			subdirTasks.push(collectFiles(entryPath, files));
		} else if (entry.isFile) {
			files.push(entryPath);
		}
	}
	// Awaited after the loop so that all subdirectories are scanned in parallel.
	await Promise.all(subdirTasks);
}

/**
 * Replaces all occurrences of `from` with `to` in a single file.
 * @returns `true` if the file was modified, `false` otherwise. Files that
 * aren't valid UTF-8 are skipped (reported as not modified).
 */
export async function replaceInFile(
	path: string,
	from: string,
	to: string
): Promise<boolean> {
	const bytes = await Deno.readFile(path);
	let text: string;
	try {
		text = utf8Decoder.decode(bytes);
	} catch {
		// Not a valid UTF-8 file (e.g. a texture or a sound). Skip it.
		return false;
	}
	if (!text.includes(from)) {
		return false;
	}
	await Deno.writeFile(path, utf8Encoder.encode(text.replaceAll(from, to)));
	return true;
}

/**
 * Walks all the folders from `settings.paths` and replaces all occurrences of
 * `replace_from` with `replace_to` in the found files. Files are processed in
 * parallel with a bounded concurrency to speed up the I/O.
 * @returns The number of scanned files and the number of modified files.
 */
export async function runReplacement(
	settings: TextReplacerSettings
): Promise<{ scanned: number; modified: number }> {
	const { replace_from, replace_to, paths } = settings;

	// Collect the files from all root folders.
	const files: string[] = [];
	for (const rootDir of paths) {
		let stat: Deno.FileInfo;
		try {
			stat = await Deno.stat(rootDir);
		} catch (error) {
			if (error instanceof Deno.errors.NotFound) {
				console.log(`Folder "${rootDir}" doesn't exist. Skipping it.`);
				continue;
			}
			throw error;
		}
		if (!stat.isDirectory) {
			fail(`The path "${rootDir}" is not a directory.`);
		}
		await collectFiles(rootDir, files);
	}

	// Process the files in parallel using a pool of async workers.
	let nextFileIndex = 0;
	let modified = 0;
	let failure: unknown = undefined;
	const worker = async (): Promise<void> => {
		while (failure === undefined) {
			const index = nextFileIndex++;
			if (index >= files.length) {
				return;
			}
			const path = files[index];
			try {
				if (await replaceInFile(path, replace_from, replace_to)) {
					modified++;
				}
			} catch (error) {
				if (failure === undefined) {
					failure = error;
				}
				return;
			}
		}
	};
	await Promise.all(
		Array.from(
			{ length: Math.min(MAX_CONCURRENT_FILES, files.length) },
			() => worker()
		)
	);
	if (failure !== undefined) {
		fail(
			`Failed to process the files:\n${
				failure instanceof Error ? (failure.stack ?? failure.message) : String(failure)
			}`
		);
	}
	return { scanned: files.length, modified };
}

if (import.meta.main) {
	const settings = parseSettings(Deno.args);
	const { replace_from, replace_to } = settings;
	const { scanned, modified } = await runReplacement(settings);
	console.log(
		`Replaced all occurrences of ${JSON.stringify(replace_from)} with ` +
			`${JSON.stringify(replace_to)} in ${modified} out of ${scanned} files.`
	);
}
