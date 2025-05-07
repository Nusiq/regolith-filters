import { processModule } from "./map-ts.ts";

if (import.meta.main) {
	// TODO - reading the scope from a file and the scope property
	const scope = {};
	const modules = await processModule();
	for (const module of modules) {
		await module.apply(scope);
	}
}
