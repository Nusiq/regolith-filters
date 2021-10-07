from pathlib import Path
from typing import Iterator, List, Optional
import re



FUNCTIONS_PATH = Path('BP/functions')

BLANK_LINE = re.compile(" +\n")
JUST_DEFINE = re.compile("definefunction <([a-zA-Z_0-9]+)>:")
SUBFUNCTION = re.compile("(.* )?function <([a-zA-Z_0-9]+)>:")

def modify_function(
        path: Path, func_text: List[str],
        zero_indent=0, is_root=True, cursor=0) -> int:
    if not is_root and path.exists():
        raise RuntimeError(
            "The function file can't be created because "
            "it already exists!")
    path.parent.mkdir(exist_ok=True, parents=True)
    new_func_text = []
    modified = not is_root  # new file is considered to be modified
    first_indent = None
    while cursor < len(func_text):
        # Read line and its indentation value
        line = func_text[cursor]
        line = line.rstrip()
        no_indent_line = line.lstrip(" ")
        indent = len(line)-len(no_indent_line)
        # Indentation for blank lines doesn't matter
        if BLANK_LINE.fullmatch(line):
            new_func_text.append(no_indent_line)
            cursor += 1
            continue
        # Special case for looping subfunctions
        if not is_root:
            if first_indent is None:
                first_indent = indent
                # empty subfunction
                if first_indent <= zero_indent:
                    break
            # The end of subfunction reached
            if indent < first_indent: 
                break
            # Unindent the zero_indent
            line = line[zero_indent:]
        if match := JUST_DEFINE.fullmatch(no_indent_line):
            cursor += 1
            cursor = modify_function(
                (path.with_suffix("") / match[1]).with_suffix(".mcfunction"),
                func_text,  zero_indent=indent, is_root=False, cursor=cursor)
            modified = True
        elif match := SUBFUNCTION.fullmatch(no_indent_line):
            function_name = (
                path.relative_to(FUNCTIONS_PATH).with_suffix("") /
                match[2]
            ).as_posix()
            if match[1] is None:
                new_func_text.append(f"function {function_name}")
            else:
                new_func_text.append(f"{match[1]}function {function_name}")
            cursor += 1
            cursor = modify_function(
                (path.with_suffix("") / match[2]).with_suffix(".mcfunction"),
                func_text,  zero_indent=indent, is_root=False, cursor=cursor)
            modified = True
        else:  # comment or normal line
            new_func_text.append(no_indent_line)
            cursor += 1
    if modified:
        function_name = path.relative_to(
            FUNCTIONS_PATH).with_suffix("").as_posix()
        print(f"Modified function {function_name}.")
        with path.open('w') as f:
            f.write("\n".join(new_func_text))
    return cursor

        
if __name__ == '__main__':
    for path in FUNCTIONS_PATH.glob("**/*.mcfunction"):
        if path.is_dir():
            continue
        with path.open('r') as f:
            func_text = f.readlines()
        modify_function(path, func_text)
