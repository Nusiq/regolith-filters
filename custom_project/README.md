# WARNING
This filter is experimental. I'm not sure if I'll keep it.

# Source code
https://github.com/Nusiq/custom-project-filter-src

# Description
This filter lets you organize your project in a custom way by using a file
extensions defined in the configuration `export_map.json` file. The file
extensions are used to detect the type of the Minecraft project file, the
export map is used to decide where to export the flie. The default export map
comes with some useful defaults which cover most of the cases that you'll find
in Minecraft project but it's fully customizable to your needs.

The data folder of the filter must be orgainized in the following way:
```
<data-path>/custom_project/project/*
<data-path>/custom_project/export_map.json
```
The project folder contains the files of the project and the export_map defines
how to move them. Files are exported to RP and BP folders based on their
relative paths inside the project folder, their extensions and the export map.

The process of exporting is the easiest to understand if you look at the
example below.

# Example
_\<data-path\>/custom_project/export_map.json_
```json
{
    // This is a simplified version of the default export map
    "lang": "RP/texts",
    "mcfunction": "BP/functions",
    "png" : "RP/textures",
    "bpe.json": "BP/entities",
    "rpe.json": "RP/entity"
}
```

**Examples of the file paths inside the project folder and where they are
exported (all paths on the left are relative to 
_\<data-path\>/custom_project/project/_):**


Simple file names (the name of the source file is the same as the name of the
destination file):
- en_US.lang -> RP/texts/en_US.lang
- abc.mcfunction -> BP/functions/abc.mcfunction
- a/b/c/hello.png -> RP/textures/a/b/c/hello.png
- enemy/zombie.bpe.json -> BP/entities/enemy/zombie.bpe.json
- entity/zombie.rpe.json -> RP/entity/zombie.rpe.json

File names based on their parent folder (useful for grouping files in single
folders of the project):
- enemy/zombie/bpe.json -> BP/entities/enemy/zombie.bpe.json
- entity/zombie/rpe.json -> RP/entity/zombie.rpe.json




# How to install the filter
_This instruction assumes you're using regolith 0.0.8 or above. As of the time
of writing, 0.0.8 is yet to be released._

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
