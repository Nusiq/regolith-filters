[
    {
        "source": "simple_block.feature.json",
        "json_template": True,
        "scope": {
            'identifier': f"nusiq:{block}",
            'block': f"minecraft:{block}"
        },
        "target": {
            "dir": AUTO_FLAT,
            "stem": block
        }
    }
    for block in ['diamond_block', 'stone', 'emerald_block']
]