import ast
import operator as op
from typing import Dict

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
    # ast.Is: op.is_,
    # ast.IsNot: op.is_not,
    # ast.In: lambda a, b: op.contains(b, a),
    # ast.NotIn: lambda a, b: not op.contains(b, a),

    # BoolOp (hardcoded)
    # class ast.And
    # class ast.Or

    # IfExp (hardcoded)
    # Subscript (hardcoded)
}

def safe_eval(expr, scope: Dict[str, int]):
    return _eval(ast.parse(expr, mode='eval').body, scope)

def _eval(node, scope: Dict[str, int]):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        try:
            return scope[node.id]
        except KeyError:
            raise NameError(f"Unknown variable '{node.id}'")
    if isinstance(node, ast.BinOp):
        return operators[type(node.op)](_eval(node.left, scope), _eval(node.right, scope))
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
    if isinstance(node, ast.Subscript):
        return _eval(node.value, scope)[_eval(node.slice, scope)]
    if isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](_eval(node.operand, scope))
    raise TypeError(node)