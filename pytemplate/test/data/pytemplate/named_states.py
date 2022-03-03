{
    "component_groups": {
        f"{namespace}:{name}": {
            f"minecraft:{int_component}": {
                "value": i
            }
        } for i, name in enumerate(names)
    },
    "events": {
        f"{namespace}:{name}":{
            "add": {
                "component_groups": [f"{namespace}:{name}"]
            },
            "remove": {
                "component_groups": [f"{namespace}:{name_n}" for name_n in names if name_n != name]
            }
        } for name in names
    }
}