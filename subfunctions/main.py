from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, NamedTuple, TypeVar
import re
import json
import sys
from copy import deepcopy
from safe_eval import SafeEvalException, safe_eval
from enum import Enum, auto

FUNCTIONS_PATH = Path('BP/functions')
RP_TEXTS_PATH = Path('RP/texts')
BP_TEXTS_PATH = Path('BP/texts')

NAME_P = "[a-zA-Z_0-9]+"
FUNCTION_NAME_P = f"{NAME_P}(?:/{NAME_P})*"
INT_P = "-?[0-9]+"
EXPR_P = '[\'\\[\\]"%><,}{\\.!=a-zA-Z_0-9+\\-/*+ :()]+'
JUST_DEFINE = re.compile(f"definefunction <({FUNCTION_NAME_P})>:")
SUBFUNCTION = re.compile(f"(.* )?function <({FUNCTION_NAME_P})>:")
FUNCTION_TREE = re.compile(
    f"functiontree <({NAME_P})><({NAME_P}) +({INT_P})\.\.({INT_P})(?: +({INT_P}))?>:")
FOR = re.compile(f"for <({NAME_P}) +({INT_P})\.\.({INT_P})(?: +({INT_P}))?>:")
UNPACK_HERE = re.compile("UNPACK:HERE")
UNPACK_SUBFUNCTION = re.compile("UNPACK:SUBFUNCTION")
VAR = re.compile(f"var +({NAME_P}) *= *({EXPR_P})")
NO_VAR = re.compile(f"> +({EXPR_P})")
ASSERT = re.compile(f"assert +({EXPR_P})")
IF = re.compile(f"if <({EXPR_P})>:")
FOREACH = re.compile(f"foreach <({NAME_P}) +({NAME_P}) +({EXPR_P})>:")
EVAL = re.compile(f"`eval: *({EXPR_P}) *`")

T = TypeVar("T")

class SubfunctionAssertionException(Exception):
    def __init__(self, errors: List[str]=None):
        self.errors = [] if errors is None else errors
    
    def __str__(self):
        return "\n".join(self.errors)

class UnpackMode(Enum):
    NONE = auto()
    SUBFUNCTION = auto()
    HERE = auto()

class McfuncitonFile(NamedTuple):
    '''
    A function file data to save.

    :param path: a path to the file
    :param body: a body of the function as a list of strings
    :param is_root_block: whether this function is based on a root code block
        of root CommandWalker
    :param is_modified: whether thif function was modified in relation to the
        original block it was based on.
    :param delete_file: if true, the file should be deleted
    '''
    path: Path
    body: List[str]
    is_root_block: bool=False
    is_modified: bool=True
    delete_file: bool=False

def print_red(text):
    for t in text.split('\n'):
        print("\033[91m {}\033[00m".format(t))

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

def line_error_message(line, start, stop, max_len=50):
    '''
    
    '''
    start, stop = sorted((start, stop))
    max_len = min(len(line), max_len)
    start = max(0, start)
    stop = min(len(line), stop)
    if stop-start >= max_len:
        up = line[start:start+max_len]
        down = "^"*max_len
    elif stop-max_len-1 >= 0:
        up = line[stop-max_len:stop]
        down = " "*(stop-1-max_len) + "^"*(stop-start)
    else:
        up = line[0:max_len]
        down = " "*start + "^"*(stop-start)+" "*(max_len-stop)
    return up, down

def eval_line_of_code(line: str, scope: Dict[str, int]) -> Tuple[str, bool]:
    cursor = 0
    replace = []
    while cursor < len(line) and (match := EVAL.search(line[cursor:])):
        start, end = cursor+match.start(), cursor+match.end()
        try:
            replace.append((start, end, str(safe_eval(match[1], scope)))) 
        except SafeEvalException as e:
            u, d = line_error_message(line, start, end, max_len=50)
            raise SafeEvalException(e.errors + [u, d])
        cursor = end
    if len(replace) > 0:
        result_list = []
        prev_end = 0
        for r in replace:
            result_list.append(line[prev_end:r[0]])  # prefix
            result_list.append(r[2])  # value
            prev_end = r[1]
        # Last item (python's variable scope is weeeird :O, but awesome)
        result_list.append(line[r[1]:])  # sufix
        return "".join(result_list), True
    return line, False

