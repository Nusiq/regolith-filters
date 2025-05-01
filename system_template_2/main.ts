import { processSystemTemplate } from "./map-ts.ts";

if (import.meta.main) {
	const systems = await processSystemTemplate();
	for (const system of systems) {
		await system.apply();
	}
}
