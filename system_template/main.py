from __future__ import annotations

from typing import Dict, List, Iterable, Literal, Tuple, Any, Optional
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
from regolith_json_template import eval_json, JsonTemplateK
import argparse
from typing import TypedDict, Literal
import io
import os

class WdSwitch:
    '''
    A context manager that switches the working directory to the specified path
    '''
    def __init__(self, path: Path):
        self.path = path
        self.old_path = Path.cwd()

    def __enter__(self):
        os.chdir(self.path)

    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self.old_path)

class SpecialKeys(Enum):
    AUTO = auto()  # Special key used for the "target" property in "_map.py"

DATA_PATH = Path('data')
SYSTEM_TEMPLATE_DATA_PATH = DATA_PATH / 'system_template'
BP_PATH = Path('BP')
RP_PATH = Path('RP')


class Source(TypedDict):
    path: str
    status: Literal['merged', 'skipped', 'overwritten', 'created']

class FileReport(TypedDict):
    target: str
    sources: list[Source]

class Report:
    def __init__(self):
        self.file_reports: dict[str, FileReport] = {}
    
    def _init_report(self, target: Path):
        '''
        Initializes a report for a file if it doesn't exist.
        '''
        if target not in self.file_reports:
            self.file_reports[target] = FileReport(
                target=target.as_posix(),
                sources=[],
            )

    def append_source(
            self, target: Path,
            source: Path,
            status: Literal['merged', 'skipped', 'overwritten', 'created']):
        self._init_report(target)
        self.file_reports[target]['sources'].append(
            Source(path=source.as_posix(), status=status))

    def dump_report(self, path: Path):
        '''Dump the report to the specified path'''
        nice_report: list[FileReport] = [r for r in self.file_reports.values()]
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='utf8') as f:
            json.dump(nice_report, f, indent=4, cls=CompactEncoder)

    def dump_report_to_file(self, file: io.TextIOWrapper):
        '''Dump the report to the file'''
        nice_report: list[FileReport] = [r for r in self.file_reports.values()]
        json.dump(nice_report, file, indent=4, cls=CompactEncoder)


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

def walk_system_paths(systems: List[str]) -> Iterable[Path]:
    for system_path in DATA_PATH.rglob("*"):
        if system_path.is_file():
            continue
        system_scope_path = system_path / '_scope.json'
        file_map_path = system_path / '_map.py'
        if not system_scope_path.exists() or system_scope_path.is_dir():
            continue
        if not file_map_path.exists() or file_map_path.is_dir():
            continue
        # Chek if the system matches the glob pattern
        relative_path = system_path.relative_to(DATA_PATH)
        for system_glob in systems:
            if relative_path.match(system_glob):
                yield system_path
                break

class System:
    def __init__(self, scope: Dict, system_path: Path, auto_map: Dict[str, str]):
        self.scope: Dict[str, Any] = scope | load_jsonc(system_path / '_scope.json').data
        self.system_path: Path = system_path
        self.file_map: List[Dict] = self._init_file_map(
            system_path / '_map.py')
        self.auto_map: Dict[str, str] = auto_map

    def _init_file_map(self, file_map_path: Path) -> List[Dict]:
        try:
            file_map_text = file_map_path.read_text(encoding='utf8')
            with WdSwitch(self.system_path):
                return eval(file_map_text, copy(self.scope))
        except Exception as e:
            raise SystemTemplateException([
                f"Failed to evaluate {file_map_path.as_posix()} "
                "due to an error:",  str(e)])

    def walk_system_items(self) -> Iterable[SystemItem]:
        '''
        Based on the data from one item in the _map.py file, returns an iterable
        with the SystemItem objects that correspond to the matched glob patterns in
        the source property.
        '''
        for data in self.file_map:
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
                for source_path in self.system_path.glob(source_pattern):
                    has_items = True
                    # Skip directories
                    if not source_path.is_file():
                        continue
                    # Skip _map.py and _scope.json
                    relative_source_path = source_path.relative_to(self.system_path)
                    if relative_source_path.as_posix() in ["_map.py", "_scope.json"]:
                        continue
                    yield SystemItem(relative_source_path, shared, data, self)
                if not has_items:
                    print_yellow(
                        f"Warning: No files found for the source pattern: "
                        f"{source_pattern} in {self.system_path.as_posix()}"
                    )
            else:
                yield SystemItem(Path(source_pattern), shared, data, self)

