from pathlib import Path
from typing import Iterator, List, Tuple, NamedTuple
import re
from collections import deque

FUNCTIONS_PATH = Path('BP/functions')

JUST_DEFINE = re.compile("definefunction <([a-zA-Z_0-9]+)>:")
SUBFUNCTION = re.compile("(.* )?function <([a-zA-Z_0-9]+)>:")
FUNCTION_TREE = re.compile("functiontree <([a-zA-Z_0-9]+)><([a-zA-Z_0-9]+) *([0-9]+)\.\.([0-9]+)(?: *([0-9]+))?>:")

class McfuncitonFile(NamedTuple):
    '''
    A function file data to save.

    :param path: a path to the file
    :param body: a body of the function as a list of strings
    '''
    path: Path
    body: List[str]

def get_function_name(path: Path):
    '''
    Returns the name of a function based on its path.
    The path must be valid (relative to FUNCTIONS_PATH)
    '''
    return path.relative_to(FUNCTIONS_PATH).with_suffix("").as_posix()

def get_subfunction_path(function_path: Path, subfunction_name: str):
    return (
        function_path.with_suffix("") / subfunction_name
    ).with_suffix(".mcfunction")

def strip_line(line) -> Tuple[str, int]:
    '''
    Returns stripped version of line and a number of spaces in the indentation
    of this line.
    '''
    # line = line.rstrip() changes the length of the line which
    # is used in indent = len(line)-len(stripped_line). Without this line
    # the function would have unexpected behavior for lines that end with
    # white spaces of the last line of the file without "\n"
    line = line.rstrip()
    stripped_line = line.rstrip().lstrip(" ")
    indent = len(line)-len(stripped_line)
    return stripped_line, indent

class CommandsWalker:
    def __init__(self, path: Path, func_text: List[str]):
        '''
        :param path: path to the root file.
        :param func_text: the list with lines of code from the root file.
        '''
        self.cursor = 0
        self.path = path
        self.func_text = func_text

    def walk_function(self) -> Iterator[McfuncitonFile]:
        '''
        Walks the commands of a function and looks for custom subfunction
        syntax. Yields new files to create.

        :param path: path to the root file.
        :param func_text: the list with lines of code from the root file.
        '''
        yield from self._walk_function(self.path)

    def walk_code_block(
            self, zero_indent: int,
            is_root: bool) -> Iterator[Tuple[str, int]]:
        '''
        Yields lines of code for current code block.

        :param zero_indent: the indentation depth that defines this code block
            everything below or equal to that indentation is considered out of
            code block and ends the iteration.
        :param is_root: whether the current code block is root (the outermost
            code block). If this value is set to true the iteration will go
            until the end of file
        '''
        first_indent = None
        if is_root:
            while self.cursor < len(self.func_text):
                yield strip_line(self.func_text[self.cursor])
                self.cursor += 1
        else:
            _, first_indent = strip_line(self.func_text[self.cursor])
            # empty subfunction
            if first_indent <= zero_indent:
                return
            # not empty subfunction
            while self.cursor < len(self.func_text):
                no_indent_line, indent = strip_line(self.func_text[self.cursor])
                if indent < first_indent:  # The end of subfunction reached
                    break

                yield no_indent_line, indent
                self.cursor += 1

    def _walk_function(
            self, path: Path, zero_indent=0,
            is_root=True) -> Iterator[McfuncitonFile]:
        if not is_root and path.exists():
            raise RuntimeError(
                "The function file can't be created because "
                "it already exists!")
        new_func_text = []
        modified = not is_root  # new file is considered to be modified

        for no_indent_line, indent in self.walk_code_block(
                zero_indent, is_root):
            if match := JUST_DEFINE.fullmatch(no_indent_line):
                self.cursor += 1
                yield from self._walk_function(
                    get_subfunction_path(path, match[1]), zero_indent=indent,
                    is_root=False)
                modified = True
            elif match := SUBFUNCTION.fullmatch(no_indent_line):
                subfunction_name = f'{get_function_name(path)}/{match[2]}'
                prefix = "" if match[1] is None else match[1]
                new_func_text.append(f"{prefix}function {subfunction_name}")
                self.cursor += 1
                yield from self._walk_function(
                    get_subfunction_path(path, match[2]), zero_indent=indent,
                    is_root=False)
                modified = True
            # elif match := FUNCTION_TREE.fullmatch(no_indent_line):
            #     m_name = match[1]
            #     m_var = match[2]
            #     m_min = int(match[3])
            #     m_max = int(match[4])
            #     m_step = match[5] if match[5] is None else int(match[5])
            else:  # comment, normal line or blank line
                new_func_text.append(no_indent_line)
        if modified:
            yield McfuncitonFile(path, new_func_text)

if __name__ == '__main__':
    # glob pattern result changed to list to avoid going over newly created
    # files
    for path in list(FUNCTIONS_PATH.glob("**/*.mcfunction")):
        if path.is_dir():
            continue
        with path.open('r') as f:
            func_text = f.readlines()

        for func_file in CommandsWalker(path, func_text).walk_function():
            func_file.path.parent.mkdir(exist_ok=True, parents=True)
            with func_file.path.open('w') as f:
                f.write("\n".join(func_file.body))
            print(f"Created new function: {get_function_name(func_file.path)}")
