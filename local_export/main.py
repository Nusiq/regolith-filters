'''
Exports specified files from the working directory of the filters (the folder
with the BP, RP and data folders) to the root directory of the Regolith
project.

This is useful for pulling out files that were generated during the Regolith
run by other filters, for example documentation generated into the data
folder, so that they're available in the project directory after the run
finishes.

The settings of the filter should contain a "map" property with a list of
objects that have "source" and "target" keys. The "source" is the path to the
exported file, relative to the working directory of the filters. The "target"
is the path to the destination file, relative to the root directory of the
Regolith project.
'''
from typing import Any, cast
from pathlib import Path
import os
import json
import sys
import shutil

ROOT_DIR = os.environ.get("ROOT_DIR")


def export(source: str, target: str) -> None:
    source_path = Path(source).resolve()
    target_path = Path(ROOT_DIR) / target
    if target_path.is_dir():
        raise Exception(
            f"Target path {target_path} is a directory, can't "
            "export the file there.")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    print(
        f"Exporting file:\n"
        f"- source: {source_path}\n"
        f"- target: {target_path}\n"
    )
    shutil.copy2(source_path, target_path)


def main():
    if ROOT_DIR is None:
        raise Exception(
            "The ROOT_DIR environment variable is not set. The filter can "
            "only run from Regolith.")
    args = sys.argv
    invalid_args_message = (
        "Unable to parse arguments. The filter should have an array of "
        "objects containing 'source' and 'target' keys. With paths mapping "
        "the exporting."
    )
    try:
        args = json.loads(args[1])["map"]
    except Exception:
        raise Exception(invalid_args_message)
    if not isinstance(args, list):
        raise Exception(invalid_args_message)
    args = cast(list[Any], args)
    for arg in args:
        match arg:
            case {"source": str(source), "target": str(target)}:
                export(source, target)
            case _:
                raise Exception(invalid_args_message)


if __name__ == "__main__":
    main()
