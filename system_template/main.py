from __future__ import annotations

from typing import (
    Dict, List, Iterable, Literal, Tuple, Any, Optional, cast, TypeGuard)
import json
import merge
import sys
from pathlib import Path
import shutil
from copy import copy
from enum import Enum, auto
from better_json_tools import load_jsonc
from better_json_tools.compact_encoder import CompactEncoder
from better_json_tools.json_walker import JSONWalker
from regolith_subfunctions import CodeTree
from regolith_json_template import eval_json, JsonTemplateK, JsonTemplateJoinStr
import argparse
from typing import TypedDict, Literal
import io
import os

# Overwrite the functions path of the regolith_subfunctions to be an absolute
# path. This shoudln't break anything, but it will allow us to set pass
# absolute paths to the subfunction files.
import regolith_subfunctions
regolith_subfunctions.FUNCTIONS_PATH = Path('BP/functions').absolute()

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
    '''
    Special keys used for the "target" property in "_map.py"
    '''
    # Use auto mapping, treat the root of the system as the root of the path
    AUTO = auto()
    # Same as the AUTO mapping, but add the name of the system to the export path
    AUTO_SUBFOLDER = auto()
    # Auto map to the correct folders in the RP or BP folders, but don't add the
    # subpath in the system folder
    AUTO_FLAT = auto()
    # Works like AUTO_FLAT, but adds the name of the system to the export path
    AUTO_FLAT_SUBFOLDER = auto()

DATA_PATH = Path('data')
SYSTEM_TEMPLATE_DATA_PATH = DATA_PATH / 'system_template'
BP_PATH = Path('BP')
RP_PATH = Path('RP')

class MergeStatus(Enum):
    MERGED = 'Merged.'
    APPENDED_END = 'Appended content to the end.'
    APPENDED_START = 'Inserted content at the start.'
    SKIPPED = 'Skipped.'
    OVERWRITTEN = 'Overwritten.'
    CREATED = 'Created.'
    SKIPPED_EXPORT_ONCE = 'Skipped (export once enabled).'


OnConflictPolicy = Literal[
    'stop',
    'overwrite',
    'merge',
    'skip',
    'append_start',
    'append_end'
]

class Source(TypedDict):
    path: str
    status: str

class FileReport(TypedDict):
    sources: list[Source]


class Report:
    def __init__(self):
        self.file_reports: dict[str, FileReport] = {}
    
    def _init_report(self, target: str):
        '''
        Initializes a report for a file if it doesn't exist.
        '''
        if target not in self.file_reports:
            self.file_reports[target] = FileReport(sources=[],)

    def append_source(
            self, target: Path,
            source: Path,
            status: MergeStatus):
        target_posix = target.as_posix()
        self._init_report(target_posix)
        self.file_reports[target_posix]['sources'].append(
            Source(path=source.as_posix(), status=status.value)
        )

    def dump_report(self, path: Path):
        '''Dump the report to the specified path'''
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='utf8') as f:
            json.dump(self.file_reports, f, cls=CompactEncoder)

    def dump_report_to_file(self, file: io.TextIOWrapper):
        '''Dump the report to the file'''
        json.dump(self.file_reports, file, indent=4, cls=CompactEncoder)

    def is_known_source_target_pair(self, source: Path, target: Path) -> bool:
        '''
        Checks if the specified source file, has been already used to modify
        the target file. Returns True if if it has been used, False otherwise.
        '''
        source_posix = source.as_posix()
        target_posix = target.as_posix()
        if target_posix in self.file_reports:
            for report in self.file_reports[target_posix]['sources']:
                if report['path'] == source_posix:
                    return True
        return False

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

class Mapping(TypedDict):
    target: str
    replace_extension: str

