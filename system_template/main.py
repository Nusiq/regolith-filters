from __future__ import annotations

from typing import Dict, List, Iterable, Literal, Optional
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
from regolith_subfunctions import CodeTree

class SpecialKeys(Enum):
    AUTO = auto()  # Special key used for the "target" property in "_map.py"

DATA_PATH = Path('data')
SYSTEM_TEMPLATE_DATA_PATH = DATA_PATH / 'system_template'
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

def print_yellow(text):
    for t in text.split('\n'):
        print("\033[93m {}\033[00m".format(t))

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
    for system_item_data in file_map:
        for system_item in get_system_items(
                system_item_data, system_path, scope, auto_map):
            system_item.eval()


def get_system_items(
        data: Dict, system_path: Path, scope: Dict,
        auto_map: Dict) -> Iterable[SystemItem]:
    '''
    Based on the data from one item in the _map.py file, returns an iterable
    with the SystemItem objects that correspond to the matched glob patterns in
    the source property.
    '''
    if 'source' not in data:
        raise SystemTemplateException([
            "Missing 'source' property in one of the "
            f"_map.py items: {data}"])

    # Treat as a glob pattern only if it contains a "*" or "?" characters
    source_pattern: str = data['source']
    if not isinstance(source_pattern, str):
        raise SystemTemplateException([
            f"Invalid source value: {source_pattern} in {data}"])
    shared: bool = False
    if source_pattern.startswith("SHARED:"):
        shared = True
        source_pattern = source_pattern[7:]
    

    if "*" in source_pattern or '?' in source_pattern:
        has_items = False
        for source_path in system_path.glob(source_pattern):
            has_items = True
            # Skip directories
            if not source_path.is_file():
                continue
            # Skip _map.py and _scope.json
            relative_source_path = source_path.relative_to(system_path)
            if relative_source_path.as_posix() in ["_map.py", "_scope.json"]:
                continue
            yield SystemItem(
                relative_source_path, shared, data, system_path, scope,
                auto_map)
        if not has_items:
            print_yellow(
                f"Warning: No files found for the source pattern: "
                f"{source_pattern} in {system_path.as_posix()}"
            )
    else:
        yield SystemItem(
            Path(source_pattern), shared, data, system_path, scope, auto_map)

