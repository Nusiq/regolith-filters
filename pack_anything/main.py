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
        git_out = subprocess.check_output(
            'git describe --tags --always --abbrev=0',
            cwd=PROJECT_PATH.as_posix())
        git_out = git_out.decode('utf-8').splitlines()[0].strip()
        return git_out
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
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path_on_disk, path_in_zip in pathmap:
            if path_on_disk.is_file():
                zf.write(path_on_disk, path_in_zip.as_posix())
                continue
            if path_in_zip != Path('.'):
                zf.mkdir(path_in_zip.as_posix())
            # os.walk with topdown=True guarantees that each directory is
            # visited before its contents, so directory entries are always
            # written to the archive before any of their child files.
            for dirpath, dirnames, filenames in os.walk(path_on_disk):
                dirnames.sort()
                filenames.sort()
                rel_dir = Path(dirpath).relative_to(path_on_disk)
                for dirname in dirnames:
                    out_path = (
                        path_in_zip / rel_dir / dirname).as_posix()
                    zf.mkdir(out_path)
                for filename in filenames:
                    file = Path(dirpath) / filename
                    out_path = (
                        path_in_zip / rel_dir / filename).as_posix()
                    zf.write(file, out_path)

if __name__ == '__main__':
    main()
