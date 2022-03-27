from typing import Any, Dict, List, Tuple
import merge
import json
import sys
from itertools import chain
from pathlib import Path
import math
import uuid


DATA_PATH = Path('data')
BP_PATH = Path('BP')
RP_PATH = Path('RP')


def walk_json(data, json_path=None):
    '''
    Walks JSON file (data) yields json paths.
    '''
    if json_path is None:
        json_path = []
    if isinstance(data, dict):
        for k in data.keys():
            curr_path = json_path + [k]
            if isinstance(data[k], (dict, list)):
                yield from walk_json(data[k], json_path=curr_path)
            yield tuple(curr_path)
    elif isinstance(data, list):
        for i in range(len(data)):
            curr_path = json_path + [i]
            if isinstance(data[i], (dict, list)):
                yield from walk_json(data[i], json_path=curr_path)
            yield tuple(curr_path)

def access_json(data, path):
    if len(path) == 0:
        return data
    return access_json(data[path[0]], path[1:])

def replace_templates(
        data: Any, scope: Dict[str, Any], templates: Dict[str, str],
        trigger_phrase: str) -> Tuple[Dict, bool]:
    # Gather points of iterests (things that will be replaced)
    points_of_interset = []
    for poi in walk_json(data):
        k = poi[-1]
        if isinstance(k, str) and k.startswith(trigger_phrase):
            points_of_interset.append(poi)
    if len(points_of_interset) == 0:  # No points of interests, return
        return data, False
    for poi in sorted(points_of_interset):
        # Access template
        try:
            k = poi[-1]
            template_name = k.split(":", 1)[1]
            template = templates[template_name]
        except KeyError as e:
            raise RuntimeError(f"Unable to read template {k}") from e

        # Apply template
        if len(poi) == 1:  # Templating root
            try:
                curr_scope = scope | data[poi[0]]
            except KeyError:
                continue  # Replaced by the recursive template execution, skip
            # delete POI
            del data[poi[0]]
            # Merge with template
            data = merge.deep_merge_objects(
                a=eval(template, curr_scope),
                b=data, 
                list_merge_policy=merge.ListMergePolicy.APPEND)
            # Run recursive templating
            data, _ = replace_templates(
                data, curr_scope, templates, trigger_phrase)
        else:  # Templating offspring
            parent = access_json(data, poi[:-2])
            try:
                curr_scope = scope |  access_json(parent, poi[-2:])
            except KeyError:
                continue  # Replaced by the recursive template execution, skip
            # delete POI
            del parent[poi[-2]][poi[-1]]
            # Merge with template
            parent[poi[-2]] = merge.deep_merge_objects(
                a=eval(template, curr_scope),
                b=parent[poi[-2]],
                list_merge_policy=merge.ListMergePolicy.APPEND)
            # Run recursive templating
            parent[poi[-2]], _ = replace_templates(
                parent[poi[-2]], curr_scope, templates, trigger_phrase)
    return data, True

def main(
        bp_patterns: List[str], rp_patterns: List[str], templates_path: str,
        trigger_phrase: str, sort_keys: bool, compact: bool, scope: Dict):
    '''
    Main function of the project. Adds filters to behavior- and resource-pack
    files. Read README for mor information.
    '''
    # Resolve glob patterns for BP  and RP
    bp_paths = set()
    for i in bp_patterns:
        bp_paths.update(BP_PATH.glob(i))
    rp_paths = set()
    for i in rp_patterns:
        rp_paths.update(RP_PATH.glob(i))

    # Load the template files
    templates: Dict[str, str] = {}
    tp = DATA_PATH / templates_path
    for template_path in tp.glob("**/*.py"):
        key = template_path.relative_to(tp).with_suffix("").as_posix()
        with template_path.open('r') as f:
            templates[key] = f.read()

    fp: Path
    # Replace values in file using templates
    for fp in chain(bp_paths, rp_paths):
        if not fp.exists() or not fp.is_file():
            continue
        try:
            with fp.open('r') as f:
                data = json.load(f)
        except:
            print(f"Unable to load file {fp.as_posix()}")
            continue

        data, modified = replace_templates(
            data, scope, templates, trigger_phrase)
        if not modified:
            continue  # Data not modified. Don't edit the file.

        with fp.open('w') as f:
            if compact:
                json.dump(
                    data, f, indent='\t',
                    separators=(',', ':'), sort_keys=sort_keys)
            else:
                json.dump(data, f, indent='\t', sort_keys=sort_keys)

if __name__ == '__main__':
    try:
        config = json.loads(sys.argv[1])
    except Exception:
        config = {}
    # Glob patters for finding JSON files to edit
    if 'bp_patterns' in config:
        bp_patterns = config['bp_patterns']
    else:
        bp_patterns = ['**/*.json']
    if 'rp_patterns' in config:
        rp_patterns = config['rp_patterns']
    else:
        rp_patterns = ['**/*.json']

    # File path to the templates folder
    templates_path = 'pytemplate'

    # Trigger phrase
    if 'trigger_phrase' in config:
        trigger_phrase = config['trigger_phrase']
    else:
        trigger_phrase = "TEMPLATE"
    if 'sort_keys' in config:
        sort_keys = config['sort_keys']
    else:
        sort_keys = True
    if 'compact' in config:
        compact = config['compact']
    else:
        compact = False

    # Add scope
    scope = {'true': True, 'false': False, 'math': math, 'uuid': uuid}
    if 'scope_path' not in config:
        config['scope_path'] = 'pytemplate/scope.json'
    with (DATA_PATH / config['scope_path']).open('r') as f:
        scope = scope | json.load(f)

    main(
        bp_patterns=bp_patterns,
        rp_patterns=rp_patterns,
        templates_path=templates_path,
        trigger_phrase=trigger_phrase,
        sort_keys=sort_keys,
        compact=compact,
        scope=scope,
    )