class SystemItem:
    '''
    An object based of one item in the _map.py file, after evaluation of the
    glob pattern to the source file.
    '''
    def __init__(
            self, source: Path, shared: bool, data: Dict, system_path: Path,
            external_scope: Dict, auto_map: Dict):
        data = copy(data)  # copy to avoid outputing values from evalation
        self.relative_source_path = source
        self.shared = shared
        self.system_path = system_path
        self.auto_map = auto_map
        self.target = self._init_target(data)
        self.on_conflict = self._init_on_conflict(data)
        self.scope = external_scope | data.get('scope', {})
        self.subfunctions = data.get(
            # default for .mcfunction is True but for .lang is False
            'subfunctions', self.target.suffix == '.mcfunction')

    def _init_target(self, data: Dict) -> Path:
        '''
        In the __init__ function, creates teh target path either by reading it
        from the data or by evaluating the AUTO mapping.
        '''
        if 'target' not in data:
            raise SystemTemplateException([
                f"Missing 'target'  property in one of the "
                f"_map.py items: : {data}"])
        target = data['target']
        if target is SpecialKeys.AUTO:
            target = get_auto_target_mapping(
                self.relative_source_path, self.auto_map)
        elif isinstance(target, str) and (target.startswith('BP/') or target.startswith('RP/')):
            target = Path(target)
        else:
            raise SystemTemplateException([
                f'Export target must be "AUTO" or a path that starts with "BP/" or "RP/": {target}'])
        return target

    def _init_on_conflict(
            self, data: Dict,
    ) -> Literal[
        'stop', 'overwrite', 'merge', 'skip', 'append_start', 'append_end',
        'skip'
    ]:
        '''
        In the __init__ function, creates the on_conflict policy either by
        reading it from the data or by inserting the default value.
        Additionally checks if the policy is valid for the target file type.
        '''
        # Get on_conflict policy: stop, overwrite, append_end, append_start,
        # skip or merge
        if self.target.suffix in ('.material', '.json'):
            on_conflict = data.get('on_conflict', 'stop')
            valid_keys = ['stop', 'overwrite', 'merge', 'skip']
            if on_conflict not in valid_keys:
                raise SystemTemplateException([
                    f"Invalid 'on_conflict' value: {on_conflict} for "
                    f"{self.target.as_posix()}. Valid values for JSON files "
                    f"are: {valid_keys}"])
        elif self.target.suffix == '.lang':
            on_conflict = data.get('on_conflict', 'append_end')
            valid_keys = [
                'stop', 'overwrite', 'append_end', 'append_start', 'skip']
            if on_conflict not in valid_keys:
                raise SystemTemplateException([
                    f"Invalid 'on_conflict' value: {on_conflict} for "
                    f"{self.target.as_posix()}. Valid values for .lang files "
                    f"are: {valid_keys}"])
        elif self.target.suffix == '.mcfunction':
            on_conflict = data.get('on_conflict', 'stop')
            valid_keys = [
                'stop', 'overwrite', 'append_end', 'append_start', 'skip']
            if on_conflict not in valid_keys:
                raise SystemTemplateException([
                    f"Invalid 'on_conflict' value: {on_conflict} for "
                    f"{self.target.as_posix()}. Valid values for .lang files "
                    f"are: {valid_keys}"])
        else:
            on_conflict = data.get('on_conflict', 'stop')
            valid_keys = ['stop', 'overwrite', 'skip']
            if on_conflict not in valid_keys:
                raise SystemTemplateException([
                    f"Invalid 'on_conflict' value: {on_conflict} for "
                    f"{self.target.as_posix()}. Valid values for this kind of file "
                    f"are: {valid_keys}"])
        return on_conflict

    def eval(self) -> None:
        '''
        Evaluates the SystemItem by writing to the target file.
        '''
        # DETERMINE THE SOURCE PATH
        source_path: Path = self.system_path / self.relative_source_path
        if self.shared and not source_path.exists():
            source_path = (
                SYSTEM_TEMPLATE_DATA_PATH / "_shared" /
                self.relative_source_path)

        # READ TARGET DATA AND HANDLE CONFLICTS
        target_data = None
        if self.target.exists():
            # Special case when the target already exist and is a folder
            if not self.target.is_file():
                raise SystemTemplateException([
                    f"Failed to create the target file because there a folder "
                    f"at the same path already exists: {self.target.as_posix()}"])
            # Handling the conficts based on the on_conflict policy
            if self.on_conflict == 'stop':
                raise SystemTemplateException([
                    f"Target already exists: {self.target.as_posix()}"])
            elif self.on_conflict == 'overwrite':
                print(f"Overwriting {self.target.as_posix()}")
                self.target.unlink()
            elif self.on_conflict == 'skip':
                print(f"Skipping {self.target.as_posix()}")
                return
            elif self.on_conflict in ('merge', 'append_end', 'append_start'):
                try:
                    if self.target.suffix in ('.material', '.json'):
                        target_data = load_jsonc(self.target).data
                    else:
                        with self.target.open('r', encoding='utf8') as f:
                            target_data = f.read()
                except Exception as e:
                    raise SystemTemplateException([
                        "Failed to load the target file for merging:\n"
                        f"- Source file: {source_path.as_posix()}\n"
                        f"- Error: {str(e)}"])
                self.target.unlink()

        # INSERT SOURCE/GENERATED DATA INTO TARGET
        try:
            self.target.parent.mkdir(parents=True, exist_ok=True)
            # Merging is possible only if target is JSON and source is either
            # python or JSON
            if (
                    self.target.suffix in ('.material', '.json') and
                    source_path.suffix in ('.material', '.json', '.py')):
                if source_path.suffix == '.py':
                    with source_path.open('r') as f:
                        file_json = eval(f.read(), self.scope)
                elif source_path.suffix in ('.material', '.json'):
                    file_json = load_jsonc(source_path).data
                if self.on_conflict == 'merge':
                    file_json = merge.deep_merge_objects(
                        target_data, file_json,
                        list_merge_policy=merge.ListMergePolicy.APPEND)
                with self.target.open('w') as f:
                    json.dump(file_json, f, cls=CompactEncoder)
            else:  # Other files (append_start, append_end or overwrite)
                if self.on_conflict == 'append_start':
                    target_data = "" if target_data is None else target_data
                    with source_path.open('r', encoding='utf8') as f:
                        source_data = f.read()
                    with self.target.open('w', encoding='utf8') as f:
                        f.write("\n".join([source_data, target_data]))
                elif self.on_conflict == 'append_end':
                    target_data = "" if target_data is None else target_data
                    with source_path.open('r', encoding='utf8') as f:
                        source_data = f.read()
                    with self.target.open('w', encoding='utf8') as f:
                        f.write("\n".join([target_data, source_data]))
                else:
                    shutil.copy(source_path.as_posix(), self.target.as_posix())
                if self.target.suffix == '.mcfunction' or self.target.suffix == '.lang':
                    if self.subfunctions:
                        code = CodeTree(self.target)
                        code.root.eval_and_dump(
                            self.scope, self.target, self.target)
        except Exception as e:
            raise SystemTemplateException([
                f'Failed to evaluate {source_path.as_posix()} for '
                f'{self.target.as_posix()}":',
                str(e)])


def main():
    try:
        config = json.loads(sys.argv[1])
    except Exception:
        config = {}
    # Add scope
    scope = {
        'true': True, 'false': False, 'math': math, 'uuid': uuid,
        "AUTO": SpecialKeys.AUTO}
    scope_path = DATA_PATH / config.get(
        'scope_path', 'system_template/scope.json')
    scope = scope | load_jsonc(scope_path).data
    # Try to load the auto map
    try:
        auto_map_path = SYSTEM_TEMPLATE_DATA_PATH / "auto_map.json"
        auto_map = load_jsonc(auto_map_path).data
    except FileNotFoundError:
        auto_map = {}
    try:
        for system_path in (SYSTEM_TEMPLATE_DATA_PATH).glob("**/*"):
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
                f"{system_path.relative_to(SYSTEM_TEMPLATE_DATA_PATH).as_posix()}"
            )
            compile_system(scope, system_path, auto_map)
    except SystemTemplateException as e:
        for err in e.errors:
            print_red(err)
        sys.exit(1)

if __name__ == '__main__':
    main()