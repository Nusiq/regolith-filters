[
    
    {
        # First export, there shouldn't be any conflicts
        "source": "on_conflict_overwrite.behavior.json",
        "target": AUTO_FLAT,
        "on_conflict": "overwrite"
    },
    {
        # Second export conflict
        "source": "on_conflict_overwrite.behavior.json",
        "target": AUTO_FLAT,
        "on_conflict": "overwrite"
    },
    {
        # Third export just for a good measure
        "source": "on_conflict_overwrite.behavior.json",
        "target": AUTO_FLAT,
        "on_conflict": "overwrite"
    }
]