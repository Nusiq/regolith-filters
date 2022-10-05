from pathlib import Path
import json
import sys
import random

FUNCTIONS_PATH = Path('BP/functions')

# {"rawtext": [{"text": "hello"}]}

# no "f", "0", "1", "7", "8" because they're hard to read
COLOR_CODES = "234569abcdeg"

def generate_tellraw_command(
        func_name: str, prefix: str="", random_colors=True) -> str:
    '''
    Generates the tellraw command with the function name.
    '''
    if random_colors:
        random.seed(func_name)
        func_name = f"§{random.sample(COLOR_CODES, 1)[0]}{func_name}"
    tellraw_data = {
        "rawtext": [
            {"text": prefix},
            {"selector": "@s"},
            {"text": ": "},
            {"text": func_name},
        ]
    }
    tellraw_text_data = json.dumps(
        tellraw_data, separators=(',', ':'), ensure_ascii=False)
    return f"tellraw @a {tellraw_text_data}"


if __name__ == '__main__':
    config = json.loads(sys.argv[1])
    if 'include' in config:
        include = config['include']
    else:
        include = ["**/*.mcfunction"]
    if 'exclude' in config:
        exclude = config['exclude']
    else:
        exclude = []
    if 'random_colors' in config:
        random_colors = config['random_colors']
    else:
        random_colors = True
    if 'prefix' in config:
        prefix = config['prefix']
    else:
        prefix = ""

    paths_set = set()
    excluded_paths_list = []
    for excluded_paths in exclude:
        for path in FUNCTIONS_PATH.glob(excluded_paths):
            if path.is_file():
                excluded_paths_list.append(path)
    for included_files in include:
        for path in FUNCTIONS_PATH.glob(included_files):
            if path.is_file() and path not in excluded_paths_list:
                paths_set.add(path)
    for path in paths_set:
        with path.open('r', encoding="utf8") as f:
            data = f.read()
        func_name = path.as_posix()[len('BP/functions/'):-len(".mcfunction")]
        tellraw_command = generate_tellraw_command(
            func_name, prefix, random_colors)
        data = f"{tellraw_command}\n" + data
        with path.open('w', encoding="utf8") as f:
            f.write(data)