class SystemItem:
    '''
    An object based of one item in the _map.py file, after evaluation of the
    glob pattern to the source file.
    '''
    def __init__(self, source: Path, shared: bool, data: Dict, parent: System):
            # , system_path: Path,
            # external_scope: Dict, auto_map: Dict):
        data = copy(data)  # copy to avoid outputing values from evalation
        self.relative_source_path = source
        self.shared = shared
        self.parent = parent
        self.target = self._init_target(data)
        self.on_conflict = self._init_on_conflict(data)
        self.json_template = data.get('json_template', False)
        self.scope = self.parent.scope | data.get('scope', {})

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
                self.relative_source_path, self.parent.auto_map)
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

    def eval(self, report: Report) -> None:
        '''
        Evaluates the SystemItem by writing to the target file.
        '''
        # DETERMINE THE SOURCE PATH
        source_path: Path = self.parent.system_path / self.relative_source_path
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
                report.append_source(self.target, source_path, 'overwritten')
                self.target.unlink()
            elif self.on_conflict == 'skip':
                print(f"Skipping {self.target.as_posix()}")
                report.append_source(self.target, source_path, 'skipped')
                return
            elif self.on_conflict in ('merge', 'append_end', 'append_start'):
                try:
                    report.append_source(self.target, source_path, 'merged')
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
        else:
            report.append_source(self.target, source_path, 'created')
        # INSERT SOURCE/GENERATED DATA INTO TARGET
        try:
            self.target.parent.mkdir(parents=True, exist_ok=True)
            # Merging is possible only if target is JSON and source is either
            # python or JSON
            if (
                    self.target.suffix in ('.material', '.json') and
                    source_path.suffix in ('.material', '.json', '.py')):
                if source_path.suffix == '.py':
                    source_text = source_path.read_text(encoding='utf8')
                    with WdSwitch(self.parent.system_path):
                        file_json = eval(source_text, self.scope)
                elif source_path.suffix in ('.material', '.json'):
                    file_json = load_jsonc(source_path).data
                    if self.json_template:
                        file_json = eval_json(
                            file_json, {'K': JsonTemplateK} | self.scope)
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
                        abs_target = self.target.absolute()
                        code = CodeTree(abs_target)
                        with WdSwitch(self.parent.system_path):
                            code.root.eval_and_dump(
                                self.scope, abs_target, abs_target)
        except Exception as e:
            raise SystemTemplateException([
                f'Failed to evaluate {source_path.as_posix()} for '
                f'{self.target.as_posix()}":',
                str(e)])

    def pack(self, op_stack: Optional[List[Tuple[str, str]]]=None) -> None:
        '''
        Packs the shared files from the _shared folder into the system folder
        by moving them. Optionally, it can record the operation in the
        operation stack as a pair of paths (source, target).
        '''
        if not self.shared:
            return
        # Get paths in the system and shared folders
        system_path: Path = self.parent.system_path / self.relative_source_path
        shared_path: Path = (
            SYSTEM_TEMPLATE_DATA_PATH / "_shared" / self.relative_source_path)
        system_exists = system_path.exists()
        shared_exists = shared_path.exists()
        if not system_exists and not shared_exists:
            raise SystemTemplateException([
                f"Failed to pack the file because it doesn't exist in the "
                f"system or shared folder: {self.relative_source_path}"])
        elif not system_exists and shared_exists:
            shared_path.rename(system_path)
            if op_stack is not None:
                op_stack.append([
                    shared_path.as_posix(),
                    system_path.as_posix()])
        # system_exists and not shared_exists: Already packed
        # system_exists and shared_exists: System file has priority

    def unpack(self, op_stack: Optional[List]=None) -> None:
        '''
        Unpacks the files from the system folder into the _shared folder by
        moving them. Optionally, it can record the operation in the
        operation stack as a pair of paths (source, target).
        '''
        if not self.shared:
            return
        # Get paths in the system and shared folders
        system_path: Path = self.parent.system_path / self.relative_source_path
        shared_path: Path = (
            SYSTEM_TEMPLATE_DATA_PATH / "_shared" / self.relative_source_path)
        system_exists = system_path.exists()
        shared_exists = shared_path.exists()
        if not system_exists and not shared_exists:
            raise SystemTemplateException([
                f"Failed to unpack the file because it doesn't exist in the "
                f"system or shared folder: {self.relative_source_path}"])
        elif system_exists and not shared_exists:
            system_path.rename(shared_path)
            if op_stack is not None:
                op_stack.append([
                    system_path.as_posix(),
                    shared_path.as_posix()])
        elif system_exists and shared_exists:
            print_yellow(
                "WARNING: Unable to unpack the file because a file with the "
                "same name already exists in the shared folder:\n"
                f"- Path: {self.relative_source_path}"
            )
        # not system_exists and shared_exists: Already unpacked


def parse_args() -> Tuple[Dict, Literal['pack', 'unpack']]:
    parser = argparse.ArgumentParser(
        description=(
            'System template: Regolith filter for grouping files into systems')
    )
    subparsers = parser.add_subparsers(dest='command')

    # Unpack
    parser_unpack = subparsers.add_parser(
        'unpack', help='Unpacks the shared files into the "_shared" folder')

    # Pack
    parser_pack = subparsers.add_parser(
        'pack', help='Packs the shared files into the "_shared" folder')

    # Common arguments
    for subcommand in [parser_unpack, parser_pack]:
        subcommand.add_argument(
            '--systems', nargs='+', type=str, default=None,
            required=True, help='The glob pattern to match systems')
        subcommand.add_argument(
            '--scope', type=str, default='system_template/scope.json',
            required=False, help='The path to the scope file')

    # Parse arguments
    args = parser.parse_args()


    # We can handle all commmands in the same way because they all have the
    # same arguments
    config = {
        'systems': args.systems,
        'scope_path': args.scope,
    }
    return config, args.command

