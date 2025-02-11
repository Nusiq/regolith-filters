[
    {
        "source": "glow.particle.json",
        "json_template": True,
        "scope": {
            'identifier': f"nusiq:{color['color_name']}_glow",
            'color_r': color['color_r'],
            'color_g': color['color_g'],
            'color_b': color['color_b']
        },
        "target": {
            "dir": AUTO_FLAT,
            "stem": f"{color['color_name']}_glow"
        }
    }
    for color in colors
]