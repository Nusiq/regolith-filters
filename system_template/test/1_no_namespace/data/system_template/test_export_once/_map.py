[
    # This system tests the "export_once" feature. The repeated export should
    # only be exported once. The behavior uses type_family, which would be
    # duplicated if the export_once feature was not working.
    {
        "source": "test_export_once.behavior.json",
        "target": AUTO_FLAT,
    },
    {
        "source": "test_export_once_extension.behavior.json",
        "target": "BP/entities/test_export_once.behavior.json",
        "on_conflict": "merge",
        "export_once": True
    },
    {
        "source": "test_export_once_extension.behavior.json",
        "target": "BP/entities/test_export_once.behavior.json",
        "on_conflict": "merge",
        "export_once": True
    },
    {
        "source": "test_export_once_extension.behavior.json",
        "target": "BP/entities/test_export_once.behavior.json",
        "on_conflict": "merge",
        "export_once": True
    },
    {
        "source": "test_export_once_extension.behavior.json",
        "target": "BP/entities/test_export_once.behavior.json",
        "on_conflict": "merge",
        "export_once": True
    }
]