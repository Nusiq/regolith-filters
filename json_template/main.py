import json
from pathlib import Path
import sys
from better_json_tools import load_jsonc
from better_json_tools.compact_encoder import CompactEncoder
from itertools import chain
from regolith_json_template import eval_json, DEFAULT_SCOPE, JsonTemplateException

DATA_PATH = Path('data')
BP_PATH = Path('BP')
RP_PATH = Path('RP')

def print_red(text):
    for t in text.split('\n'):
        print("\033[91m {}\033[00m".format(t))

def main():
    '''
    The main function of the Regolith filter.
    '''
    try:
        config = json.loads(sys.argv[1])
    except Exception:
        config = {}
    # Set default config values
    config.setdefault('scope_path', 'json_template/scope.json')
    config.setdefault('patterns', ['BP/**/*.json', 'RP/**/*.json'])

    # Load the combined scope
    scope = DEFAULT_SCOPE | load_jsonc(DATA_PATH / config['scope_path']).data

    for p in chain(*[Path(".").glob(p) for p in config['patterns']]):
        # LOAD THE FILE
        try:
            file_data = load_jsonc(p).data
        except (OSError, ValueError, TypeError, LookupError) as e:
            raise JsonTemplateException(
                f"Failed to load file as JSON:\n"
                f"  File: {p}\n"
                f"  Error: {e}")
        # EVALUATE THE FILE
        try:
            file_data = eval_json(file_data, scope)
        except JsonTemplateException as e:
            raise JsonTemplateException(
                f"Failed to evaluate JSON template:\n"
                f"  File: {p}\n"
                f"  Error: {e}")
        # WRITE THE FILE
        try:
            with open(p, 'w') as f:
                json.dump(file_data, f, cls=CompactEncoder)
        except (OSError, TypeError) as e:
            # TypeError is raised when data is not JSON serializable
            raise JsonTemplateException(
                f"Failed to write file:\n"
                f"  File: {p}\n"
                f"  Error: {e}")

if __name__ == '__main__':
    try:
        main()
    except JsonTemplateException as e:
        print_red(f"ERROR: {e}")
        sys.exit(1)
