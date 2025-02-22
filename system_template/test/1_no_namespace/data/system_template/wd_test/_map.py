[
    {
        "source": "subpath/wd_test_json.behavior.json",
        "target": AUTO_FLAT,
        "json_template": True,
        "scope": {
            "os": os,
            "mappy_wd": os.getcwd()
        }
    },
    {
        "source": "subpath/wd_test_py.behavior.py",
        "target": AUTO_FLAT,
        "scope": {
            "os": os,
            "mappy_wd": os.getcwd()
        }
    },
    {
        "source": "subpath/wd_test.mcfunction",
        "target": AUTO_FLAT,
        "scope": {
            "os": os,
            "mappy_wd": os.getcwd()
        }
    }
]