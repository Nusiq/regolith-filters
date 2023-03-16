[
    {
        "source": "aaa.entity.py",
        "target": "RP/entity/aaa.entity.json",
    },
    {
        "source": "bbb.entity.py",
        "target": "RP/entity/bbb.entity.json",
        "scope": {
            "textures": {
                p.stem: (Path("textures") / p.with_suffix('')).as_posix()
                for p in Path("pathlib_test").glob("*.png")
            }
        }
    },
    {
        "source": "pathlib_func.mcfunction",
        "target": AUTO,
        "scope": {
            "textures": [
                p.with_suffix('').as_posix()
                for p in Path("pathlib_test").glob("*.png")
            ]
        }
    },
]