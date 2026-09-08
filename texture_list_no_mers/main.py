'''
Generates textures_list.json files for the resource pack and its subpacks.

The lists contain all the textures (*.png and *.tga files) from the 'textures'
folders, except for the textures with the '_mer' and '_mers' suffix.

Minecraft Creator Tools (mctools.dev) reports errors like TEXTURELIST102 when
texture set images are referenced in texture_list.json. The '_mer' and '_mers'
textures are typically used by texture sets, so this filter skips them.
'''
import json
from itertools import chain
from pathlib import Path

ROOT_PATH = Path("RP")
SUBPACK_PATH = ROOT_PATH / "subpacks"


def fetch_subpack_folders():
    """
    Fetches a list of all subpack folders in the resource-pack.
    """
    if SUBPACK_PATH.exists():
        for subpack_folder in SUBPACK_PATH.iterdir():
            if subpack_folder.is_dir() and (subpack_folder / "textures").exists():
                yield subpack_folder


def list_textures(root_folder: Path):
    """
    Lists all textures within the 'textures' folder within the path. For example
    pass in 'RP", and it will search 'RP/textures'.
    """
    textures = []
    textures_folder = root_folder / "textures"

    for texture in chain(
        textures_folder.glob("**/*.png"), textures_folder.glob("**/*.tga")
    ):
        # Minecraft Creator Tools Complain about that with errors like
        # TEXTURELIST102 Texture set image must not be referenced in
        # texture_list.json. ...
        # This is a workaround, a proper solution would check textures_set files.
        if texture.stem.endswith("_mers") or texture.stem.endswith("_mer"):
            continue
        textures.append(texture.relative_to(root_folder).with_suffix("").as_posix())
    return textures


def generate_texture_list_file(root_folder: Path, textures):
    """
    Generates root_folder/textures/textures_list.json
    """
    if len(textures) > 0:
        with open(
            root_folder / "textures" / "textures_list.json",
            "w",
            encoding="utf8",
            newline="\n",
        ) as f:
            json.dump(textures, f, indent="\t")


def main():
    # Handle the root resource pack file
    pack_textures = sorted(list_textures(ROOT_PATH))
    generate_texture_list_file(ROOT_PATH, pack_textures)

    for subpack_folder in fetch_subpack_folders():
        # The texture list of a subpack must also contain the textures of the
        # main resource pack. The list is sorted to keep the output of the
        # filter deterministic.
        subpack_textures = sorted(
            set(list_textures(subpack_folder) + pack_textures)
        )
        generate_texture_list_file(subpack_folder, subpack_textures)


if __name__ == "__main__":
    main()
