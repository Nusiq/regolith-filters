import ast
import operator as op
from typing import Dict

operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.FloorDiv: op.floordiv,
    ast.Invert: op.inv,
}

def safe_eval(expr, scope: Dict[str, int]):
    return _eval(ast.parse(expr, mode='eval').body, scope)

def _eval(node, scope: Dict[str, int]):
    if isinstance(node, ast.Num): # <number>
        return node.n
    if isinstance(node, ast.Name):
        try:
            return scope[node.id]
        except KeyError:
            raise NameError(f"Unknown variable '{node.id}'")
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return operators[type(node.op)](_eval(node.left, scope), _eval(node.right, scope))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](_eval(node.operand, scope))
    else:
        raise TypeError(node)