class SubfunctionError(Exception):
    def __init__(self, errors: List[str]=None):
        self.errors = [] if errors is None else errors

    def __str__(self):
        return "\n".join(self.errors)

class SubfunctionSyntaxError(SubfunctionError):
    pass

class FinalCommandsWalkerError(Exception):
    def __init__(
            self, root_path: Path,
            cursor: Optional[int]=None, errors: List[str]=None):
        if cursor is None:
            first_err = (
                'An error has occured while processing '
                f'{root_path.as_posix()}" file')
        else:
            first_err = (
                'An error has occured while processing '
                f'"{root_path.as_posix()}" file, at line {cursor}.')
        self.errors = [
            first_err
        ] + errors

    def __str__(self) -> str:
        return "\n".join(self.errors)

class CommandsWalker:
    def __init__(
            self, path: Path, source_func_text: List[str],
            scope: Optional[Dict[str,int]]=None, is_root=True,
            cursor_offset=0, root_path: Optional[Path]=None,
            new_scope=True, is_mcfunction=True):
        '''
        :param path: path of the output file
        :param source_func_text: the list with lines of code from the root file.
        :param scope: the scope that provides variables that can be used by
            in evaluated parts of code
        :is_root: whether this CommandWalker walks through the root code block
            of a source mcfunction file (not subfunction)
        :cursor_offset: the offset  of the cursor for nested CommandWalkers
            used in combination wiht 'cursor' to tell which line is
            being proccessed at given moment
        :root_path: a pth of the source file used for printing errors
        :new_scope: whether the scope should be copied for this CommandsWalker
        :is_mcfunction: whether the file is an .mcfunction file.
        '''
        self.cursor = 0
        self.cursor_offset=cursor_offset
        self.path = path
        self.root_path = path if root_path is None else root_path 
        self.source_func_text = source_func_text
        self._scope = {} if scope is None else scope
        self._scope_copied = not new_scope
        self.is_root = is_root
        self.is_mcfunction = is_mcfunction

    @property
    def scope(self):  # First use of scope triggers deepcopy; no reassignment
        if not self._scope_copied:
            # copy makes sure that the variables from different mcfunction
            # files won't leak to each other
            self._scope = deepcopy(self._scope)
            self._scope_copied = True
        return self._scope

    def walk_function(
            self,
            parent_unpack_mode: Optional[UnpackMode]=None
            ) -> Iterator[McfuncitonFile]:
        '''
        Walks the commands of a function and looks for custom subfunction
        syntax. Yields new files to create.

        :param path: path to the root file.
        '''
        try:
            yield from self._walk_function(
                self.path, parent_unpack_mode=parent_unpack_mode)
        except (
                SafeEvalException, SubfunctionSyntaxError,
                SubfunctionAssertionException) as e:
            raise FinalCommandsWalkerError(
                root_path=self.root_path,
                cursor=self.cursor+self.cursor_offset+1,
                errors=e.errors)
        except FinalCommandsWalkerError as e:
            raise e
        except SubfunctionError as e:
            raise FinalCommandsWalkerError(
                root_path=self.root_path,
                errors=e.errors)
        except Exception as e:
            raise FinalCommandsWalkerError(
                root_path=self.root_path,
                cursor=self.cursor+self.cursor_offset+1,
                errors=["An unexpected error occured", str(e)])

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
            while self.cursor < len(self.source_func_text):
                line, indent = strip_line(self.source_func_text[self.cursor])
                yield line, indent, 0
                self.cursor += 1
        else:
            # Skip empty lines
            while self.cursor < len(self.source_func_text):
                first_line, first_indent = strip_line(
                    self.source_func_text[self.cursor])
                if first_line != "":
                    break
                yield first_line, first_indent, first_indent
                self.cursor += 1
            # empty subfunction
            if first_indent <= zero_indent:
                return
            # not empty subfunction
            while self.cursor < len(self.source_func_text):
                no_indent_line, indent = strip_line(
                    self.source_func_text[self.cursor])

                # Empty lines can have any indent
                if indent < first_indent and no_indent_line != "":
                    break    # The end of subfunction reached

                yield no_indent_line, indent, first_indent
                self.cursor += 1

    def _walk_function(
            self, path: Path, zero_indent=0,
            is_root_block=True, parent_unpack_mode: Optional[UnpackMode]=None
            ) -> Iterator[McfuncitonFile]:
        if not is_root_block and path.exists():
            if self.is_mcfunction:
                raise SubfunctionError([
                    f"The function file \"{get_function_name(path)}\" can't be "
                    "created because it already exists!"])
            raise SubfunctionError([
                f"The file \"{path.as_posix()}\" can't be created because it "
                "already exists!"])
        new_func_text = []
        modified = not is_root_block  # new file is considered to be modified

        unpack_mode = parent_unpack_mode or UnpackMode.NONE
        for no_indent_line, indent, base_indent in self.walk_code_block(
                zero_indent, is_root_block):
                
            # blank line or comment
            if no_indent_line.startswith("#") or no_indent_line == "":
                # Skip double comments (subfunction comments) in mcfunction
                # files
                if not no_indent_line.startswith("##") or not self.is_mcfunction:
                    new_func_text.append(
                        " "*(indent-base_indent) +  # Python goes "b"+"r"*10
                        no_indent_line)
                continue
            # Evaluate eval expressions in this line
            no_indent_line, line_modified = eval_line_of_code(
                no_indent_line, self.scope)
            modified = modified or line_modified

            if (  # JUST_DEFINE
                    (match := JUST_DEFINE.fullmatch(no_indent_line)) and
                    self.is_mcfunction):
                self.cursor += 1
                if unpack_mode == UnpackMode.HERE:
                    subfunction_path = get_subfunction_path(
                        path.parent, match[1])
                else:  # NONE or SUBFUNCTION
                    subfunction_path = get_subfunction_path(path, match[1])
                yield from self._walk_function(
                    subfunction_path, zero_indent=indent, is_root_block=False)
                self.cursor -= 1
                modified = True
            elif (  # SUBFUNCTION
                    (match := SUBFUNCTION.fullmatch(no_indent_line)) and
                    self.is_mcfunction):
                if unpack_mode in (UnpackMode.SUBFUNCTION, UnpackMode.HERE):
                    raise SubfunctionSyntaxError([
                        "Using 'function' keyword is not allowed in "
                        "functions using UNPACK:HERE or UNPACK:SUBFUNCTION!"])
                subfunction_name = f'{get_function_name(path)}/{match[2]}'
                prefix = "" if match[1] is None else match[1]
                new_func_text.append(f"{prefix}function {subfunction_name}")
                self.cursor += 1
                yield from self._walk_function(
                    get_subfunction_path(path, match[2]),
                    zero_indent=indent, is_root_block=False)
                self.cursor -= 1
                modified = True
            elif (  # FUNCTION_TREE
                    (match := FUNCTION_TREE.fullmatch(no_indent_line)) and
                    self.is_mcfunction):
                if unpack_mode in (UnpackMode.SUBFUNCTION, UnpackMode.HERE):
                    raise SubfunctionSyntaxError([
                        "Using 'functiontree' keyword is not allowed in "
                        "functions using UNPACK:HERE or UNPACK:SUBFUNCTION!"])
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
            elif match := FOR.fullmatch(no_indent_line):
                m_var = match[1]
                m_min = int(match[2])
                m_max = int(match[3])
                m_step = 1 if match[4] is None else int(match[4])
                self.cursor += 1
                yield from self.create_for(
                    path, m_var, m_min, m_max, m_step, zero_indent,
                    new_func_text, unpack_mode)
                modified = True
                self.cursor -= 1
            elif match := FOREACH.fullmatch(no_indent_line):
                m_index = match[1]
                m_var = match[2]
                try:
                    m_itrerable = safe_eval(match[3], self.scope)
                except SafeEvalException as e:
                    start, stop = match.regs[3]
                    u, d = line_error_message(
                        no_indent_line, start, stop, max_len=50)
                    raise SafeEvalException(e.errors + [u, d])
                self.cursor += 1
                yield from self.create_foreach(
                    path, m_index, m_var, m_itrerable, zero_indent,
                    new_func_text, unpack_mode)
                modified = True
                self.cursor -= 1
            elif match := IF.fullmatch(no_indent_line):
                try:
                    m_condition = bool(safe_eval(match[1], self.scope))
                except SafeEvalException as e:
                    start, stop = match.regs[1]
                    u, d = line_error_message(
                        no_indent_line, start, stop, max_len=50)
                    raise SafeEvalException(e.errors + [u, d])
                self.cursor += 1
                yield from self.create_if(
                    path, m_condition, zero_indent,
                    new_func_text, unpack_mode)
                modified = True
                self.cursor -= 1
            elif match := VAR.fullmatch(no_indent_line):
                m_name = match[1]
                m_expr = match[2]
                try:
                    self.scope[m_name] = safe_eval(m_expr, self.scope)
                except SafeEvalException as e:
                    u, d = line_error_message(
                        no_indent_line, 0, len(no_indent_line), max_len=50)
                    raise SafeEvalException(e.errors + [u, d])
                modified = True
            elif match := NO_VAR.fullmatch(no_indent_line):
                m_expr = match[1]
                try:
                    safe_eval(m_expr, self.scope)
                except SafeEvalException as e:
                    u, d = line_error_message(
                        no_indent_line, 0, len(no_indent_line), max_len=50)
                    raise SafeEvalException(e.errors + [u, d])
                modified = True
            elif match := ASSERT.fullmatch(no_indent_line):
                m_expr = match[1]
                try:
                    if not safe_eval(m_expr, self.scope):
                        u, d = line_error_message(  # 7 = len("assert ")
                            no_indent_line, 7, len(no_indent_line), max_len=50)
                        raise SubfunctionAssertionException(["Assertion failed:", u, d])
                except SafeEvalException as e:
                    u, d = line_error_message(
                        no_indent_line, 0, len(no_indent_line), max_len=50)
                    raise SafeEvalException(e.errors + [u, d])
                modified = True
            elif (  # UNPACK_HERE
                    (match := UNPACK_HERE.fullmatch(no_indent_line)) and
                    self.is_mcfunction):
                if not (self.cursor + self.cursor_offset == 0):  # first line?
                    raise SubfunctionSyntaxError([
                        "'UNPACK:HERE' can be used only at the "
                        "first line of code of a function!"])
                # Replace the path with a path of a fake file to change the
                # target directory of the defined functions
                self.path = self.path.parent.with_suffix(".mcfunction")
                unpack_mode = UnpackMode.HERE
            elif (  # UNPACK_SUBFUNCTION
                    (match := UNPACK_SUBFUNCTION.fullmatch(no_indent_line)) and
                    self.is_mcfunction):
                if not (self.cursor + self.cursor_offset == 0):  # first line?
                    raise SubfunctionSyntaxError([
                        "'UNPACK:SUBFUNCTION' can be used only at the "
                        "first line of code of a function!"])
                unpack_mode = UnpackMode.SUBFUNCTION
            else:  # normal line
                if unpack_mode in (UnpackMode.SUBFUNCTION, UnpackMode.HERE):
                    raise SubfunctionSyntaxError([
                        "Every command must be closed inside 'definefunction'"
                        " block when using UNPACK:HERE or UNPACK:SUBFUNCTION!"])
                new_func_text.append(
                    " "*(indent-base_indent) +  # Python goes "b"+"r"*10
                    no_indent_line)
        delete_file = (
            self.is_root and
            unpack_mode in (UnpackMode.SUBFUNCTION, UnpackMode.HERE))
        yield McfuncitonFile(
            path, new_func_text,
            is_root_block=is_root_block and self.is_root,
            is_modified=modified, delete_file=delete_file)

    def create_for(
            self, path: Path, variable: str, min_: int, max_: int,
            step: int, zero_indent: int, parent_function_text: List[str],
            parent_unpack_mode: UnpackMode) -> Iterator[McfuncitonFile]:
        '''
        Yields the functions from for loop.
        '''
        block_text: List[str] = []
        cursor_offset = self.cursor + self.cursor_offset
        for no_indent_line, indent, base_indent in self.walk_code_block(
                zero_indent, False):
            block_text.append(" "*(indent-base_indent) + no_indent_line)
        if len(block_text) == 0:
            raise SubfunctionSyntaxError([
                f'Missing body of the for code block of '
                f'"{get_function_name(path)}" function'])
        for i in range(min_, max_, step):
            self.scope[variable] = i
            for function in CommandsWalker(
                    path, source_func_text=block_text,
                    scope=self.scope, cursor_offset=cursor_offset,
                    root_path=self.root_path, new_scope=False
                    ).walk_function(parent_unpack_mode):
                if function.is_root_block:  # Apped this to real root function
                    parent_function_text.extend(function.body)
                else:  # yield subfunction
                    yield function

    def create_foreach(
            self, path: Path, index: str, variable: str, iterable: Iterable,
            zero_indent: int, parent_function_text: List[str],
            parent_unpack_mode: UnpackMode) -> Iterator[McfuncitonFile]:
        '''
        Yields the functions from for loop.
        '''
        block_text: List[str] = []
        cursor_offset = self.cursor + self.cursor_offset
        for no_indent_line, indent, base_indent in self.walk_code_block(
                zero_indent, False):
            block_text.append(" "*(indent-base_indent) + no_indent_line)
        if len(block_text) == 0:
            raise SubfunctionSyntaxError([
                f'Missing body of the foreach code block of '
                f'"{get_function_name(path)}" function'])
        for i, item in enumerate(iterable):
            self.scope[variable] = item
            self.scope[index] = i
            for function in CommandsWalker(
                    path, source_func_text=block_text,
                    scope=self.scope, cursor_offset=cursor_offset,
                    root_path=self.root_path, new_scope=False
                    ).walk_function(parent_unpack_mode):
                if function.is_root_block:  # Apped this to real root function
                    parent_function_text.extend(function.body)
                else:  # yield subfunction
                    yield function

    def create_if(
            self, path: Path, condition: bool, zero_indent: int,
            parent_function_text: List[str],
            parent_unpack_mode: UnpackMode) -> Iterator[McfuncitonFile]:
        '''
        Yields the functions from the if block if its condition is true.
        '''
        eval_condition = condition
        block_text: List[str] = []
        cursor_offset = self.cursor + self.cursor_offset
        for no_indent_line, indent, base_indent in self.walk_code_block(
                zero_indent, False):
            block_text.append(" "*(indent-base_indent) + no_indent_line)
        if len(block_text) == 0:
            raise SubfunctionSyntaxError([
                f'Missing body of the if code block of '
                f'"{get_function_name(path)}" function'])
        if eval_condition:
            for function in CommandsWalker(
                    path, source_func_text=block_text,
                    scope=self.scope, cursor_offset=cursor_offset,
                    root_path=self.root_path, new_scope=False
                    ).walk_function(parent_unpack_mode):
                if function.is_root_block:  # Apped this to real root function
                    parent_function_text.extend(function.body)
                else:  # yield subfunction
                    yield function

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
        cursor_offset = self.cursor + self.cursor_offset
        body_list: List[str] = []
        leaf_values: List[int] = [i for i in range(min_, max_, step)]

        for no_indent_line, indent, base_indent in self.walk_code_block(
                zero_indent, False):
            body_list.append(" "*(indent-base_indent) + no_indent_line)
        if len(body_list) == 0:
            raise SubfunctionSyntaxError([
                f'Missing body for function tree code block "{name}" of '
                f'"{get_function_name(path)}" function'])
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
                left_suffix, _ = eval_line_of_code(body_list[0], self.scope)
            else:  # Add leaf function
                left_branch_path = get_subfunction_path(
                    path, f'{name}_{left_min}_{left_max}')
                left_suffix = (
                    f'function {get_function_name(left_branch_path)}')
                self.scope[variable] = left_min
                yield from CommandsWalker(
                    left_branch_path, body_list,
                    self.scope, is_root=False, cursor_offset=cursor_offset,
                    root_path=self.root_path, new_scope=False
                ).walk_function()

            # Right branch half
            if right_min != right_max:
                right_branch_path = get_subfunction_path(
                    path, f'{name}_{right_min}_{right_max}')
                right_suffix = (
                    f'function {get_function_name(right_branch_path)}')
            elif len(body_list) == 1:  # Add leaf command
                self.scope[variable] = right_min
                right_suffix, _ = eval_line_of_code(body_list[0], self.scope)
            else:  # Add leaf function
                right_branch_path = get_subfunction_path(
                    path, f'{name}_{right_min}_{right_max}')
                right_suffix = (
                    f'function {get_function_name(right_branch_path)}')
                self.scope[variable] = right_min
                yield from CommandsWalker(
                    right_branch_path, body_list,
                    self.scope, is_root=False, cursor_offset=cursor_offset,
                    root_path=self.root_path, new_scope=False
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
    try:
        config = json.loads(sys.argv[1])
    except Exception:
        config = {}
    # Add scope
    scope = {'true': True, 'false': False}
    scope_path = Path('data') / config.get(
        'scope_path', 'subfunctions/scope.json')
    try:
        with scope_path.open('r') as f:
            scope = scope | json.load(f)
    except:
        print_red(
            f"Unable to read scope from {scope_path.as_posix()}. "
            "Replaced with default scope. "
            "You can set it in config.json file in the filter settings in "
            "'scope_path' property.")
    edit_lang_files = config.get('edit_lang_files', False)
    
    # glob pattern result changed to list to avoid going over newly created
    # files
    walk_files = list(FUNCTIONS_PATH.glob("**/*.mcfunction"))
    if edit_lang_files:
        walk_files += list(RP_TEXTS_PATH.glob("*.lang"))
        walk_files += list(BP_TEXTS_PATH.glob("*.lang"))
    for path in walk_files:
        if path.is_dir():
            continue
        with path.open('r') as f:
            func_text = f.readlines()

        try:
            is_mcfunction=path.suffix == '.mcfunction'
            for func_file in CommandsWalker(
                    path, func_text, scope=scope,
                    is_mcfunction=is_mcfunction
                    ).walk_function():
                if func_file.delete_file:  # The file should be deleted if exists
                    func_file.path.unlink(missing_ok=True)
                    print(f"Deleted function: {get_function_name(func_file.path)} and created subfunctions")
                    continue
                if not func_file.is_modified:
                    continue
                func_file.path.parent.mkdir(exist_ok=True, parents=True)
                with func_file.path.open('w') as f:
                    f.write("\n".join(func_file.body))
                if func_file.is_root_block:
                    if is_mcfunction:
                        print(f"Modified function: {get_function_name(func_file.path)}")
                    else:
                        print(f"Modified file: {func_file.path.as_posix()}")
        except FinalCommandsWalkerError as e:
            for err in e.errors:
                print_red(err)
            sys.exit(1)
