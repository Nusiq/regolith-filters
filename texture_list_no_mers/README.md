# Texture List No MERs
Generates `textures_list.json` files for the resource pack and its subpacks.

The generated lists contain all the textures (`*.png` and `*.tga` files) from
the `textures` folders, **except** for the textures with the `_mer` and
`_mers` suffix. Minecraft Creator Tools ([mctools.dev](https://mctools.dev))
reports errors like `TEXTURELIST102 Texture set image must not be referenced
in texture_list.json` when texture set images are referenced in the file, and
the `_mer`/`_mers` textures are typically used by texture sets. Skipping them
keeps the texture lists clean.

The filter generates:
- `RP/textures/textures_list.json` - for the main resource pack.
- `RP/subpacks/<subpack_name>/textures/textures_list.json` - for every
  subpack that has a `textures` folder. Subpack lists also include the
  textures of the main resource pack (deduplicated).

The lists are sorted alphabetically, so the output of the filter is
deterministic and diffs stay clean between runs.

# 💿 Installation
Run the following command in the Regolith project to make this filter
available:
```
regolith install github.com/Nusiq/regolith-filters/texture_list_no_mers
```

Add the filter to the `filters` list in the `config.json` file of the Regolith
project to actually enable it:
```json
                    {
                        "filter": "texture_list_no_mers"
                    },
```

The filter doesn't take any settings.
