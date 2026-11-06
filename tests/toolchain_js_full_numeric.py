"""Numerically verify all six JS codegen formulas not covered by native CI.

Combined with toolchain_ci_smoke.py's 27 JavaScript IDs, these six cases
exercise all 33 registered formulas at least once in the Node.js runtime.
This is NOT a full input/range proof or a 462-language numeric certification.
"""
from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hyuncalculator.codegen import GenerationOptions, generate
from hyuncalculator.codegen.registry import catalog
from toolchain_ci_smoke import selected_cases
from hyuncalculator.quant import (
    normal_probabilities, covariance_correlation, bond_metrics, risk_metrics,
    ewma_volatility, backtest_single_asset,
)


DATA = [
    [0.05, 0.10, 0.08], [0.10, 0.02, 0.07],
    [-0.05, 0.03, 0.01], [0.02, -0.04, 0.06],
]
RETURNS = [0.05, -0.02, 0.01, -0.03, 0.04, 0.015]
BACKTEST_RETURNS = [0.02, -0.01, 0.03, 0.01, -0.02, 0.04]
SIGNALS = [1, 1, -1, 0, 0.5, 0]


def flatten_result(dictionary):
    out = []
    for value in dictionary.values():
        out.extend(float(x) for x in np.asarray(value, dtype=float).ravel())
    return out


CASES = (
    ('STAT-001', 'normal', 'normal(100,100,20,0.95)',
     flatten_result(normal_probabilities(100, 100, 20, 0.95)), 2e-7),
    ('STAT-002', 'cov', 'cov(' + json.dumps(DATA) + ')',
     flatten_result(covariance_correlation(DATA)), 1e-9),
    ('BOND-001', 'bond', 'bond(1000,0.05,0.04,5,2)',
     flatten_result(bond_metrics(1000, 0.05, 0.04, 5, 2)), 1e-9),
    ('RISK-003', 'performance',
     'performance(' + json.dumps(RETURNS) + ',0.001,252)',
     flatten_result(risk_metrics(RETURNS, 0.001, 252)), 1e-8),
    ('TS-001', 'ewma', 'ewma([0.02,-0.01,0.03,0.015,-0.04],0.94)',
     flatten_result(ewma_volatility([.02, -.01, .03, .015, -.04], .94)), 1e-9),
    ('STRAT-002', 'backtest',
     'backtest(' + json.dumps(BACKTEST_RETURNS) + ',' + json.dumps(SIGNALS)
     + ',3,2,0.0001,252)',
     flatten_result(backtest_single_asset(BACKTEST_RETURNS, SIGNALS, 3, 2,
                                           0.0001, 252)), 1e-8),
)

INVALID = (
    ('STAT-001', 'normal(100,100,0,0.95)'),
    ('STAT-002', 'cov([[1,2],[3,4]])'),
    ('STRAT-002', 'backtest([0.01,0.02,0.03],[1,0],3,2,0.001,252)'),
)


def execute(code, javascript):
    with tempfile.TemporaryDirectory(prefix='hyuncalc_js_numeric_') as directory:
        path = Path(directory) / 'driver.mjs'
        path.write_text(code + '\n' + javascript + '\n', encoding='utf-8')
        result = subprocess.run(['node', str(path)], cwd=directory,
                                capture_output=True, text=True,
                                timeout=30, check=False)
        if result.returncode:
            raise AssertionError('Node.js execution failed: '
                                 + result.stderr[-2500:])
        marked = [line[len('HYUN_NUMERIC '):] for line in result.stdout.splitlines()
                  if line.startswith('HYUN_NUMERIC ')]
        if len(marked) != 1:
            raise AssertionError(f'Unexpected Node output: {result.stdout[-1000:]}')
        return json.loads(marked[0])


def check_numeric(formula_id, fn, call, expected, tolerance):
    source = generate(formula_id, GenerationOptions(language='JavaScript'))
    found = execute(source, "console.log('HYUN_NUMERIC '+JSON.stringify(" + call + '));')
    if not isinstance(found, list) or len(found) != len(expected):
        raise AssertionError(f'{formula_id}: length {len(found) if isinstance(found,list) else None}'
                             f' != {len(expected)}')
    for index, (a, b) in enumerate(zip(found, expected)):
        if a is None or not math.isfinite(float(a)) or not math.isfinite(b):
            raise AssertionError(f'{formula_id}[{index}]: non-finite {a} vs {b}')
        if not math.isclose(float(a), b, rel_tol=tolerance, abs_tol=tolerance):
            raise AssertionError(f'{formula_id}[{index}]: got {a} != {b}')
    return len(found)


def check_invalid(formula_id, call):
    source = generate(formula_id, GenerationOptions(language='JavaScript'))
    script = ("let result = 'FAILED_TO_REJECT'; try { " + call
              + "; } catch (e) { if (e instanceof RangeError) result='REJECTED'; "
              + "else result='WRONG_ERROR'; } "
              + "console.log('HYUN_NUMERIC '+JSON.stringify(result));")
    actual = execute(source, script)
    if actual != 'REJECTED':
        raise AssertionError(f'{formula_id} did not throw RangeError: {actual}')


def main():
    if not shutil.which('node'):
        raise RuntimeError('Required Node.js runtime missing; no silent skip')
    # Ensure combined native/JS numerical test IDs cover the entire catalog.
    common = [name for name, _ in selected_cases()]
    remaining = [entry[0] for entry in CASES]
    all_ids = common + remaining
    registered = {formula.id for formula in catalog()}
    if (len(common) != 27 or len(remaining) != 6 or
            len(all_ids) != 33 or len(set(all_ids)) != 33 or
            set(all_ids) != registered):
        raise AssertionError('Numerical smoke catalog is incomplete, duplicated or stale')
    numeric = 0
    rejects = 0
    fail = []
    for formula_id, fn, call, expected, tol in CASES:
        try:
            n = check_numeric(formula_id, fn, call, expected, tol)
            numeric += 1
            print(f'PASS JS numerical {formula_id} ({n} output fields)', flush=True)
        except Exception as exc:
            fail.append((formula_id, str(exc)))
            print(f'FAIL JS numerical {formula_id}: {exc}', flush=True)
    for formula_id, call in INVALID:
        try:
            check_invalid(formula_id, call)
            rejects += 1
            print(f'PASS JS rejection {formula_id}', flush=True)
        except Exception as exc:
            fail.append((formula_id + '/invalid', str(exc)))
            print(f'FAIL JS rejection {formula_id}: {exc}', flush=True)
    print(f'JS REMAINING NUMERIC SUMMARY: {numeric} numerical PASS; '
          f'{rejects} rejection PASS; {len(fail)} FAIL; '
          f'{len(CASES) + len(INVALID)} planned cases', flush=True)
    if fail:
        raise SystemExit(1)
    return numeric + rejects


if __name__ == '__main__':
    main()