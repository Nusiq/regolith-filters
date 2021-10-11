from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple, NamedTuple, TypeVar
import re
from collections import deque
from safe_eval import safe_eval

FUNCTIONS_PATH = Path('BP/functions')

JUST_DEFINE = re.compile("definefunction <([a-zA-Z_0-9]+)>:")
SUBFUNCTION = re.compile("(.* )?function <([a-zA-Z_0-9]+)>:")
FUNCTION_TREE = re.compile("functiontree <([a-zA-Z_0-9]+)><([a-zA-Z_0-9]+) *([0-9]+)\.\.([0-9]+)(?: *([0-9]+))?>:")


EVAL = re.compile("`eval:([a-zA-Z_0-9+\-/*+ ()]+)`")
T = TypeVar("T")


class McfuncitonFile(NamedTuple):
    '''
    A function file data to save.

    :param path: a path to the file
    :param body: a body of the function as a list of strings
    '''
    path: Path
    body: List[str]
    is_root_block: bool=False

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

def eval_line_of_code(line: str, scope: Dict[str, int]):
    while match := EVAL.search(line):
        l, r = match.span()
        line = line[:l] + str(safe_eval(match[1], scope)) + line[r:]
    return line

class CommandsWalker:
    def __init__(
            self, path: Path, func_text: List[str],
            scope: Optional[Dict[str,int]]=None, is_root_file=True):
        '''
        :param path: path to the root file.
        :param func_text: the list with lines of code from the root file.
        '''
        self.cursor = 0
        self.path = path
        self.func_text = func_text
        self.scope = {} if scope is None else scope
        self.is_root_file = is_root_file


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
            is_root_block: bool) -> Iterator[Tuple[str, int, int]]:
        '''
        Yields lines of code for current code block.

        :param zero_indent: the indentation depth that defines this code block
            everything below or equal to that indentation is considered out of
            code block and ends the iteration.
        :param is_root_block: whether the current code block is root
            (the outermost code block). If this value is set to true the
            iteration will go until the end of file
        '''
        first_indent = None
        if is_root_block:
            while self.cursor < len(self.func_text):
                line, indent = strip_line(self.func_text[self.cursor])
                yield line, indent, 0
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

                yield no_indent_line, indent, first_indent
                self.cursor += 1

    def _walk_function(
            self, path: Path, zero_indent=0,
            is_root_block=True) -> Iterator[McfuncitonFile]:
        if not is_root_block and path.exists():
            raise RuntimeError(
                "The function file can't be created because "
                "it already exists!")
        new_func_text = []
        modified = not is_root_block  # new file is considered to be modified

        for no_indent_line, indent, base_indent in self.walk_code_block(
                zero_indent, is_root_block):
            if match := JUST_DEFINE.fullmatch(no_indent_line):
                self.cursor += 1
                yield from self._walk_function(
                    get_subfunction_path(path, match[1]),
                    zero_indent=indent, is_root_block=False)
                self.cursor -= 1
                modified = True
            elif match := SUBFUNCTION.fullmatch(no_indent_line):
                subfunction_name = f'{get_function_name(path)}/{match[2]}'
                prefix = "" if match[1] is None else match[1]
                new_func_text.append(f"{prefix}function {subfunction_name}")
                self.cursor += 1
                yield from self._walk_function(
                    get_subfunction_path(path, match[2]),
                    zero_indent=indent, is_root_block=False)
                self.cursor -= 1
                modified = True
            elif match := FUNCTION_TREE.fullmatch(no_indent_line):
                m_name = match[1]
                m_var = match[2]
                m_min = int(match[3])
                m_max = int(match[4])
                m_step = 1 if match[5] is None else int(match[5])
                self.cursor += 1
                yield from self.create_function_tree(
                    path, m_name, m_var, m_min, m_max, m_step, zero_indent,
                    new_func_text)
                self.cursor -= 1
                modified = True
            else:  # comment, normal line or blank line
                new_func_text.append(
                    " "*(indent-base_indent) +  # Python goes "b"+"r"*10
                    eval_line_of_code(no_indent_line, self.scope))
        if modified:
            yield McfuncitonFile(
                path, new_func_text,
                is_root_block=is_root_block and self.is_root_file)

    def create_function_tree(
            self, path: Path, name: str, variable: str, min_: int, max_: int,
            step: int, zero_indent: int, parent_function_text: List[str]
            ) -> Iterator[McfuncitonFile]:
        '''
        Yields the functions from function tree.
        '''
        def yield_splits(
                list: List[T],
                is_root_block=True) -> Iterator[Tuple[T, T, T, T, bool]]:
            if len(list) <= 1:
                return
            split = len(list)//2
            left, right = list[:split], list[split:]
            yield list[0], left[-1], right[0], list[-1], is_root_block
            yield from yield_splits(left, False)
            yield from yield_splits(right, False)
        body_list: List[str] = []
        leaf_values: List[int] = [i for i in range(min_, max_, step)]

        for no_indent_line, indent, base_indent in self.walk_code_block(
                zero_indent, False):
            body_list.append(" "*(indent-base_indent) + no_indent_line)
        if len(body_list) == 0:
            raise RuntimeError(
                f'Missing body for function tree "{name}" of '
                f'"{get_function_name(path)}" function')
        for left_min, left_max, right_min, right_max, is_root_block in yield_splits(
                leaf_values):
            # Sorting items if of reverse iteration
            left_min, left_max, right_min, right_max = sorted(
                (left_min, left_max, right_min, right_max))
            branch_path = get_subfunction_path(
                path, f'{name}_{left_min}_{right_max}')
            left_prefix = (
                f'execute @s[scores={{{variable}={left_min}..{left_max}}}]'
                ' ~ ~ ~ ')
            right_prefix = (
                f'execute @s[scores={{{variable}={right_min}..{right_max}}}]'
                ' ~ ~ ~ ')
            
            # Left branch half
            if left_min != left_max:  # go deeper into tree branches
                left_branch_path = get_subfunction_path(
                    path, f'{name}_{left_min}_{left_max}')
                left_suffix = (
                    f'function {get_function_name(left_branch_path)}')
            elif len(body_list) == 1:  # Add leaf command
                self.scope[variable] = left_min
                left_suffix = eval_line_of_code(
                    body_list[0], self.scope)
            else:  # Add leaf function
                left_branch_path = get_subfunction_path(
                    path, f'{name}_{left_min}_{left_max}')
                left_suffix = (
                    f'function {get_function_name(left_branch_path)}')
                self.scope[variable] = left_min
                yield from CommandsWalker(
                    left_branch_path, body_list,
                    self.scope, is_root_file=False
                ).walk_function()

            # Right branch half
            if right_min != right_max:
                right_branch_path = get_subfunction_path(
                    path, f'{name}_{right_min}_{right_max}')
                right_suffix = (
                    f'function {get_function_name(right_branch_path)}')
            elif len(body_list) == 1:  # Add leaf command
                self.scope[variable] = right_min
                right_suffix = eval_line_of_code(
                    body_list[0], self.scope)
            else:  # Add leaf function
                right_branch_path = get_subfunction_path(
                    path, f'{name}_{right_min}_{right_max}')
                right_suffix = (
                    f'function {get_function_name(right_branch_path)}')
                self.scope[variable] = right_min
                yield from CommandsWalker(
                    right_branch_path, body_list,
                    self.scope, is_root_file=False
                ).walk_function()


            if is_root_block:
                parent_function_text.append(f'{left_prefix}{left_suffix}')
                parent_function_text.append(f'{right_prefix}{right_suffix}')
            else:
                body = [
                    f'{left_prefix}{left_suffix}',
                    f'{right_prefix}{right_suffix}']
                yield McfuncitonFile(branch_path, body, is_root_block=False)


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
            if func_file.is_root_block:
                print(f"Modified function: {get_function_name(func_file.path)}")
