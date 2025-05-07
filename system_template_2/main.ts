import { processSystemTemplate } from "./map-ts.ts";

if (import.meta.main) {
	// TODO - reading the scope from a file and the scope property
	const scope = {};
	const systems = await processSystemTemplate();
	for (const system of systems) {
		await system.apply(scope);
	}
}
