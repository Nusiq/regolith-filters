import { assertEquals } from "@std/assert";
import { AutoMapResolver, AutoMapType } from "./auto-map-resolver.ts";

// Test auto map data
const TEST_AUTO_MAP: AutoMapType = {
	".geo.json": "RP/models/entity",
	".block.json": "BP/blocks",
	".item.png": {
		target: "RP/textures/items",
		extension: ".png",
	},
	".entity.tga": {
		target: "RP/textures/entity",
		extension: ".tga",
	},
	".mc.language.json": {
		target: "texts/languages",
		extension: ".lang",
	},
	// Order matters - this should match before .json
	".special.json": "data/special",
	// This is a more general pattern and will only match if no more specific patterns match
	".json": "data/general",
};

// Basic mapping test
Deno.test("resolveAutoPath - basic string mapping", () => {
	const resolver = new AutoMapResolver(TEST_AUTO_MAP);
	const result = resolver.resolveAutoPath("mymodel.geo.json", false);
	assertEquals(result, "RP/models/entity/mymodel.geo.json");
});

// Test with :auto (preserve directory structure)
Deno.test("resolveAutoPath - preserve directory structure with :auto", () => {
	const resolver = new AutoMapResolver(TEST_AUTO_MAP);
	const result = resolver.resolveAutoPath("mobs/dragon/dragon.geo.json", false);
	assertEquals(result, "RP/models/entity/mobs/dragon/dragon.geo.json");
});

// Test with :autoFlat (flatten directory structure)
Deno.test(
	"resolveAutoPath - flatten directory structure with :autoFlat",
	() => {
		const resolver = new AutoMapResolver(TEST_AUTO_MAP);
		const result = resolver.resolveAutoPath(
			"mobs/dragon/dragon.geo.json",
			true
		);
		assertEquals(result, "RP/models/entity/dragon.geo.json");
	}
);

// Test object-based mappings with extension replacement
Deno.test("resolveAutoPath - extension replacement", () => {
	const resolver = new AutoMapResolver(TEST_AUTO_MAP);
	const result = resolver.resolveAutoPath("sword.item.png", false);
	assertEquals(result, "RP/textures/items/sword.png");
});

// Test unknown file extensions
Deno.test("resolveAutoPath - unknown extension returns null", () => {
	const resolver = new AutoMapResolver(TEST_AUTO_MAP);
	const result = resolver.resolveAutoPath("unknown.xyz", false);
	assertEquals(result, null);
});

// Test complex file endings (multiple dots)
Deno.test("resolveAutoPath - complex file endings", () => {
	const resolver = new AutoMapResolver(TEST_AUTO_MAP);
	const result = resolver.resolveAutoPath("en_US.mc.language.json", false);
	assertEquals(result, "texts/languages/en_US.lang");
});

// Test order matters
Deno.test("resolveAutoPath - order matters for overlapping patterns", () => {
	const resolver = new AutoMapResolver(TEST_AUTO_MAP);

	// Should match .special.json, not .json
	const resultSpecial = resolver.resolveAutoPath("config.special.json", false);
	assertEquals(resultSpecial, "data/special/config.special.json");

	// Should match .json as fallback
	const resultGeneral = resolver.resolveAutoPath("simple.json", false);
	assertEquals(resultGeneral, "data/general/simple.json");
});
