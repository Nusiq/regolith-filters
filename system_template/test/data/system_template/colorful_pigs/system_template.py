[
    {
        "source": "behavior.py",  # Python files can be are evaluated and dumped as JSON
        "target": f"BP/entities/pig_{color}.behavior.json",
        "scope": {"color":color, "rgb": rgb, "namespace": namespace},  # The scope used during evaluation
        "on_conflict": "merge"  # How to handle files that already exist in the poject
    }  for color, rgb in colors
] + [
    {
        "source": "client_entity.py",
        "target": f"RP/entity/pig_{color}.entity.json",
        "scope": {"color":color, "rgb": rgb},
        "use_global_scope": true  # In previous example the 'namespace' was passed by specific values. Here we entire global scope (this is less efficient)
    } for color, rgb in colors
] + [
    {
        "source": "rc.json",  # Basic JSON file can just be copied (don't need scope because there is no evaluation)
        "target": f"RP/render_controllers/pig_color.rc.json"
    }
] + [
    {
        "source": f"pig_{color}.png",  # Any type of file is supported
        "target": f"RP/textures/entity/pig_color/{color}.png",
    } for color, _ in colors
]