class AutoMappingProvider:
    def __init__(self, data_walker: Optional[JSONWalker]=None):
        self.data: Dict[str, Mapping] = {}
        if data_walker is None:
            return
        for mapping_walker in data_walker // str:
            key: str = mapping_walker.parent_key
            value: Any = mapping_walker.data
            if isinstance(value, str):
                self.data[key] = {
                    "target": value,
                    "replace_extension": key
                }
            elif isinstance(value, dict):
                target_walker = mapping_walker / "target"
                if not target_walker.exists:
                    raise SystemTemplateException([
                        'The "target" property of the auto mapping is missing.',
                        f'Key: {key}',
                        f'JSON path: {mapping_walker.path_str}'])
                if not isinstance(target_walker.data, str):
                    raise SystemTemplateException([
                        'The "target" property of the auto mapping must be a'
                        'string with the mapping path.',
                        f'Key: {key}',
                        f'JSON path: {mapping_walker.path_str}'])
                replace_extension_walker = mapping_walker / "replace_extension"
                if not replace_extension_walker.exists:
                    replace_extension = key
                elif not isinstance(replace_extension_walker.data, str):
                    raise SystemTemplateException([
                        'The "replace_extension" property of the auto mapping must '
                        'be a string.',
                        f'Key: {key}',
                        f'JSON path: {mapping_walker.path_str}'])
                else:
                    replace_extension = replace_extension_walker.data
                self.data[key] = {
                    "target": target_walker.data,
                    "replace_extension": replace_extension
                }
            else:
                raise SystemTemplateException([
                    'The auto mapping must be a string or an object.',
                    f'Key: {key}',
                    f'JSON path: {mapping_walker.path_str}'])

    def get_auto_target_mapping(
            self, source: Path, middle: str="",
            stem: None | str = None) -> Path:
        '''
        Gets the target path for the AUTO mapping (using the AUTO or AUTO_SUBFOLDER)
        special keys.

        :param source: The path to the source file
        :param middle: The middle part inserted into the path. When using the
            AUTO_SUBFOLDER special key, this will be the name of the system.
            Otherwise it will be an empty string (nothing will be inserted).
        :param stem: The optional property that overwrites the stem of the
            target path.
        '''
        for key, map_data in self.data.items():
            if key == "":
                continue  # Maybe this should be an error?
            if source.name.endswith(key):
                if stem is None:
                    stem = source.name[:-len(key)]
                name = stem + map_data['replace_extension']
                return (
                    Path(map_data['target']) / middle / source.with_name(name))
        raise Exception(
            "Failed to find an AUTO mapping export target for "
            f"{source.as_posix()}")


def walk_system_paths(systems: List[str]) -> Iterable[tuple[Path, Optional[Path]]]:
    '''
    Recursively walks the directories inside the SYSTEM_TEMPLATE_DATA_PATH
    and yields pairs of (system_path, group_path). The group_path is the path
    to a directory that contains the _group_scope.json file and is an ancestor
    of the system_path. If such directory doesn't exist, the group_path is
    None.
    '''
    group_path: Optional[Path] = None
    for root, dirs_, _ in os.walk(SYSTEM_TEMPLATE_DATA_PATH.as_posix()):
        # If there is a group path, check if we are still in it
        if group_path is not None:
            if not Path(root).is_relative_to(group_path):
                group_path = None
        
        # Check if the root is a group
        group_path_candidate = Path(root)
        group_scope_path = group_path_candidate / '_group_scope.json'
        found_group = False
        if group_scope_path.exists() and group_scope_path.is_file():
            # Don't allow nested groups
            if group_path is not None:
                raise SystemTemplateException([
                    "Nested groups are not allowed. The group path is "
                    "already in a group:",
                    f"Path: {group_path_candidate.as_posix()}",
                    f"Parent group path: {group_path.as_posix()}"
                ])
            group_path = group_path_candidate
            found_group = True
        # Check if the root is a system
        system_path = Path(root)
        system_scope_path = system_path / '_scope.json'
        if not system_scope_path.exists() or system_scope_path.is_dir():
            continue
        file_map_path = system_path / '_map.py'
        if not file_map_path.exists() or file_map_path.is_dir():
            continue
        # The system can't be both a group and a system at the same time
        if found_group:
            raise SystemTemplateException([
                f"You can't have a group and a system at the same path. "
                "The directory of a system can't contain a _group_scope.json:",
                f"Path: {system_path.as_posix()}"])

        relative_path = system_path.relative_to(DATA_PATH)
        for system_glob in systems:
            if relative_path.match(system_glob):
                yield system_path, group_path
                # Don't walk into the system. No nested systems allowed!
                dirs_.clear()
                break
        else:  # It's not a system. Manage the childern to walk into them.
            # The dirs_ can be modified to remove the directories that we don't
            # want to walk into or to change the walk order.
            dirs_.sort()
            for special in ["_shared", "_plugins"]:
                try:
                    dirs_.remove(special)
                except ValueError:
                    pass

