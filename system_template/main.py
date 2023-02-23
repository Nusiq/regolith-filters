from typing import Dict, List
import json
import merge
import sys
from pathlib import Path
import shutil
import math
import uuid
from copy import copy
from enum import Enum, auto
from better_json_tools import load_jsonc
from better_json_tools.compact_encoder import CompactEncoder

class SpecialKeys(Enum):
    AUTO = auto()  # Special key used for the "target" property in "_map.py"

DATA_PATH = Path('data')
BP_PATH = Path('BP')
RP_PATH = Path('RP')

class SystemTemplateException(Exception):
    def __init__(self, errors: List[str]=None):
        self.errors = [] if errors is None else errors
    
    def __str__(self):
        return "\n".join(self.errors)

def print_red(text):
    for t in text.split('\n'):
        print("\033[91m {}\033[00m".format(t))


def get_auto_target_mapping(source: Path, auto_map: Dict[str, str]) -> Path:
    for key, value in auto_map.items():
        if source.name.endswith(key):
            return Path(value) / source
    raise Exception(
        "Failed to find an AUTO mapping export target for "
        f"{source.as_posix()}")

def compile_system(scope: Dict, system_path: Path, auto_map: Dict[str, str]):
    scope = scope | load_jsonc(system_path / '_scope.json').data
    file_map_path = system_path / '_map.py'
    try:
        with file_map_path.open('r') as f:
            # copy to avoid outputing values from evalation
            file_map = eval(f.read(), copy(scope))
    except Exception as e:
        raise SystemTemplateException([
            f"Failed to evaluate {file_map_path.as_posix()} "
            "due to an error:",  str(e)])
    for file_map_item in file_map:
        if 'source' not in file_map_item:
            raise SystemTemplateException([
                    "Missing 'source' property in one of the "
                    f"_map.py items: {file_map_item}"])
        source: Path = system_path / file_map_item['source']
        if 'target' not in file_map_item:
            raise SystemTemplateException([
                f"Missing 'target'  property in one of the "
                f"_map.py items: : {file_map_item}"])
        target = file_map_item['target']
        if target is SpecialKeys.AUTO:
            target = get_auto_target_mapping(
                Path(file_map_item['source']), auto_map)
        elif isinstance(target, str) and (target.startswith('BP/') or target.startswith('RP/')):
            target = Path(target)
        else:
            raise SystemTemplateException([
                f'Export target must be "AUTO" or a path that starts with "BP/" or "RP/": {target}'])
        # Get on_conflict policy: stop, overwrite, append_end, append_start,
        # skip or merge
        if target.suffix in ('.material', '.json'):
            on_conflict = file_map_item.get('on_conflict', 'stop')
            valid_keys = ['stop', 'overwrite', 'merge', 'skip']
            if on_conflict not in valid_keys:
                raise SystemTemplateException([
                    f"Invalid 'on_conflict' value: {on_conflict} for "
                    f"{target.as_posix()}. Valid values for JSON files "
                    f"are: {valid_keys}"])
        elif target.suffix == '.lang':
            on_conflict = file_map_item.get('on_conflict', 'append_end')
            valid_keys = [
                'stop', 'overwrite', 'append_end', 'append_start', 'skip']
            if on_conflict not in valid_keys:
                raise SystemTemplateException([
                    f"Invalid 'on_conflict' value: {on_conflict} for "
                    f"{target.as_posix()}. Valid values for .lang files "
                    f"are: {valid_keys}"])
        elif target.suffix == '.mcfunction':
            on_conflict = file_map_item.get('on_conflict', 'stop')
            valid_keys = [
                'stop', 'overwrite', 'append_end', 'append_start', 'skip']
            if on_conflict not in valid_keys:
                raise SystemTemplateException([
                    f"Invalid 'on_conflict' value: {on_conflict} for "
                    f"{target.as_posix()}. Valid values for .lang files "
                    f"are: {valid_keys}"])
        else:
            on_conflict = file_map_item.get('on_conflict', 'stop')
            valid_keys = ['stop', 'overwrite', 'skip']
            if on_conflict not in valid_keys:
                raise SystemTemplateException([
                    f"Invalid 'on_conflict' value: {on_conflict} for "
                    f"{target.as_posix()}. Valid values for this kind of file "
                    f"are: {valid_keys}"])
        # Handling the conflicts with skip, stop and overwrite policy here
        # other policies just read the data from are handled later
        target_data = None
        if target.exists():
            # Special case when the target already exist and is a folder
            if not target.is_file():
                raise SystemTemplateException([
                    f"Failed to create the target file because there a folder "
                    f"at the same path already exists: {target.as_posix()}"])
            # Handling the conficts based on the on_conflict policy
            if on_conflict == 'stop':
                raise SystemTemplateException([
                    f"Target already exists: {target.as_posix()}"])
            elif on_conflict == 'overwrite':
                print(f"Overwriting {target.as_posix()}")
                target.unlink()
            elif on_conflict == 'skip':
                print(f"Skipping {target.as_posix()}")
                continue
            elif on_conflict in ('merge', 'append_end', 'append_start'):
                try:
                    if target.suffix in ('.material', '.json'):
                        target_data = load_jsonc(target).data
                    else:
                        with target.open('r', encoding='utf8') as f:
                            target_data = f.read()
                except Exception as e:
                    raise SystemTemplateException([
                        "Failed to load the target file for merging "
                        f"due to an error: {str(e)}"])
                target.unlink()
        # Python templating for JSON files
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            # Merging is possible only if target is JSON and source is either
            # python or JSON
            if (
                    target.suffix in ('.material', '.json') and
                    source.suffix in ('.material', '.json', '.py')):
                if source.suffix == '.py':
                    file_scope = copy(scope) | file_map_item.get('scope', {})
                    with source.open('r') as f:
                        file_json = eval(f.read(), file_scope)
                elif source.suffix in ('.material', '.json'):
                    file_json = load_jsonc(source).data
                if on_conflict == 'merge':
                    file_json = merge.deep_merge_objects(
                        target_data, file_json,
                        list_merge_policy=merge.ListMergePolicy.APPEND)
                with target.open('w') as f:
                    json.dump(file_json, f, cls=CompactEncoder)
            else:  # Other files (append_start, append_end or overwrite)
                if on_conflict == 'append_start':
                    with source.open('r', encoding='utf8') as f:
                        source_data = f.read()
                    with target.open('w', encoding='utf8') as f:
                        f.write("\n".join([source_data, target_data]))
                elif on_conflict == 'append_end':
                    with source.open('r', encoding='utf8') as f:
                        source_data = f.read()
                    with target.open('w', encoding='utf8') as f:
                        f.write("\n".join([target_data, source_data]))
                else:
                    shutil.copy(source.as_posix(), target.as_posix())
        except Exception as e:
            raise SystemTemplateException([
                f'Failed to evaluate {source.as_posix()} for '
                f'{target.as_posix()}":',
                str(e)])

