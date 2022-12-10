{
	"format_version": "1.10.0",
	"minecraft:client_entity": {
		"description": {
			"identifier": f"{namespace}:pig_{color}",
			"min_engine_version": "1.8.0",
			"materials": {
				"default": "pig"
			},
			"textures": {
				"default": f"textures/entity/pig_color/{color}"
			},
			"geometry": {
				"default": "geometry.pig.v1.8"
			},
			"animations": {
				"setup": "animation.pig.setup",
				"walk": "animation.quadruped.walk",
				"look_at_target": "animation.common.look_at_target",
				"baby_transform": "animation.pig.baby_transform"
			},
			"scripts": {
				"animate": [
					"setup",
					{
						"walk": "query.modified_move_speed"
					},
					"look_at_target",
					{
						"baby_transform": "query.is_baby"
					}
				]
			},
			"render_controllers": [
				"controller.render.pig_color"
			],
			"spawn_egg": {
				"base_color": rgb,
				"overlay_color": "#000000"
			}
		}
	}
}