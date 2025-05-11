import { processModule } from "./map-ts.ts";

if (import.meta.main) {
	// TODO - reading the scope from a file and the scope property
	const scope = {};
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
