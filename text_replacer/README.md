# Text Replacer
A filter that replaces all occurrences of a string with another string in
every text file of the behavior and the resource packs.

Files that aren't valid UTF-8 (e.g. textures, sounds) are skipped, so the
filter never corrupts binary files.

# 💿 Installation
Run the following command in the Regolith project to make this filter
available:
```
regolith install github.com/Nusiq/regolith-filters/text_replacer
```

Add the filter to the `filters` list in the `config.json` file of the Regolith
project to actually enable it (the settings properties are explained in the
next section):
```json
                    {
                        "filter": "text_replacer",
                        "settings": {
                            "replace_from": "@namespace",
                            "replace_to": "my_namespace"
                        }
                    },
```

# 🔧 Configuration settings
## replace_from (required)
The string to search for in the files of the packs.

## replace_to (required)
The string that replaces every occurrence of `replace_from`.

## paths (optional)
A list of folders to scan, relative to the working directory of the filters.
Defaults to `["RP", "BP"]`. You rarely need to change this, but it can be
useful for scanning other folders, for example:
```json
                    {
                        "filter": "text_replacer",
                        "settings": {
                            "replace_from": "@namespace",
                            "replace_to": "my_namespace",
                            "paths": ["RP", "BP", "data"]
                        }
                    },
```
