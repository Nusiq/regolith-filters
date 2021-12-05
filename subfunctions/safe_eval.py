import ast
import operator as op
import copy
from typing import Dict, List, Optional
import traceback

operators = {
    # BinOp
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.LShift: op.lshift,
    ast.RShift: op.rshift,
    ast.BitOr: op.or_,
    ast.BitXor: op.xor,
    ast.BitAnd: op.and_,
    # ast.MatMult: op.matmul,
    
    # UnrayOp
    ast.UAdd: lambda a: a,
    ast.USub: op.neg,
    ast.Not: op.not_,
    ast.Invert: op.inv,

    # Compare
    ast.Eq: op.eq,
    ast.NotEq: op.ne,
    ast.Lt: op.lt,
    ast.LtE: op.le,
    ast.Gt: op.gt,
    ast.GtE: op.ge,
    ast.Is: op.is_,
    ast.IsNot: op.is_not,
    ast.In: lambda a, b: op.contains(b, a),
    ast.NotIn: lambda a, b: not op.contains(b, a),

    # BoolOp (hardcoded)
    # class ast.And
    # class ast.Or

    # IfExp (hardcoded)
    # Subscript (hardcoded)
}

simple_collections = {
    ast.List: list,
    ast.Tuple: tuple,
    ast.Set: set
}

scope_funcs = {
    "abs": abs, # Returns the absolute value of a number
    "all": all, # Returns True if all items in an iterable object are true
    "any": any, # Returns True if any item in an iterable object is true
    "bool": bool, # Returns the boolean value of the specified object
    "complex": complex, # Returns a complex number
    "float": float, # Returns a floating point number
    "hex": hex, # Converts a number into a hexadecimal value
    "int": int, # Returns an integer number
    "len": len, # Returns the length of an object
    "max": max, # Returns the largest item in an iterable
    "min": min, # Returns the smallest item in an iterable
    "oct": oct, # Converts a number into an octal
    "pow": pow, # Returns the value of x to the power of y
    "range": range, # Returns a sequence of numbers, starting from 0 and increments by 1 (by default)
    "reversed": reversed, # Returns a reversed iterator
    "round": round, # Rounds a numbers
    "sorted": sorted, # Returns a sorted list
    "str": str, # Returns a string object
    "sum": sum, # Sums the items of an iterator
    "zip": zip, # Returns an iterator, from two or more iterators
}

f_string_format_spec = {
    # https://docs.python.org/3/library/ast.html#ast.FormattedValue
    -1: str, # lambda x: x,  # no formatting  CHANGED TO STR TO RETURN STRINGS
    115: str,  # string formatting ("!s")
    114: repr,  # repr formatting ("!r")
    97: ascii,  # ascii formatting ("!a")
}

attributes = {
    str: {
        'capitalize': str.capitalize,
        'casefold': str.casefold,
        'center': str.center,
        'count': str.count,
        'encode': str.encode,
        'endswith': str.endswith,
        'expandtabs': str.expandtabs,
        'find': str.find,
        # 'format': str.format,
        # 'format_map': str.format_map,
        'index': str.index,
        'isalnum': str.isalnum,
        'isalpha': str.isalpha,
        'isascii': str.isascii,
        'isdecimal': str.isdecimal,
        'isdigit': str.isdigit,
        'isidentifier': str.isidentifier,
        'islower': str.islower,
        'isnumeric': str.isnumeric,
        'isprintable': str.isprintable,
        'isspace': str.isspace,
        'istitle': str.istitle,
        'isupper': str.isupper,
        'join': str.join,
        'ljust': str.ljust,
        'lower': str.lower,
        'lstrip': str.lstrip,
        'maketrans': str.maketrans,
        'partition': str.partition,
        'removeprefix': str.removeprefix,
        'removesuffix': str.removesuffix,
        'replace': str.replace,
        'rfind': str.rfind,
        'rindex': str.rindex,
        'rjust': str.rjust,
        'rpartition': str.rpartition,
        'rsplit': str.rsplit,
        'rstrip': str.rstrip,
        'split': str.split,
        'splitlines': str.splitlines,
        'startswith': str.startswith,
        'strip': str.strip,
        'swapcase': str.swapcase,
        'title': str.title,
        'translate': str.translate,
        'upper': str.upper,
        'zfill': str.zfill,
    },
    list: {
        'append': list.append,
        'clear': list.clear,
        'copy': list.copy,
        'count': list.count,
        'extend': list.extend,
        'index': list.index,
        'insert': list.insert,
        'pop': list.pop,
        'remove': list.remove,
        'reverse': list.reverse,
        'sort': list.sort,
    }
}

class SafeEvalException(Exception):
    def __init__(self, errors: List[str]=None):
        self.errors = [] if errors is None else errors
    
    def __str__(self):
        return "\n".join(self.errors)

def safe_eval(expr, scope: Dict[str, int]):
    try:
        syntax_tree = ast.parse(expr, mode='eval').body
    except SyntaxError as e:
        raise SafeEvalException([
            "Expression evaluation failed due to invalid Python syntax in "
            f'following expression:', expr
        ])

    try:
        return _eval(syntax_tree, scope)
    except SafeEvalException as e:
        raise SafeEvalException(["Expression evaluation failed."] + e.errors)
    except Exception as e:
        raise SafeEvalException([
            "Expression evaluation failed.",
            f"Unexpected error occured:",
            *traceback.format_exc().split("\n")
        ])

