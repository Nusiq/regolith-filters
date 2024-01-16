[
    {
        "file_type": {
            "source": "json",
            "target": "json"
        },
        "source": "item_part1.templ",
        "target": "BP/items/item.templ"
    },
    {
        "file_type": "json", # Short form for {"source": "json", "target": "json"}
        "source": "item_part2.templ",
        "target": "BP/items/item.templ",
        "on_conflict": "merge"
    },
    {
        "file_type": ".json",  # You can use .json instead of json
        "source": "item_part3.templ",
        "target": "BP/items/item.templ",
        "on_conflict": "merge"
    }
]