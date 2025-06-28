import { asPosix, join } from "./path-utils.ts";
import * as JSONC from "@std/jsonc";

/**
 * Gets the ROOT_DIR environment variable
 * @returns The value of ROOT_DIR
 * @throws Error if ROOT_DIR is not set
 */
export function getRootDir(): string {
	const rootDir = Deno.env.get("ROOT_DIR");
	if (!rootDir) {
		throw new Error("ROOT_DIR environment variable is not set");
	}
	return asPosix(rootDir);
}

/**
 * Gets the original data path from config.json
 * @param rootDir The ROOT_DIR value
 * @returns The original data path
 * @throws Error if config.json cannot be read or dataPath is not found
 */
export async function getDataPath(rootDir: string): Promise<string> {
	const configPath = join(rootDir, "config.json");

	try {
		const configContent = await Deno.readTextFile(configPath);
		const config: any = JSONC.parse(configContent);

		const dataPath = config?.regolith?.dataPath;
		if (!dataPath) {
			throw new Error("Could not find regolith.dataPath in config.json");
		}

		return asPosix(dataPath);
	} catch (error) {
		throw new Error(`Failed to read or parse config.json: ${error}`);
	}
}
