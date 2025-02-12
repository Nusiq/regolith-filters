[
    *[{
        "source": "on_conflict.txt",
        "on_conflict": "append_start",
        "target": "BP/on_conflict.txt"
    } for _ in range(10)],
    *[{
        "source": "on_conflict.mcfunction",
        "on_conflict": "append_end",
        "target": AUTO_FLAT
    } for _ in range(10)],
    *[{
        "source": "on_conflict.behavior.json",
        "on_conflict": "merge",
        "json_template": True,
        "scope": {
            "event": f"my_event_{i}"
        },
        "target": AUTO_FLAT
    } for i in range(10)]
]