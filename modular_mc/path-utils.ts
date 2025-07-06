import * as stdPath from "@std/path";

/**
 * Ensures a path uses forward slashes regardless of platform
 */
export function asPosix(path: string): string {
	return path.replace(/\\/g, "/");
}

/**
 * Joins path segments and ensures the result uses forward slashes
 */
export function join(...paths: string[]): string {
	return asPosix(stdPath.join(...paths));
}

/**
 * Returns the relative path from 'from' to 'to', as a posix path
 */
export function relative(from: string, to: string): string {
	return asPosix(stdPath.relative(from, to));
}

/**
 * Normalizes a path and ensures the result uses forward slashes
 */
export function normalize(path: string): string {
	return asPosix(stdPath.normalize(path));
}

/**
 * Returns the directory name of a path
 */
export function dirname(path: string): string {
	return asPosix(stdPath.dirname(path));
}

/**
 * Resolves a path to an absolute path
 */
export function resolve(...pathSegments: string[]): string {
	return asPosix(stdPath.resolve(...pathSegments));
}

/**
 * Returns the last portion of a path
 */
export function basename(path: string, suffix?: string): string {
	return asPosix(stdPath.basename(path, suffix));
}
/**
 * Returns the extension of the file, defined as everything after the first dot in the basename.
 * If there is no dot in the basename, returns an emtpy string.
 */
export function suffixes(str: string): string {
	const firstDot = str.indexOf(".");
	if (firstDot === -1) return "";
	return str.slice(firstDot + 1);
}
