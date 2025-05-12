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
