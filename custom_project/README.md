# WARNING
This filter is experimental. I'm not sure if I'll keep it.

# Source code
https://github.com/Nusiq/custom-project-filter-src

# Description
This filter lets you organize your project in a custom way by using a file
extensions and paths defined in the configuration file `config.json`. The file
extensions are used to detect the type of the Minecraft project file, the types
of the files combined with their relative path to the root of the data folders
(also defined in config) are used to determine where should they be exported.

The default map of file extensions comes with useful defaults which cover most
of the cases that you'll find in Minecraft project but it's fully customizable
to your needs. The default settings are compatible with
[bedrock-addon-icons](https://github.com/SirLich/bedrock-addon-icons)
VS Code plugin.

The process of exporting is the easiest to understand if you look at the
example below.

# Example
_\<data-path\>/custom_project/export_map.json_
```json
{
    // This is a simplified version of the default export map
    "roots": [
        "project"
    ],
    "extensions_map": {
        ".lang": "RP/texts",
        ".mcfunction": "BP/functions",
        ".png" : "RP/textures",
        ".bpe.json": "BP/entities",
        ".rpe.json": "RP/entity"
    }
}
```

**The paths of source file relative to `<data-path>/custom_project/project/`)
and where they should be exported based on the example config file above.**:


Simple file names (the name of the source file is the same as the name of the
destination file):
- en_US.lang -> RP/texts/en_US.lang
- abc.mcfunction -> BP/functions/abc.mcfunction
- a/b/c/hello.png -> RP/textures/a/b/c/hello.png
- enemy/zombie.bpe.json -> BP/entities/enemy/zombie.bpe.json
- entity/zombie.rpe.json -> RP/entity/zombie.rpe.json

File names based on their parent folder (useful for grouping files in single
folders of the project):
- enemy/zombie/.bpe.json -> BP/entities/enemy/zombie.bpe.json
- enemy/zombie/.rpe.json -> RP/entity/enemy/zombie.rpe.json

Files with underscore instead of the name (file names based on their parent
folder):
- enemy/zombie/_.png -> RP/textures/enemy/zombie.png
- enemy/zombie/_.bpe.json -> BP/entities/enemy/zombie.bpe.json
- entity/zombie/_.rpe.json -> RP/entity/zombie.rpe.json

Note the you can have multiple root folders. In this case it's _project_
which translates to `<data-path>/custom_project/project/`, you could have for
example _foo_ which would translate to `<data-path>/custom_project/foo/`.

# Installation
Simply run the command:
```
regolith install github.com/Nusiq/regolith-filters/custom_project
```

Regolith will add the latest version of the filter to `filterDefinitions` of
your `config.json` file. Then, you can edit the `filters` list to actually
use the filter.

# Acknowledgements
Thanks to [SirLich](https://github.com/SirLich) for creating the
[bedrock-addon-icons](https://github.com/SirLich/bedrock-addon-icons) VS
Code plugin, which was the inspiration for this filter and the basis for
the default set of file extensions used in export_map.json
