[
    {
        "source": "my_source.mcfunction",
        "target": AUTO,
        "scope": {
            "secret_data": "This is a very secret data"
        }
    },
    {
        "source": "SHARED:my_shared_source.mcfunction",
        "target": AUTO,
        "scope": {
            "secret_data": "This goes into the shared file"
        }
    },
    {
        "source": "SHARED:my_shared_source_but_not_in_shared_folder.mcfunction",
        "target": AUTO,
        "scope": {
            "secret_data": "Some secret data"
        }
    },
    {
        "source": "en_US.lang",
        "target": AUTO,
        "subfunctions": true
    }
]