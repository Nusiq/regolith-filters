from typing import Dict
import json
import sys
from pathlib import Path
import shutil
import math
import uuid
from copy import copy

DATA_PATH = Path('data')
BP_PATH = Path('BP')
RP_PATH = Path('RP')


def compile_system(scope: Dict, system_path: Path):
    with (system_path / 'system_scope.json').open('r') as f:
        scope = scope | json.load(f)
    with (system_path / 'system_template.py').open('r') as f:
        # copy to avoic outputing values from evalation
        system_template = eval(f.read(), copy(scope))
    for file_template in system_template:
        source: Path = system_path / 'data' / file_template['source']
        target = file_template['target']
        if target.startswith('BP/') or target.startswith('RP/'):
            target = Path(target)
        else:
            raise Exception(f'Target must start with "BP/" or "RP/": {target}')
        print(source.as_posix(), "==>", target.as_posix())
        if target.exists():
            raise Exception(f'Target "{target}" already exists')
        # Python templating for JSON files
        if source.suffix == '.py' and target.suffix == '.json':
            if file_template.get('use_global_scope', False):
                file_scope = scope | file_template.get('scope', dict())
            else:
                file_scope = {
                    'true': True, 'false': False, 'math': math, 'uuid': uuid
                } | file_template.get('scope', dict())
            with source.open('r') as f:
                file_json = eval(f.read(), file_scope)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('w') as f:
                json.dump(file_json, f, indent="\t", sort_keys=True)
        else:  # Other files can just be copied
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source, target)

def main(scope: Dict, templates_path: str):
    for system_path in (DATA_PATH / templates_path).glob("*"):
        if system_path.is_file():
            continue
        print(f"Generating system: {system_path.name}")
        compile_system(scope, system_path)

if __name__ == '__main__':
    config = json.loads(sys.argv[1])
    # File path to the templates folder
    templates_path = 'system_template'

    # Add scope
    scope = {'true': True, 'false': False, 'math': math, 'uuid': uuid}
    with (
            DATA_PATH / config.get('scope_path', 'pytemplate/scope.json')
            ).open('r') as f:
        scope = scope | json.load(f)
    main(scope, templates_path)
