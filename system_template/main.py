from typing import Dict, List
import json
import merge
import sys
from pathlib import Path
import shutil
import math
import uuid
from copy import copy

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

def compile_system(scope: Dict, system_path: Path):
    with (system_path / 'system_scope.json').open('r') as f:
        scope = scope | json.load(f)
    system_template_path = system_path / 'system_template.py'
    with system_template_path.open('r') as f:
        # copy to avoic outputing values from evalation
        try:
            system_template = eval(f.read(), copy(scope))
        except Exception as e:
            raise SystemTemplateException([
                f"Failed to evaluate {system_template_path.as_posix()} "
                "due to an error:",  str(e)])
    for file_template in system_template:
        if 'source' not in file_template:
            raise SystemTemplateException([
                    f"Missing 'source' in file_template: {file_template}"])
        source: Path = system_path / 'data' / file_template['source']
        if 'target' not in file_template:
            raise SystemTemplateException([
                    f"Missing 'target' in file_template: {file_template}"])
        target = file_template['target']
        if target.startswith('BP/') or target.startswith('RP/'):
            target = Path(target)
        else:
            raise SystemTemplateException([
                f'Target must start with "BP/" or "RP/": {target}'])
        # Get on_conflict policy: stop, overwrite, append_end, append_start,
        # skip or merge
        if target.suffix == '.json':
            on_conflict = file_template.get('on_conflict', 'stop')
            valid_keys = ['stop', 'overwrite', 'merge', 'skip']
            if on_conflict not in valid_keys:
                raise SystemTemplateException([
                    f"Invalid 'on_conflict' value: {on_conflict} for "
                    f"{target.as_posix}. Valid values for JSON files "
                    f"are: {valid_keys}"])
        elif target.suffix == '.lang':
            on_conflict = file_template.get('on_conflict', 'append_end')
            valid_keys = [
                'stop', 'overwrite', 'append_end', 'append_start', 'skip']
            if on_conflict not in valid_keys:
                raise SystemTemplateException([
                    f"Invalid 'on_conflict' value: {on_conflict} for "
                    f"{target.as_posix}. Valid values for .lang files "
                    f"are: {valid_keys}"])
        elif target.suffix == '.mcfunction':
            on_conflict = file_template.get('on_conflict', 'stop')
            valid_keys = [
                'stop', 'overwrite', 'append_end', 'append_start', 'skip']
            if on_conflict not in valid_keys:
                raise SystemTemplateException([
                    f"Invalid 'on_conflict' value: {on_conflict} for "
                    f"{target.as_posix}. Valid values for .lang files "
                    f"are: {valid_keys}"])
        else:
            on_conflict = file_template.get('on_conflict', 'stop')
            valid_keys = ['stop', 'overwrite', 'skip']
            if on_conflict not in valid_keys:
                raise SystemTemplateException([
                    f"Invalid 'on_conflict' value: {on_conflict} for "
                    f"{target.as_posix}. Valid values for this kind of file "
                    f"are: {valid_keys}"])
        # Handling the conflicts with skip, stop and overwrite policy here
        # other policies just read the data from are handled later
        target_data = None
        if target.exists():
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
                with target.open('r', encoding='utf8') as f:
                    if target.suffix == '.json':
                        target_data = json.load(f)
                    else:
                        target_data = f.read()
                target.unlink()
        # Python templating for JSON files
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            # Merging is possible only if target is JSON and source is either
            # python or JSON
            if target.suffix == '.json' and source.suffix in ('.json', '.py'):
                if source.suffix == '.py':
                    if file_template.get('use_global_scope', False):
                        file_scope = scope | file_template.get('scope', dict())
                    else:
                        file_scope = {
                            'true': True, 'false': False,
                            'math': math, 'uuid': uuid
                        } | file_template.get('scope', dict())
                    with source.open('r') as f:
                        file_json = eval(f.read(), file_scope)
                elif source.suffix == '.json':
                    with source.open('r') as f:
                        file_json = json.load(f)
                if on_conflict == 'merge':
                    file_json = merge.deep_merge_objects(
                        target_data, file_json,
                        list_merge_policy=merge.ListMergePolicy.APPEND)
                with target.open('w') as f:
                    json.dump(file_json, f, indent="\t", sort_keys=True)
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

def main(scope: Dict, templates_path: str):
    for system_path in (DATA_PATH / templates_path).glob("**/*"):
        if system_path.is_file():
            continue
        system_scope_path = system_path / 'system_scope.json'
        system_template_path = system_path / 'system_template.py'
        if not system_scope_path.exists() or system_scope_path.is_dir():
            continue
        if not system_template_path.exists() or system_template_path.is_dir():
            continue
        print(
            "Generating system: "
            f"{system_path.relative_to(DATA_PATH / templates_path).as_posix()}"
        )
        compile_system(scope, system_path)

if __name__ == '__main__':
    try:
        config = json.loads(sys.argv[1])
    except Exception:
        config = {}
    # File path to the templates folder
    templates_path = 'system_template'

    # Add scope
    scope = {'true': True, 'false': False, 'math': math, 'uuid': uuid}
    with (
            DATA_PATH / config.get('scope_path', 'system_template/scope.json')
            ).open('r') as f:
        scope = scope | json.load(f)
    try:
        main(scope, templates_path)
    except SystemTemplateException as e:
        for err in e.errors:
            print_red(err)
        sys.exit(1)
