# Local Export
Exports files from the Regolith's working directory to the project directory.

# 💿 Installation
Run the following command in the Regolith project to make this filter
available:
```
regolith install github.com/Nusiq/regolith-filters/local_export
```

Add the filter to the `filters` list in the `config.json` file of the Regolith
project to actually enable it (the settings properties are explained in the
next section):
```json
                    {
                        "filter": "local_export",
                        "settings": {
                            "map": [
                                {
                                    "source": "data/content_guide.md",
                                    "target": "content_guide.md"
                                }
                            ]
                        }
                    },
```

# 🔧 Configuration settings
## map
A list of objects that define the exporting. Every object must contain two
string properties:

- `source` - the path to the exported file, relative to the working directory
  of the filters. This is the folder that contains the `BP`, `RP` and `data`
  folders during the Regolith run.
- `target` - the path to the destination file, relative to the root directory
  of the Regolith project. Missing parent folders of the target are created
  automatically.

# ⚠️ Notes
- The filter copies single files. It raises an error if the target path is an
  existing directory, or if the source file doesn't exist.
