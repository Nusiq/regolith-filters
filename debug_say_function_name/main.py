from pathlib import Path
import json
import sys

FUNCTIONS_PATH = Path('BP/functions')

if __name__ == '__main__':
    config = json.loads(sys.argv[1])
    patterns = config['patterns']

    paths_set = set()
    for pattern in patterns:
        for path in FUNCTIONS_PATH.glob(pattern):
            if path.is_file():
                paths_set.add(path)
    for path in paths_set:
        with path.open('r') as f:
            data = f.read()
        func_name = path.as_posix()[len('BP/functions/'):-len(".mcfunction")]
        data = f"say {func_name}\n" + data
        with path.open('w') as f:
            f.write(data)
