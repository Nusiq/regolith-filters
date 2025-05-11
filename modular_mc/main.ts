import { processModule } from "./map-ts.ts";
import { deepMergeObjects, ListMergePolicy } from "./json-merge.ts";
import { join, isAbsolute } from "@std/path";

if (import.meta.main) {
	let scope: Record<string, any> = {};

	// Get command line arguments
	const args = Deno.args;
	if (args.length > 0) {
		try {
			const input = JSON.parse(args[0]);

			// Handle scope property
			if (input.scope !== undefined) {
				scope = input.scope;
			}

			// Handle scope_path property
			if (input.scope_path !== undefined) {
				// Resolve the path - if not absolute, make it relative to ./data
				const scopePath = isAbsolute(input.scope_path)
					? input.scope_path
					: join("./data", input.scope_path);

				const scopePathContent = await Deno.readTextFile(scopePath);
				const scopePathData = JSON.parse(scopePathContent);

				// Merge scope_path data into scope if both exist
				if (input.scope !== undefined) {
					scope = deepMergeObjects(
						scope,
						scopePathData,
						ListMergePolicy.GREATER_LENGTH
					);
				} else {
					scope = scopePathData;
				}
			}
		} catch (error) {
			console.error("Error processing input:", error);
			Deno.exit(1);
		}
	}

	const modules = await processModule();
	for (const module of modules) {
		try {
			await module.apply(scope);
		} catch (error: unknown) {
			const errorMessage =
				error instanceof Error ? error.message : String(error);
			console.error(errorMessage);
			Deno.exit(1);
		}
	}
}