class System:
    def __init__(
            self, scope: Dict, system_path: Path, group_path: Optional[Path],
            auto_map: AutoMappingProvider):
        plugins_path = system_path / '_plugins'
        if plugins_path.exists():
            for plugin_path in plugins_path.rglob("*.py"):
                if plugin_path.is_dir():
                    continue
                plugin_scope = load_plugin(plugin_path, system_path)
                scope = scope | plugin_scope
        scope_path = system_path / '_scope.json'
        if group_path is not None:
            try:
                group_scope = load_jsonc(group_path / '_group_scope.json').data
                scope = scope | group_scope
            except Exception as e:
                raise SystemTemplateException([
                    f"Failed to load the _group_scope.json file due to an error:",
                    f"Path: {group_path.as_posix()}",
                    str(e)])
        try:
            self.scope: Dict[str, Any] = scope | load_jsonc(scope_path).data
        except Exception as e:
            raise SystemTemplateException([
                f"Failed to load the _scope.json file due to an error:",
                f"Path: {scope_path.as_posix()}",
                str(e)])
        self.system_path: Path = system_path
        self.group_path: Optional[Path] = group_path
        self.file_map: List[Dict] = self._init_file_map(
            system_path / '_map.py')
        self.auto_map: AutoMappingProvider = auto_map

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
        if not isinstance(self.file_map, list):
            raise SystemTemplateException([
                "The _map.py must be a list of dicts."])
        for data in self.file_map:
            if not isinstance(data, dict):
                raise SystemTemplateException([
                    "The _map.py must be a list of dicts."])
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
                    if source_path.is_relative_to(self.system_path / '_plugins'):
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

        source_file_type, target_file_type = self._init_file_types(
            data, self.relative_source_path.suffix, self.target.suffix)
        self.source_file_type = source_file_type
        self.target_file_type = target_file_type

        self.on_conflict: OnConflictPolicy = self._init_on_conflict(data)
        self.json_template: bool = data.get('json_template', False)
        self.scope = self.parent.scope | data.get('scope', {})
        self.subfunctions: bool = data.get(
            # default for .mcfunction is True but for .lang is False
            'subfunctions', self.target_file_type == '.mcfunction')
        self.export_once: bool = data.get('export_once', False)

        if (
                self.on_conflict not in [
                    'merge', 'append_start', 'append_end'
                ] and
                self.export_once):
            raise SystemTemplateException([
                "The 'export_once' property can be used only with the "
                "export policies that try to merge the files: "
                "'append_start', 'append_end' and 'merge'.\n"
                f"Item: {self.relative_source_path.as_posix()}"])

    def _init_target(self, data: dict[str, Any]) -> Path:
        '''
        In the __init__ function, creates teh target path either by reading it
        from the data or by evaluating the AUTO mapping.
        '''
        if 'target' not in data:
            raise SystemTemplateException([
                f"Missing 'target'  property in one of the "
                f"_map.py items: {data}"])
        
        # Parse the target property
        target_dir: str | SpecialKeys
        target_stem: Optional[str] = None
        t = data['target']
        match t:
            case str() | SpecialKeys():
                target_dir = t
            case {'stem': str(), 'dir': str() | SpecialKeys()}:
                target_dir = t['dir']
                target_stem = t['stem']
            case _:
                raise SystemTemplateException([
                    f"Invalid target value in the _map.py item:\n{data}.\n"
                    "The target must be one of the following:\n"
                    "- A string with the path to the target directory\n"
                    "- An AUTO mapping object\n"
                    "- An object with 'dir' (AUTO maping or str) and 'stem' "
                    "(str) properties."
                ])
        
        # Resolve the target to a path
        system_name_path: str = self.parent.system_path.relative_to(
            # Insert the name of the system. If the system is a part
            # of a group, then the name of the system is a path
            # relative to the group.
            SYSTEM_TEMPLATE_DATA_PATH
            if self.parent.group_path is None
            else self.parent.group_path
        ).as_posix()

        match target_dir:
            case SpecialKeys.AUTO:
                target = self.parent.auto_map.get_auto_target_mapping(
                    source=self.relative_source_path,
                    stem=target_stem)
            case SpecialKeys.AUTO_SUBFOLDER:
                target = self.parent.auto_map.get_auto_target_mapping(
                    source=self.relative_source_path,
                    middle=system_name_path,
                    stem=target_stem
                )
            case SpecialKeys.AUTO_FLAT:
                target = self.parent.auto_map.get_auto_target_mapping(
                    source=Path(self.relative_source_path.name),
                    stem=target_stem
                )
            case SpecialKeys.AUTO_FLAT_SUBFOLDER:
                target = self.parent.auto_map.get_auto_target_mapping(
                    source=Path(self.relative_source_path.name),
                    middle=system_name_path,
                    stem=target_stem
                )
            case _:
                target = Path(target_dir)

        target_str = target.as_posix()
        if not (
                target_str.startswith('BP/') or
                target_str.startswith('RP/') or
                target_str.startswith('data/')
        ):
            raise SystemTemplateException([
                'Failed to resolve the export target to a valid path. The '
                'target must start with "BP/", "RP/" or "data/".',
                f'Export target: {target_str}'])
        return Path(target)

    def _init_file_types(
        self, data: Dict[Any, Any],
        source_suffix: str,
        target_suffix: str
    ) -> tuple[str, str]:
        '''
        In the __init__ function, creates the source_file_type and
        target_file_type either by reading them from the data or by inserting
        the default values (based on the actual file extensions).

        The file types are file extensions with the leading dot. For example:
        ".json" not "json", even though the user prvides "json" in the _map.py
        '''
        source_file_type: str = source_suffix
        target_file_type: str = target_suffix
        match data:
            case {'file_type': str(ft)}:
                source_file_type = target_file_type = ft
            case {'file_type': dict(ft)}:  # type: ignore
                if 'source' in ft:
                    if not isinstance(ft['source'], str):
                        raise SystemTemplateException([
                            "Invalid source file type (must be a string)"])
                    source_file_type = ft['source']
                if 'target' in ft:
                    if not isinstance(ft['target'], str):
                        raise SystemTemplateException([
                            "Invalid target file type (must be a string)"])
                    target_file_type = ft['target']
            case _: pass

        # Removing and adding the leading dot makes sure that the end result
        # will always have the leading dot regardles of the user input.
        source_file_type = source_file_type.removeprefix('.')
        target_file_type = target_file_type.removeprefix('.')
        return f'.{source_file_type}', f'.{target_file_type}'

    def _init_on_conflict(
        self, data: dict[str, Any]
    ) -> OnConflictPolicy:
        '''
        In the __init__ function, creates the on_conflict policy either by
        reading it from the data or by inserting the default value.
        Additionally checks if the policy is valid for the target file type.
        '''
        # Get on_conflict policy: stop, overwrite, append_end, append_start,
        # skip or merge
        def _in_valid_on_conflict_keys(
                value: Any,
                valid_keys: List[OnConflictPolicy]
        ) -> TypeGuard[OnConflictPolicy]:
            return value in valid_keys

        valid_keys: List[OnConflictPolicy]
        if self.target_file_type in ('.material', '.json'):
            on_conflict = data.get('on_conflict', 'stop')
            valid_keys = ['stop', 'overwrite', 'merge', 'skip']
            if not _in_valid_on_conflict_keys(on_conflict, valid_keys):
                raise SystemTemplateException([
                    f"Invalid 'on_conflict' value: {on_conflict} for "
                    f"{self.target.as_posix()}. Valid values for JSON files "
                    f"are: {valid_keys}"])
        elif self.target_file_type == '.lang':
            on_conflict = data.get('on_conflict', 'append_end')
            valid_keys = [
                'stop', 'overwrite', 'append_end', 'append_start', 'skip']
            if not _in_valid_on_conflict_keys(on_conflict, valid_keys):
                raise SystemTemplateException([
                    f"Invalid 'on_conflict' value: {on_conflict} for "
                    f"{self.target.as_posix()}. Valid values for .lang files "
                    f"are: {valid_keys}"])
        elif self.target_file_type == '.mcfunction':
            on_conflict = data.get('on_conflict', 'stop')
            valid_keys = [
                'stop', 'overwrite', 'append_end', 'append_start', 'skip']
            if not _in_valid_on_conflict_keys(on_conflict, valid_keys):
                raise SystemTemplateException([
                    f"Invalid 'on_conflict' value: {on_conflict} for "
                    f"{self.target.as_posix()}. Valid values for .lang files "
                    f"are: {valid_keys}"])
        else:
            on_conflict = data.get('on_conflict', 'stop')
            valid_keys = [
                'stop', 'overwrite', 'skip', 'append_start', 'append_end']
            if not _in_valid_on_conflict_keys(on_conflict, valid_keys):
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
        source_path_candidates: List[Path] = [
            self.parent.system_path / self.relative_source_path
        ]
        if self.shared:
            if self.parent.group_path is not None:
                source_path_candidates.append(
                    self.parent.group_path / "_shared" /
                    self.relative_source_path)
            source_path_candidates.append(
                SYSTEM_TEMPLATE_DATA_PATH / "_shared" / self.relative_source_path)

        source_path: Path = source_path_candidates[0]
        for source_path_candidate in source_path_candidates:
            if source_path_candidate.exists():
                source_path = source_path_candidate
                break
        else:
            raise SystemTemplateException([
                "The source file doesn't exist:",
                f"{source_path.as_posix()}"])

        # HANDLE EXPORT ONCE OPTION
        if (
                self.export_once and
                report.is_known_source_target_pair(source_path, self.target)):
            report.append_source(
                self.target, source_path,
                MergeStatus.SKIPPED_EXPORT_ONCE)
            return

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
                report.append_source(
                    self.target, source_path, MergeStatus.OVERWRITTEN)
                self.target.unlink()
            elif self.on_conflict == 'skip':
                print(f"Skipping {self.target.as_posix()}")
                report.append_source(
                    self.target, source_path, MergeStatus.SKIPPED)
                return
            elif self.on_conflict == 'merge':
                try:
                    report.append_source(
                        self.target, source_path,  MergeStatus.MERGED)
                    target_data = load_jsonc(self.target).data
                except Exception as e:
                    raise SystemTemplateException([
                        "Failed to load the target file for merging:\n"
                        f"- Source file: {source_path.as_posix()}\n"
                        f"- Error: {str(e)}"])
                self.target.unlink()
            elif self.on_conflict in ['append_start', 'append_end']:
                try:
                    report.append_source(
                        self.target,
                        source_path,
                        (
                            MergeStatus.APPENDED_END
                            if self.on_conflict == 'append_end'
                            else MergeStatus.APPENDED_START
                        )
                    )
                    with self.target.open('r', encoding='utf8') as f:
                        target_data = f.read()
                except Exception as e:
                    raise SystemTemplateException([
                        "Failed to load the target file for merging:\n"
                        f"- Source file: {source_path.as_posix()}\n"
                        f"- Error: {str(e)}"])
                self.target.unlink()
        else:
            report.append_source(self.target, source_path, MergeStatus.CREATED)
        # INSERT SOURCE/GENERATED DATA INTO TARGET
        try:
            self.target.parent.mkdir(parents=True, exist_ok=True)
            # Merging is possible only if target is JSON and source is either
            # python or JSON
            if (
                    self.target_file_type in ('.material', '.json') and
                    self.source_file_type in ('.material', '.json', '.py')):
                file_json: Any = None
                file_text: str = None  # Used if parsing is not necessary
                needs_parsing = (
                    self.source_file_type == '.py' or
                    self.json_template or
                    self.on_conflict == 'merge')
                if self.source_file_type == '.py':
                    source_text = source_path.read_text(encoding='utf8')
                    with WdSwitch(self.parent.system_path):
                        file_json = eval(source_text, self.scope)
                elif self.source_file_type in ('.material', '.json'):
                    if needs_parsing:
                        file_json = load_jsonc(source_path).data
                        if self.json_template:
                            file_json = eval_json(
                                file_json, {
                                    "K": JsonTemplateK,
                                    "JoinStr": JsonTemplateJoinStr,
                                } | self.scope)
                    else:
                        file_text = source_path.read_text(encoding='utf8')
                file_json = cast(Dict[str, Any], file_json)  # assertion for mypy
                if self.on_conflict == 'merge':
                    file_json = merge.deep_merge_objects(
                        target_data, file_json,
                        list_merge_policy=merge.ListMergePolicy.APPEND)
                if needs_parsing:  # File was parsed, so we need to dump it
                    with self.target.open('w') as f:
                        json.dump(file_json, f, cls=CompactEncoder)
                else:  # File was not parsed, so we just write the text
                    with self.target.open('w', encoding='utf8') as f:
                        f.write(file_text)
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
                if self.target_file_type in ['.mcfunction', '.lang']:
                    if self.subfunctions:
                        abs_target = self.target.absolute()
                        code = CodeTree(abs_target)
                        with WdSwitch(self.parent.system_path):
                            code.root.eval_and_dump(
                                self.scope, abs_target, abs_target)
        except Exception as e:
            raise SystemTemplateException([
                f'Failed to evaluate file.',
                f'Source: {source_path.as_posix()}',
                f'Target: {self.target.as_posix()}',
                f'Error: {e}'])

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
        group_shared_path: Optional[Path] = None
        if self.parent.group_path is not None:
            group_shared_path = (
                self.parent.group_path / "_shared" / self.relative_source_path)
            group_shared_exists = group_shared_path.exists()
        else:
            group_shared_exists = False
        system_exists = system_path.exists()
        shared_exists = shared_path.exists()
        if not system_exists and not shared_exists and not group_shared_exists:
            raise SystemTemplateException([
                f"Failed to pack the file because it doesn't exist in the "
                f"system or shared folder: {self.relative_source_path}"])
        elif not system_exists and group_shared_exists:
            # It's impossible for group_shared_path to be None here
            group_shared_path = cast(Path, group_shared_path)
            group_shared_path.rename(system_path)
            if op_stack is not None:
                op_stack.append([
                    group_shared_path.as_posix(),
                    system_path.as_posix()])
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
        group_shared_path: Optional[Path] = None
        if self.parent.group_path is not None:
            group_shared_path = (
                self.parent.group_path / "_shared" / self.relative_source_path)
            group_shared_exists = group_shared_path.exists()
        else:
            group_shared_exists = False
        is_group = group_shared_path is not None
        system_exists = system_path.exists()
        shared_exists = shared_path.exists()
        if not system_exists and not shared_exists and not group_shared_exists:
            raise SystemTemplateException([
                f"Failed to unpack the file because it doesn't exist in the "
                f"system or shared folder: {self.relative_source_path}"])
        elif system_exists and not group_shared_exists and is_group:
            system_path.rename(group_shared_path)
            if op_stack is not None:
                op_stack.append([
                    system_path.as_posix(),
                    group_shared_path.as_posix()])
        elif system_exists and not shared_exists and not is_group:
            system_path.rename(shared_path)
            if op_stack is not None:
                op_stack.append([
                    system_path.as_posix(),
                    shared_path.as_posix()])
        elif (
                (system_exists and group_shared_exists and is_group) or
                (system_exists and shared_exists and not is_group)):
            print_yellow(
                "WARNING: Unable to unpack the file because a file with the "
                "same name already exists in the target shared folder:\n"
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


def load_plugin(plugin_path: Path, wd_path: Path) -> Dict:
    '''
    Loads a plugin from give file path and returns its scope.
    '''
    plugin_scope = {}
    try:
        plugin_text = plugin_path.read_text()
        with WdSwitch(wd_path):
            exec(plugin_text, plugin_scope)
            del plugin_scope['__builtins__']
    except Exception as e:
        raise SystemTemplateException([
            f'Failed to load global plugin.',
            f'Path: {plugin_path.as_posix()}',
            f'Error:',
            str(e)
        ])
    for reserved_variable in [
            'K', 'JoinStr', 'true', 'false', 'AUTO', 'AUTO_SUBFOLDER',
            'AUTO_FLAT_SUBFOLDER', 'AUTO_FLAT']:
        if reserved_variable in plugin_scope:
            raise SystemTemplateException([
                'Failed to load plugin.',
                f'Path: {plugin_path.as_posix()}',
                'Error:',
                'The plugin cannot define '
                f'"{reserved_variable}" variable as it is '
                'reserved for system_template.'
            ])
    return plugin_scope

def main():
    mode = 'eval'
    config = {}
    if len(sys.argv) > 1:
        if sys.argv[1] in ['pack', 'unpack']:
            config, mode = parse_args()
            # print(sys.argv)
            # print(config, mode)
        elif sys.argv[1] == 'undo':
            mode = 'undo'
        else:
            try:
                config = json.loads(sys.argv[1])
            except Exception:
                raise SystemTemplateException([f'Failed load the config data'])

    # Add scope
    def get_scope() -> Dict[str, Any]:
        scope = {
            'true': True, 'false': False,
            "AUTO": SpecialKeys.AUTO,
            "AUTO_SUBFOLDER": SpecialKeys.AUTO_SUBFOLDER,
            "AUTO_FLAT_SUBFOLDER": SpecialKeys.AUTO_FLAT_SUBFOLDER,
            "AUTO_FLAT": SpecialKeys.AUTO_FLAT}
        plugins_path = DATA_PATH / 'system_template/_plugins'
        for plugin_path in plugins_path.rglob('*.py'):
            if plugin_path.is_dir():
                continue
            plugin_scope = load_plugin(
                plugin_path, DATA_PATH / 'system_template')
            scope = scope | plugin_scope
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

    # Reused in different modes to get the ayto map
    def get_auto_map(scope: Dict[str, Any]) -> AutoMappingProvider:
        try:
            auto_map_path = SYSTEM_TEMPLATE_DATA_PATH / "auto_map.json"
            auto_map = AutoMappingProvider(
                JSONWalker(
                    eval_json(
                        load_jsonc(auto_map_path).data,
                        {
                            "K": JsonTemplateK,
                            "JoinStr": JsonTemplateJoinStr,
                        } | scope
                    )
                )
            )
        except FileNotFoundError:
            auto_map = AutoMappingProvider(JSONWalker({}))
        return auto_map
    # Prepare the undo stack (for pack, unpack and undo)
    undo_path = SYSTEM_TEMPLATE_DATA_PATH / '.pack_undo.json'
    op_stack: List[Tuple[str, str]] = []
    try:
        if mode == 'eval':
            scope = get_scope()
            report = Report()
            auto_map = get_auto_map(scope)
            for system_path, group_path in walk_system_paths(system_patterns):
                system = System(scope, system_path, group_path, auto_map)
                rel_sys_path = system_path.relative_to(
                    SYSTEM_TEMPLATE_DATA_PATH).as_posix()
                print(f"Generating system: {rel_sys_path}")
                for system_item in system.walk_system_items():
                    system_item.eval(report)
            if log_path is not None:
                report.dump_report(log_path)
        elif mode == 'pack':
            scope = get_scope()
            auto_map = get_auto_map(scope)
            for system_path, group_path in walk_system_paths(system_patterns):
                system = System(scope, system_path, group_path, auto_map)
                rel_sys_path = system_path.relative_to(
                    SYSTEM_TEMPLATE_DATA_PATH).as_posix()
                print(f"Packing system: {rel_sys_path}")
                for system_item in system.walk_system_items():
                    system_item.pack(op_stack)
            # Save the undo stack
            with open(undo_path, 'w', encoding='utf8') as f:
                json.dump(op_stack, f, indent='\t')
        elif mode == 'unpack':
            scope = get_scope()
            auto_map = get_auto_map(scope)
            for system_path, group_path in walk_system_paths(system_patterns):
                system = System(scope, system_path, group_path, auto_map)
                rel_sys_path = system_path.relative_to(
                    SYSTEM_TEMPLATE_DATA_PATH).as_posix()
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