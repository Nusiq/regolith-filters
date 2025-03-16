from pathlib import Path
import zipfile
import sys
import json
import os
import subprocess

PROJECT_PATH = Path(os.environ['ROOT_DIR'])

def resolver_input_path(path: str):
    if path.startswith('PROJECT:'):
        path = path[len('PROJECT:'):]
        return (PROJECT_PATH / path)
    return Path(path)

def get_git_tag():
    try:
        return subprocess.check_output(
            'git describe --tags --always --abbrev=0')
    except:
        return 'unknown'

def main():
    config = json.loads(sys.argv[1])
    output_str = config['output']
    if output_str.startswith('`') and output_str.endswith('`'):
        output_str = output_str[1:-1]
        output_str = eval(output_str, {'git_describe': get_git_tag()})

    output: Path = Path(PROJECT_PATH) / output_str
    output.parent.mkdir(parents=True, exist_ok=True)

    # [path_on_disk, path_in_zip]
    pathmap: list[tuple[Path, Path]] = [
        (resolver_input_path(k), Path(v))
        for k, v in config['pathmap'].items()
    ]
    with zipfile.ZipFile(output, 'w') as zf:
        for path_on_disk, path_in_zip in pathmap:
            if path_on_disk.is_file():
                zf.write(path_on_disk, path_in_zip)
                continue
            if Path(path_in_zip) != Path('.'):
                zf.mkdir(path_in_zip.as_posix())
            for file in path_on_disk.rglob('*'):
                out_path = (
                    path_in_zip / file.relative_to(path_on_disk)).as_posix()
                if file.is_file():
                    zf.write(file, out_path)
                    continue
                zf.mkdir(out_path)

if __name__ == '__main__':
    main()