def _eval(node, scope: Dict[str, int]):
    scope = scope_funcs | scope
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        try:
            return scope[node.id]
        except KeyError:
            raise SafeEvalException(
                [f"You tried to access unknown variable: {node.id}"])
    if isinstance(node, ast.BinOp):
        return operators[
            type(node.op)](_eval(node.left, scope), _eval(node.right, scope))
    if isinstance(node, ast.Compare):
        curr_val = _eval(node.left, scope)
        for i in range(len(node.ops)):
            next_val = _eval(node.comparators[i], scope)
            op = node.ops[i]
            if not operators[type(op)](curr_val, next_val):
                return False
            curr_val = next_val
        return True
    if isinstance(node, ast.IfExp):
        if _eval(node.test, scope):
            return _eval(node.body, scope)
        else:  # TODO - other values should be checked to see if they're in scope (but not evaluated)
            return _eval(node.orelse, scope)
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
        for val in node.values:
            eval_val = _eval(val, scope)
            if eval_val:  # TODO - other values should be checked to see if they're in scope (but not evaluated)
                return eval_val
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
        for val in node.values:
            eval_val = _eval(val, scope)
            if not eval_val:  # TODO - other values should be checked to see if they're in scope (but not evaluated)
                return eval_val
    if isinstance(node, ast.Call):
        func = _eval(node.func, scope)
        args = [_eval(arg, scope) for arg in node.args]
        kwargs = {kw.arg: _eval(kw.value, scope) for kw in node.keywords}
        return func(*args, **kwargs)
    if isinstance(node, ast.Subscript):
        return _eval(node.value, scope)[_eval(node.slice, scope)]
    if isinstance(node, ast.Slice):
        lower = None if node.lower is None else _eval(node.lower, scope)
        upper = None if node.upper is None else _eval(node.upper, scope)
        step = None if node.step is None else _eval(node.step, scope)
        return slice(lower, upper, step)
    if isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](_eval(node.operand, scope))
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return simple_collections[
            type(node)](_eval(i, scope) for i in node.elts)
    if isinstance(node, ast.Dict):
        return {
            _eval(k, scope): _eval(v, scope)
            for k, v in zip(node.keys, node.values)
        }
    if isinstance(node, ast.JoinedStr):
        parsed_values = []
        for val in node.values:
            if isinstance(val, ast.FormattedValue):
                value = val.value
                conversion = f_string_format_spec[val.conversion]
                if val.format_spec is not None:  # Disabled because of possible code injection
                    raise SafeEvalException([
                        f"f-string 'format_spec' not supported: {type(node)}"])
                parsed_values.append(conversion(_eval(value, scope)))
            elif isinstance(val, ast.Constant):
                parsed_values.append(val.value)
            else:  # Shouldn't happen
                raise SafeEvalException([
                    f"f-string expression uses an unsuported node type: "
                    f"{type(node)}"])
        return "".join(parsed_values)
    if isinstance(node, ast.ListComp):
        result = []
        for generator_scope in _yield_eval_comprehensions(
                node.generators, scope):
            result.append(_eval(node.elt, generator_scope))
        return result
    if isinstance(node, ast.SetComp):
        result = set()
        for generator_scope in _yield_eval_comprehensions(
                node.generators, scope):
            result.add(_eval(node.elt, generator_scope))
        return result
    if isinstance(node, ast.GeneratorExp):
        def result():
            for generator_scope in _yield_eval_comprehensions(
                    node.generators, scope):
                yield _eval(node.elt, generator_scope)
        return result
    if isinstance(node, ast.DictComp):
        result = {}
        for generator_scope in _yield_eval_comprehensions(
                node.generators, scope):
            result[_eval(node.key, generator_scope)] = _eval(
                node.value, generator_scope)
        return result
    if isinstance(node, ast.Attribute):  # Some hardcoded attributes
        value = _eval(node.value, scope)
        print(value)
        attr = attributes[type(value)][node.attr]
        print(attr)
        def method(*args, **kwargs):
            return attr(value, *args, **kwargs)
        return method
    raise SafeEvalException([f"Expression uses an unsuported node type: {type(node)}"])

def _yield_eval_comprehensions(
        generators: List[ast.comprehension], scope: Dict,
        generator_scope: Optional[Dict]=None):
    '''
    Yields scopes created by comprehension generators.

    :param generators: list of comprehension generators
    :param scope: base scope
    :param generator_scope: scope used only inside the generators
    '''
    if generator_scope is None:
        generator_scope = {}
    if len(generators) <= 0:
        yield generator_scope
    else:
        comprehension = generators[0]
        if comprehension.is_async:
            raise SafeEvalException([f"Async list comprehensions not "
                f"supported: {type(comprehension)}"])
        if isinstance(comprehension.target, ast.Name):
            targets: List[str] = [comprehension.target.id]
        elif isinstance(comprehension.target, ast.Tuple):
            targets = [i.id for i in comprehension.target.elts]
        else:
            raise SafeEvalException(
                [f"Unsupported list comprehension target: "
                f"{type(comprehension.target)}"])
        for item in _eval(comprehension.iter, generator_scope):
            for name in targets:
                generator_scope[name] = item
            eval_scope = scope | generator_scope
            for condition in comprehension.ifs:
                if not _eval(condition, eval_scope):
                    break  # TODO - check if all variables used in conditions are in scope
            else:  # All conditions are true
                yield from _yield_eval_comprehensions(
                    generators[1:], scope, generator_scope)
