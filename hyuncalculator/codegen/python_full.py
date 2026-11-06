"""Standalone Python exporters backed by reviewed local numerical implementations.

This is a *trusted-source* exporter: it extracts named, committed function ASTs
from HyunCalculator's own finance.py/quant.py, never from an input expression.
It deliberately does not execute user-entered code.
"""
from __future__ import annotations

import ast
from pathlib import Path

from .emitter import GenerationError, _identifier

# Formula UI wrapper -> (source module, canonical numeric function, wrapper body).
# The wrapper's public parameter names come from the current operation registry.
IMPLEMENTATIONS = {
    'fin_irr': ('finance', 'irr', 'return irr(flows)'),
    'fin_loan': ('finance', 'amortization', 'return amortization(principal, rate, n, period)'),
    'qf_normal': ('quant', 'normal_probabilities', 'return normal_probabilities(x, mean, std, p)'),
    'qf_cov': ('quant', 'covariance_correlation', 'return covariance_correlation(returns)'),
    'qf_portfolio': ('quant', 'portfolio_stats', 'return portfolio_stats(w, mu, cov, rf)'),
    'qf_gmv': ('quant', 'global_minimum_variance', "weights = global_minimum_variance(cov)\nreturn {'Weights': weights, 'Portfolio variance': float(weights @ __as_array(cov) @ weights)}"),
    'qf_target': ('quant', 'minimum_variance_target', "weights = minimum_variance_target(mu, cov, target)\nreturn {'Weights': weights, 'Expected portfolio return': float(weights @ __as_array(mu))}"),
    'qf_bl': ('quant', 'black_litterman', 'return black_litterman(cov, market, delta, tau, views, np.atleast_1d(returns), np.atleast_1d(omega))'),
    'qf_bs': ('quant', 'black_scholes', 'return black_scholes(s, k, t, r, sigma, dividend=q, option=option_type)'),
    'qf_iv': ('quant', 'implied_volatility', 'return implied_volatility(price, s, k, t, r, dividend=q, option=option_type)'),
    'qf_mc': ('quant', 'european_mc', 'return european_mc(s, k, t, r, sigma, dividend=q, option=option_type, paths=paths, seed=seed)'),
    'qf_bond': ('quant', 'bond_metrics', 'return bond_metrics(face, coupon, yield_rate, years, freq)'),
    'qf_ytm': ('quant', 'yield_to_maturity', "return {'Annual nominal yield to maturity': yield_to_maturity(price, face, coupon, years, freq)}"),
    'qf_hist_var': ('quant', 'historical_var_es', 'return historical_var_es(r, confidence)'),
    'qf_normal_var': ('quant', 'normal_var_es', 'return normal_var_es(mean, sigma, confidence)'),
    'qf_performance': ('quant', 'risk_metrics', 'return risk_metrics(r, rf, ppy)'),
    'qf_ewma': ('quant', 'ewma_volatility', 'return ewma_volatility(r, decay)'),
    'qf_garch': ('quant', 'garch_forecast', 'return garch_forecast(lastvar, shock, omega, alpha, beta)'),
    'qf_moving': ('quant', 'moving_averages', 'return moving_averages(values, window)'),
    'qf_gbm': ('quant', 'gbm_moments', 'return gbm_moments(s, mu, sigma, t)'),
    'qf_ou': ('quant', 'ou_moments', 'return ou_moments(x, level, kappa, sigma, t)'),
    'qf_brownian': ('quant', 'brownian_motion', 'return brownian_motion(years, steps, paths, seed, initial, mu, sigma)'),
    'qf_gbm_paths': ('quant', 'gbm_simulation', 'return gbm_simulation(s, mu, sigma, years, steps, paths, seed)'),
    'qf_ou_paths': ('quant', 'ou_simulation', 'return ou_simulation(x, level, kappa, sigma, years, steps, paths, seed)'),
    'qf_cost': ('quant', 'transaction_cost', 'return transaction_cost(notional, commission, slippage, spread, sides)'),
    'qf_backtest': ('quant', 'backtest_single_asset', 'return backtest_single_asset(returns, signals, commission, slippage, rf, ppy)'),
}

# Formal parameter names that are reserved in Python's language grammar.
ALIASES = {'type': 'option_type', 'yield': 'yield_rate'}


