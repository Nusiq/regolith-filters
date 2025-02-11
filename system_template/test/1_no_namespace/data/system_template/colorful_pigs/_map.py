[
    {
        # Python files are evaluated and dumped as JSON
        "source": "pig_.behavior.py",
        "target": f"BP/entities/pig_{color}.behavior.json",

        # Custom scope used for evaluation (merged with global scope). Sope
        # is optional. We're passing the color and rgb so that in the behavior
        # we know which color we're dealing with.
        "scope": {"color":color, "rgb": rgb},

        # If file already exists, merge it. The pig_blue.behavior.json exists
        # in BP/entities in this exmaple.
        "on_conflict": "merge"
    }  for color, rgb in colors
] + [
    {
        "source": "pig_.entity.py",
        "target": f"RP/entity/pig_{color}.entity.json",
        "scope": {"color":color, "rgb": rgb},
    } for color, rgb in colors
] + [
    {
        # Basic JSON file can just be copied (don't need scope because
        # there is no evaluation)
        "source": "pig_color.rc.json",
        "target": AUTO #  Equivalent to "RP/render_controllers/pig_color.rc.json"
    }
] + [
    {
        "source": f"pig_{color}.png",  # Any type of file is supported
        "target": f"RP/textures/entity/pig_color/{color}.png",
    } for color, _ in colors
]
