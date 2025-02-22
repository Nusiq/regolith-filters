[
    # Json files
    {
        "source": "python_script_no_output.behavior.json",
        "target": AUTO_FLAT,
        "python_script": True
    },
    {
        "source": "python_script.behavior.json",
        "target": AUTO_FLAT,
        "python_script": True,
        "json_template": True,
        "scope": {
            "variable_from_scope": 1234
        }
    },
    {
        "source": "python_script.mcfunction",
        "target": AUTO_FLAT,
        "python_script": True,
        "scope": {
            "variable_from_scope": 1234
        }
    },
]