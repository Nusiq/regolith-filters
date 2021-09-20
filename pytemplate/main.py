from typing import Dict, List, Tuple
import merge
import json
import sys
from itertools import chain
from pathlib import Path
import math
import uuid


def walk_json(data, json_path=None):
    '''
    Walks JSON file (data) yields tuples: key, parent_key, parent.

    Hint: To access child value use parent[parent_key][child_key], in first
    iteration 'parent' and 'parent_key' are None.
    '''
    if json_path is None:
        json_path = []
    if isinstance(data, dict):
        for k in data.keys():
            curr_path = json_path + [k]
            if isinstance(data[k], (dict, list)):
                yield from walk_json(data[k], json_path=curr_path)
            yield curr_path
    elif isinstance(data, list):
        for i in range(len(data)):
            curr_path = json_path + [i]
            if isinstance(data[i], (dict, list)):
                yield from walk_json(data[i], json_path=curr_path)
            yield curr_path

def access_json(data, path):
    if len(path) == 0:
        return data
    return access_json(data[path[0]], path[1:])

def replace_templates(data, scope) -> Tuple[Dict, bool]:
    # Gather points of iterests (things that will be replaced)
    points_of_interset = []
    for poi in walk_json(data):
        k = poi[-1]
        if isinstance(k, str) and k.startswith(trigger_phrase):
            points_of_interset.append(poi)
    if len(points_of_interset) == 0:
        return data, False
    for poi in points_of_interset:
        try:
            k = poi[-1]
            template_name = k.split(":", 1)[1]
            template_path = Path('data') / templates_path / (template_name + '.py')
            with template_path.open('r') as f:
                template = f.read()
        except Exception as e:
            raise RuntimeError(
                f"Unable to read template {k}") from e
        if len(poi) == 1:  # Templating root
            try:
                curr_scope = scope | data[poi[0]]
            except KeyError:
                # This key must have been replaced already by the recursive
                # template support (it happens sometimes because the recursive)
                # templates can add items at the same depth level as they are.
                continue
            del data[poi[0]]
            data = merge.deep_merge_objects(
                data, eval(template, curr_scope),  merge.ListMergePolicy.APPEND)
            # Support recursive templates
            data, _ = replace_templates(
                data, curr_scope)
            continue
        # Templating offspring
        parent = access_json(data, poi[:-2])
        try:
            curr_scope = scope |  access_json(parent, poi[-2:])
        except KeyError:
            # This key must have been replaced already by the recursive
            # template support (it happens sometimes because the recursive)
            # templates can add items at the same depth level as they are.
            continue
        del parent[poi[-2]][poi[-1]]
        parent[poi[-2]] = merge.deep_merge_objects(
            parent[poi[-2]], eval(template, curr_scope),  merge.ListMergePolicy.APPEND)
        # Support ecursive templates
        parent[poi[-2]], _ = replace_templates(
            parent[poi[-2]], curr_scope)
    return data, True

def main(
        bp_patterns: List[str], rp_patterns: List[str], templates_path: str,
        trigger_phrase: str, sort_keys: bool, compact: bool, scope: Dict):
    '''
    Main function of the project. Adds filters to behavior- and resource-pack
    files. Read README for mor information.
    '''
    default_scope = {'true': True, 'false': False, 'math': math, 'uuid': uuid}
    scope = scope | default_scope

    # Resolve glob patterns
    bp_paths = []
    for i in bp_patterns:
        bp_paths.extend(j for j in Path('BP').glob(i))
    bp_paths = list(set(bp_paths))
    rp_paths = []
    for i in rp_patterns:
        rp_paths.extend(j for j in Path('RP').glob(i))
    rp_paths = list(set(rp_paths))

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

        try:
            data, modified = replace_templates(data, scope)
        except Exception as e:
            raise RuntimeError(f"File: {fp.as_posix()}: {str(e)}") from e
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
    config = json.loads(sys.argv[1])
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
    templates_path = config['templates_path']

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
    scope = {}
    if 'scope' in config:
        scope = scope | config['scope']
    main(bp_patterns, rp_patterns, templates_path, trigger_phrase, sort_keys, compact, scope)