def main(scope: Dict, templates_path: Path, auto_map: Dict[str, str]):
    for system_path in (DATA_PATH / templates_path).glob("**/*"):
        if system_path.is_file():
            continue
        system_scope_path = system_path / '_scope.json'
        file_map_path = system_path / '_map.py'
        if not system_scope_path.exists() or system_scope_path.is_dir():
            continue
        if not file_map_path.exists() or file_map_path.is_dir():
            continue
        print(
            "Generating system: "
            f"{system_path.relative_to(DATA_PATH / templates_path).as_posix()}"
        )
        compile_system(scope, system_path, auto_map)

if __name__ == '__main__':
    try:
        config = json.loads(sys.argv[1])
    except Exception:
        config = {}
    # File path to the templates folder
    templates_path = Path('system_template')

    # Add scope
    scope = {
        'true': True, 'false': False, 'math': math, 'uuid': uuid,
        "AUTO": SpecialKeys.AUTO}
    scope_path = DATA_PATH / config.get(
        'scope_path', 'system_template/scope.json')
    scope = scope | load_jsonc(scope_path).data
    # Try to load the auto map
    try:
        auto_map_path = DATA_PATH / "system_template/auto_map.json"
        auto_map = load_jsonc(auto_map_path).data
    except FileNotFoundError:
        auto_map = {}
    try:
        main(scope, templates_path, auto_map)
    except SystemTemplateException as e:
        for err in e.errors:
            print_red(err)
        sys.exit(1)