def main():
    mode = 'eval'
    config = {}
    if len(sys.argv) > 1:
        if sys.argv[1] in ['pack', 'unpack']:
            config, mode = parse_args()
            print(sys.argv)
            print(config, mode)
        elif sys.argv[1] == 'undo':
            mode = 'undo'
        else:
            try:
                config = json.loads(sys.argv[1])
            except Exception:
                raise SystemTemplateException([f'Failed load the config data'])

    # Add scope
    def get_scope():
        scope = {
            'true': True, 'false': False, 'math': math, 'uuid': uuid,
            "AUTO": SpecialKeys.AUTO, 'Path': Path}
        scope_path = DATA_PATH / config.get(
            'scope_path', 'system_template/scope.json')
        scope = scope | load_jsonc(scope_path).data
        return scope
    # Try to load the auto map
    system_patterns = config.get('systems', ['**/*'])

    # Get the log path if its not null
    if 'log_path' in config:
        log_path = Path(config['log_path'])
        if not log_path.is_absolute():
            log_path = Path(os.environ['ROOT_DIR']) / log_path
    else:
        log_path = None

    try:
        auto_map_path = SYSTEM_TEMPLATE_DATA_PATH / "auto_map.json"
        auto_map = load_jsonc(auto_map_path).data
    except FileNotFoundError:
        auto_map = {}
    # Prepare the undo stack (for pack, unpack and undo)
    undo_path = SYSTEM_TEMPLATE_DATA_PATH / '.pack_undo.json'
    op_stack: List[Tuple[str, str]] = []
    try:
        if mode == 'eval':
            scope = get_scope()
            report = Report()
            for system_path in walk_system_paths(system_patterns):
                rel_sys_path = system_path.relative_to(
                    SYSTEM_TEMPLATE_DATA_PATH).as_posix()
                system = System(scope, system_path, auto_map)
                print(f"Generating system: {rel_sys_path}")
                for system_item in system.walk_system_items():
                    system_item.eval(report)
            report.dump_report(log_path)
        elif mode == 'pack':
            scope = get_scope()
            for system_path in walk_system_paths(system_patterns):
                rel_sys_path = system_path.relative_to(
                    SYSTEM_TEMPLATE_DATA_PATH).as_posix()
                system = System(scope, system_path, auto_map)
                print(f"Packing system: {rel_sys_path}")
                for system_item in system.walk_system_items():
                    system_item.pack(op_stack)
            # Save the undo stack
            with open(undo_path, 'w', encoding='utf8') as f:
                json.dump(op_stack, f, indent='\t')
        elif mode == 'unpack':
            scope = get_scope()
            for system_path in walk_system_paths(system_patterns):
                rel_sys_path = system_path.relative_to(
                    SYSTEM_TEMPLATE_DATA_PATH).as_posix()
                system = System(scope, system_path, auto_map)
                print(f"Unpacking system: {rel_sys_path}")
                for system_item in system.walk_system_items():
                    system_item.unpack(op_stack)
            # Save the undo stack
            with open(undo_path, 'w', encoding='utf8') as f:
                json.dump(op_stack, f, indent='\t')
        elif mode == 'undo':
            print(f"Undoing last pack/unpack operation")
            if not undo_path.exists():
                print_red("Nothing to undo")
                return
            with open(undo_path, 'r', encoding='utf8') as f:
                old_op_stack = json.load(f)
            for target, source in old_op_stack:
                source = Path(source)
                target = Path(target)
                if not source.is_relative_to(SYSTEM_TEMPLATE_DATA_PATH):
                    raise SystemTemplateException([
                        f"Invalid source path: {source}"])
                if not target.is_relative_to(SYSTEM_TEMPLATE_DATA_PATH):
                    raise SystemTemplateException([
                        f"Invalid target path: {target}"])
                if not source.exists():
                    raise SystemTemplateException([
                        f"Source path doesn't exist: {source}"])
                if target.exists():
                    raise SystemTemplateException([
                        f"Target path already exists: {target}"])
                source.rename(target)
                # Record reverted operation
                op_stack.append([source.as_posix(), target.as_posix()])
            # Save the undo stack
            with open(undo_path, 'w', encoding='utf8') as f:
                json.dump(op_stack, f, indent='\t')
    except SystemTemplateException as e:
        for err in e.errors:
            print_red(err)
        sys.exit(1)

if __name__ == '__main__':
    main()