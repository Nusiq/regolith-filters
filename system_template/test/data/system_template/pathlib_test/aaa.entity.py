{
	"format_version": "1.19.0",
	"minecraft:client_entity": {
		"description": {
			"identifier": "minecraft:aaa",
			"materials": {
				"default": "entity_custom"
			},
			"textures": {
				p.stem: (Path("textures") / p.with_suffix('')).as_posix()
				for p in Path("pathlib_test").glob("*.png")
			},
			"geometry": {
				"default": "geometry.entity"
			},
			"render_controllers": ["controller.render.default"],
			"spawn_egg": {
				"base_color": "#288483",
				"overlay_color": "#2B7135"
			}
		}
	}
}
