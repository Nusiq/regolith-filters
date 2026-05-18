from pathlib import Path
import zipfile
import sys
import json
import os
import subprocess
from typing import Any, Callable

PROJECT_PATH = Path(os.environ['ROOT_DIR'])

class BackslashPathError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message

def print_red(text: str):
    for t in text.split('\n'):
        print("\033[91m {}\033[00m".format(t))

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
    config: dict[str, Any] = json.loads(sys.argv[1])
    output_str = config['output']
    if output_str.startswith('`') and output_str.endswith('`'):
        output_str = output_str[1:-1]
        output_str = eval(output_str, {'git_describe': get_git_tag()})


    # When the backslash paths are disabled (default), and we're not on Windows,
    # we silently replce the path segments that contain backslahses with
    # forward slashes. On Windows such paths in 'Path' object are impossible,
    # so we don't do anything.
    needs_backslash_cleanup = (
        not config.get('allow_backslash_paths', False) and
        sys.platform != "win32"
    )

    backslahs_cleanup: Callable[[Path], Path] = lambda p: p
    if needs_backslash_cleanup:
        backslahs_cleanup = lambda p: Path(p.as_posix().replace('\\', '/'))

    output: Path = Path(PROJECT_PATH) / output_str
    output.parent.mkdir(parents=True, exist_ok=True)

    # [path_on_disk, path_in_zip]
    pathmap: list[tuple[Path, Path]] = [
        (
            backslahs_cleanup(resolver_input_path(k)),
            backslahs_cleanup(Path(v)),
        )
        for k, v in config['pathmap'].items()
    ]
    try:
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
                        if needs_backslash_cleanup and out_path.find('\\') != -1:
                            raise BackslashPathError(
                                'Error: Backslash detected in one of the ZIP paths.\n'
                                f'- ZIP Path: {out_path}'
                            )
                        zf.mkdir(out_path)
                    for filename in filenames:
                        file = Path(dirpath) / filename
                        out_path = (
                            path_in_zip / rel_dir / filename).as_posix()
                        if needs_backslash_cleanup and out_path.find('\\') != -1:
                            raise BackslashPathError(
                                'Error: Backslash detected in one of the ZIP paths.\n'
                                f'- Source Path: {file.as_posix()}\n'
                                f'- ZIP Path: {out_path}'
                            )
                        zf.write(file, out_path)
    except BackslashPathError as e:
        print_red(
            f'{e.message}\n\n'
            'This is almost certainly not what you want, since file names '
            'that include backslashes are not supported on Windows. Please, '
            'make sure that the project is generated correctly, or enable '
            'the "allow_backslash_paths" option in the config file.'
        )
        output.unlink(missing_ok=True)
        exit(1)
    except Exception as e:
        output.unlink(missing_ok=True)
        raise Exception("Unexpected error while creating the ZIP file.") from e


if __name__ == '__main__':
    main()
