"""Safe numeric-expression engine shared by scientific and graph calculators.

Expressions are AST interpreted, never evaluated with Python eval/exec.
"""
from __future__ import annotations

import ast
import math
import operator
import re
from typing import Any

import numpy as np


def _factorial(x):
    if int(x) != x or x < 0 or x > 1000:
        raise ValueError('factorial requires an integer from 0 to 1000')
    return math.factorial(int(x))


def _comb(n, k):
    return math.comb(int(n), int(k))


def _perm(n, k):
    return math.perm(int(n), int(k))


def _root(x, n):
    if n == 0:
        raise ValueError('Root degree must be nonzero')
    if np.isscalar(x) and x < 0 and int(n) % 2 == 1:
        return -abs(x) ** (1 / n)
    return np.power(x, 1 / n)


def _round(x, digits=0):
    if np.ndim(x):
        return np.round(x, int(digits))
    return round(x, int(digits))


BASE_FUNCTIONS = {
    'sqrt': np.sqrt, 'cbrt': np.cbrt, 'root': _root,
    'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
    'asin': np.arcsin, 'acos': np.arccos, 'atan': np.arctan,
    'sinh': np.sinh, 'cosh': np.cosh, 'tanh': np.tanh,
    'ln': np.log, 'log': np.log10, 'log10': np.log10,
    'log2': np.log2, 'exp': np.exp, 'abs': np.abs,
    'floor': np.floor, 'ceil': np.ceil, 'round': _round,
    'factorial': _factorial, 'comb': _comb, 'perm': _perm,
    'gcd': math.gcd, 'lcm': math.lcm, 'hypot': np.hypot,
    'degrees': np.degrees, 'radians': np.radians,
    'min': np.minimum, 'max': np.maximum,
}

OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub,
             ast.Mult: operator.mul, ast.Div: operator.truediv,
             ast.Pow: operator.pow, ast.Mod: operator.mod,
             ast.FloorDiv: operator.floordiv}
UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def calculate(expression: str, *, degrees: bool = False, variables: dict[str, Any] | None = None):
    """Evaluate a scalar/NumPy expression with a deliberately tiny AST whitelist.

    ^ is treated as exponentiation, not XOR (XOR is in Programmer mode).
    Valid constants: pi, e, tau, Ans (provided by GUI); x in graph mode.
    """
    expression = expression.strip().replace('π', 'pi').replace('×', '*').replace('÷', '/')
    expression = expression.replace('^', '**').replace('−', '-')
    if not expression or len(expression) > 1200:
        raise ValueError('Expression must be between 1 and 1200 characters')
    try:
        tree = ast.parse(expression, mode='eval')
    except (SyntaxError, ValueError) as exc:
        raise ValueError('Invalid expression syntax') from exc
    if sum(1 for _ in ast.walk(tree)) > 120:
        raise ValueError('Expression is too complex')
    functions = BASE_FUNCTIONS.copy()
    if degrees:
        for name in ('sin', 'cos', 'tan'):
            fun = functions[name]
            functions[name] = lambda a, f=fun: f(np.deg2rad(a))
        for name in ('asin', 'acos', 'atan'):
            fun = functions[name]
            functions[name] = lambda a, f=fun: np.rad2deg(f(a))
    env = {'pi': math.pi, 'e': math.e, 'tau': math.tau}
    if variables:
        for k, v in variables.items():
            if k in functions or k.startswith('_') or not re.fullmatch(r'[A-Za-z][A-Za-z_0-9]*', k):
                raise ValueError('Invalid variable name')
            env[k] = v

    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float, complex):
            if isinstance(node.value, int) and node.value.bit_length() > 1024:
                raise ValueError('Integer is too large')
            return node.value
        if isinstance(node, ast.Name) and node.id in env:
            return env[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and np.isscalar(right) and abs(right) > 10000:
                raise ValueError('Exponent is too large')
            with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
                return OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY:
            return UNARY[type(node.op)](visit(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in functions:
            if node.keywords or len(node.args) > 3:
                raise ValueError('Only positional function arguments are allowed')
            with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
                try:
                    return functions[node.func.id](*(visit(arg) for arg in node.args))
                except (TypeError, OverflowError, ZeroDivisionError) as exc:
                    raise ValueError('Invalid function argument') from exc
        raise ValueError('Unsupported expression or identifier')

    try:
        result = visit(tree.body)
    except (ArithmeticError, OverflowError) as exc:
        raise ValueError('Expression is out of range') from exc
    if np.isscalar(result):
        if isinstance(result, complex):
            if not (math.isfinite(result.real) and math.isfinite(result.imag)):
                raise ValueError('Result is not finite')
        elif not math.isfinite(float(result)):
            raise ValueError('Result is not finite')
    return result