def _source_package(module: str, root: str) -> tuple[str, tuple[str, ...]]:
    """Take the transitive closure of dependencies among local named functions."""
    source = (Path(__file__).resolve().parent.parent / (module + '.py')).read_text(encoding='utf-8')
    parsed = ast.parse(source)
    functions = {node.name: node for node in parsed.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    selected = {}
    def visit(name: str):
        if name in selected:
            return
        if name not in functions:
            raise GenerationError('Missing internal implementation: ' + name)
        node = functions[name]
        # Recursively include only explicitly existing call targets, not arbitrary imports.
        selected[name] = node
        for call in ast.walk(node):
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id in functions:
                visit(call.func.id)
    visit(root)
    ordered = [name for name in functions if name in selected]
    snippets = '\n\n'.join(ast.get_source_segment(source, functions[name]) for name in ordered)
    external = set()
    for name in ordered:
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Name) and node.id in ('np', 'norm', 'brentq', 'math'):
                external.add(node.id)
    imports = []
    if 'math' in external: imports.append('import math')
    if 'np' in external: imports.append('import numpy as np')
    if 'brentq' in external: imports.append('from scipy.optimize import brentq')
    if 'norm' in external: imports.append('from scipy.stats import norm')
    return ('\n'.join(imports) + '\n\n' + snippets + '\n', tuple(sorted(external)))


def generate_python(formula, options, function_name: str) -> str:
    """Create self-contained Python function or class wrapper with explicit dependencies."""
    source_name, root, wrapper = IMPLEMENTATIONS[formula.function]
    package, external = _source_package(source_name, root)
    if function_name in {node.name for node in ast.parse(package).body if isinstance(node,ast.FunctionDef)}:
        raise GenerationError('Function name shadows an internal algorithm; choose a different name')
    if options.imports == 'standard' and (set(external) & {'np', 'norm', 'brentq'}):
        raise GenerationError(f'{formula.id} requires NumPy/SciPy; choose automatic imports')
    if options.iteration != 'auto':
        raise GenerationError('Custom iteration is not yet supported for this formula')
    if options.variant != 'periodic':
        raise GenerationError('Variant is supported only for Future Value')
    originals = [p for p, _ in formula.fields]
    renamed = dict(options.variable_names)
    if len(renamed) != len(options.variable_names) or any(name not in originals for name in renamed):
        raise GenerationError('Unknown or repeated variable name')
    params = [renamed.get(name, ALIASES.get(name, name)) for name in originals]
    for p in params: _identifier(p)
    if len(params) != len(set(params)) or function_name in params or options.class_name in params:
        raise GenerationError('Duplicate/shadowed function parameter')
    if any(p in {'np','math','norm','brentq', '__as_array'} for p in params) or (options.structure=='class' and options.class_name in {'np','math','norm','brentq'}):
        raise GenerationError('Parameter shadows a required library/helper')
    # Render only *trusted* wrapper body through Python AST, rewriting canonical
    # parameters by Name node (never text replacement in strings/attributes).
    canonical = {name: params[i] for i, name in enumerate(originals)}
    # Special syntax aliases are deliberately emitted in the trusted wrapper.
    canonical['option_type'] = canonical.get('type', 'option_type')
    canonical['yield_rate'] = canonical.get('yield', 'yield_rate')
    root_wrapper = ast.parse('def _wrapper(' + ', '.join(params) + '):\n' +
                             ''.join('    ' + line + '\n' for line in wrapper.splitlines()))
    local_vars = {'weights'}
    class Rename(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id in canonical:
                return ast.copy_location(ast.Name(id=canonical[node.id], ctx=node.ctx), node)
            return node
    renamed_ast = ast.fix_missing_locations(Rename().visit(root_wrapper))
    method = renamed_ast.body[0]
    method.name = function_name
    if options.structure == 'class':
        method.decorator_list=[ast.Name(id='staticmethod',ctx=ast.Load())]
        class_node = ast.ClassDef(name=options.class_name, bases=[], keywords=[], body=[method], decorator_list=[])
        wrapper_code = ast.unparse(ast.fix_missing_locations(class_node))
    else:
        wrapper_code = ast.unparse(renamed_ast)
    if '__as_array' in wrapper:
        if 'np' not in external:
            package='import numpy as np\n\n'+package
        package+='\n\ndef __as_array(value):\n    return np.asarray(value, dtype=float)\n'
    dependency_note=('# Dependencies: pip install numpy scipy\n' if any(x in external for x in ('np','norm','brentq')) or '__as_array' in wrapper else '# Dependencies: Python standard library\n')
    return '"""HyunCalculator generated code — ' + formula.id + '.\n' + \
           'Inputs match v1.1.0 calculator numeric units. This module is standalone.\n"""\n' + \
           dependency_note + '\n' + package + '\n\n' + wrapper_code + '\n'
