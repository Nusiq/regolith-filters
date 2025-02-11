[
    {
        "source": "replace_json.json",
        "target": "BP/replacements/replace_json.json",
        "replacements": {
            "replace_me_a": "replaced_a",
            "replace_me_b": "replaced_b"
        }
    },
    {
        "source": "replace_py.py",
        "target": "BP/replacements/replace_py.json",
        "replacements": {
            "replace_me_a": "replaced_a",
            "replace_me_b": "replaced_b"
        }
    },
    {
        "source": "replace_mcfunction.mcfunction",
        "target": "BP/replacements/replace_mcfunction.mcfunction",
        "replacements": {
            "replace_me": "replaced"
        }
    },
    {
        "source": "replace_txt.txt",
        "target": "BP/replacements/replace_txt.txt",
        "replacements": {
            "replace_me": "replaced"
        }
    },
    # Repeat to see what happens
    {
        "source": "replace_txt.txt",
        "target": "BP/replacements/replace_txt.txt",
        "on_conflict": "append_end",
        "replacements": {
            "replaced": "this shouldn't happen",
            "replace_me": "replaced 2"
        }
    },
]