# Pack Anything
Unopinionated filter that lets you pack anything into a ZIP file in any way you want.

# 💿 Installation
Run the following command in the Regolith project to make this filter
available:
```
regolith install github.com/Nusiq/regolith-filters/pack_anything
```
When you have done that, you can use the filter in your Regolith project by adding it to the `filters` section of a profile in the `config.json` file of the Project. Make sure to add configuration that specifies the `output` and the `pathmap` that defines where to look for the files, and where to export them.

For example configuration below could be used to create Mctemplate file:
```json
{
    "filter": "pack_anything",
    "settings": {
        "output": "release.mctemplate",
        "pathmap": {
            "BP": "behavior_packs/0",
            "RP": "resource_packs/0",

            // This configuration assumes that you keep the world files in your
            // project in "worlds/release-world" directory.
            "PROJECT:worlds/release-world": "."
        }
    }
}
```
# 🔧 Configuration settings
- `output` - The name of the output file. Can have any extension you want, which allows making mcaddon, mctemplate etc. (all of these Minecraft file formats are renamed ZIP files). The output path is relative to the root of the Regolith project.
- `pathmap` - A dictionary that maps the paths in the project to the paths in the output ZIP file. By default, the paths start in Regolith working directory, which means you have access to `RP`, `BP` and `data` folders. If you put a `PROJECT:` prefix in the path, it will start in the Regolith project directory.
