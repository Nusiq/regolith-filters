export const namespace = "my_namespace";
export const AUTO_MAP = {
	".bp_ac.json": "BP/animation_controllers",
	".bp_anim.json": "BP/animations",
	".biome.json": "BP/biomes",
	".block.json": "BP/blocks",
	".dialogue.json": "BP/dialogue",
	".behavior.json": "BP/entities",
	".feature_rule.json": {
		path: "BP/feature_rules",
		extension: ".json",
	},
	".feature.json": {
		path: "BP/features",
		extension: ".json",
	},
	".mcfunction": `BP/functions/${namespace}`,
	".bp_item.json": "BP/items",
	".item.json": "BP/items",
	".loot.json": {
		path: `BP/loot_tables/${namespace}`,
		extension: ".json",
	},
	".recipe.json": "BP/recipes",
	".spawn_rule.json": "BP/spawn_rules",
	".mcstructure": `BP/structures/${namespace}`,
	".jigsaw.json": {
		path: "BP/worldgen/structures",
		extension: ".json",
	},
	".template_pool.json": {
		path: "BP/worldgen/template_pools",
		extension: ".json",
	},
	".structure_set.json": {
		path: "BP/worldgen/structure_sets",
		extension: ".json",
	},
	".trade.json": `BP/trading/${namespace}`,
	".rp_ac.json": "RP/animation_controllers",
	".animation.json": "RP/animations",
	".attachable.json": "RP/attachables",
	".entity.json": "RP/entity",
	".rpe.json": "RP/entity",
	".fog.json": "RP/fogs",
	".rp_item.json": "RP/items",
	".geo.json": "RP/models/entity",
	".particle.json": "RP/particles",
	".rc.json": "RP/render_controllers",
	".fsb": `RP/sounds/${namespace}`,
	".mp4": `RP/sounds/${namespace}`,
	".ogg": `RP/sounds/${namespace}`,
	".wav": `RP/sounds/${namespace}`,
	".lang": "RP/texts",
	".attachable.tga": {
		path: `RP/textures/${namespace}/attachables`,
		extension: ".tga",
	},
	".block.tga": {
		path: `RP/textures/${namespace}/blocks`,
		extension: ".tga",
	},
	".item.tga": {
		path: `RP/textures/${namespace}/items`,
		extension: ".tga",
	},
	".entity.tga": {
		path: `RP/textures/${namespace}/entity`,
		extension: ".tga",
	},
	".particle.tga": {
		path: `RP/textures/${namespace}/particle`,
		extension: ".tga",
	},
	".attachable.png": {
		path: `RP/textures/${namespace}/attachables`,
		extension: ".png",
	},
	".attachable.texture_set.json": {
		path: `RP/textures/${namespace}/attachables`,
		extension: ".texture_set.json",
	},
	".block.png": {
		path: `RP/textures/${namespace}/blocks`,
		extension: ".png",
	},
	".block.texture_set.json": {
		path: `RP/textures/${namespace}/blocks`,
		extension: ".texture_set.json",
	},
	".item.png": {
		path: `RP/textures/${namespace}/items`,
		extension: ".png",
	},
	".item.texture_set.json": {
		path: `RP/textures/${namespace}/items`,
		extension: ".texture_set.json",
	},
	".entity.png": {
		path: `RP/textures/${namespace}/entity`,
		extension: ".png",
	},
	".entity.texture_set.json": {
		path: `RP/textures/${namespace}/entity`,
		extension: ".texture_set.json",
	},
	".particle.png": {
		path: `RP/textures/${namespace}/particle`,
		extension: ".png",
	},
	".particle.texture_set.json": {
		path: `RP/textures/${namespace}/particle`,
		extension: ".texture_set.json",
	},
	".ui.png": {
		path: `RP/textures/${namespace}/ui`,
		extension: ".png",
	},
	".js": "data/system_template_esbuild",
	".ts": "data/system_template_esbuild",
	".material": "RP/materials",
};
