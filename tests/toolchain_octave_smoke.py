"""Required Octave (MATLAB-compatible) numerical tests for emitted MATLAB source.

Selected source files are generated in temporary directories and executed with
GNU Octave, never silently skipped. Results are checked against the original
Python/Numpy/SciPy reference; this does NOT certify MATLAB proprietary runtime
or all 462 source-generation combinations.

Run: python tests/toolchain_octave_smoke.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from hyuncalculator.codegen import GenerationOptions, generate
from hyuncalculator.finance import irr
from hyuncalculator.quant import (black_scholes, normal_probabilities,
                                  normal_var_es, yield_to_maturity)
from toolchain_r_csharp_smoke import cases, verify_output


ARGUMENTS = {
    'FIN-001': '1000,0.05,10',
    'FIN-006': '120000,0.005,24,12',
    'RISK-002': '0.001,0.02,0.95',
    'STAT-001': '1.5,0.2,1.1,0.95',
    'RISK-003': '[0.01;-0.02;0.03;0.015;-0.005],0.0001,252',
    'BOND-002': '1044.912925031211,1000,0.05,5,2',
    'FIN-005': '[-100;60;60]',
    'DERIV-001': "100,105,1,0.03,0.2,0,'call'",
    'STAT-002': '[0.01,0.02;0.02,0.01;-0.01,0.03;0.03,0.00]',
}


def all_cases():
    records = [(formula, function, expected) for formula, function, _ra, _cs, expected in cases()]
    records.extend([
        ('FIN-005', 'calculate_irr', [float(irr([-100., 60., 60.]))]),
        ('DERIV-001', 'bs', list(black_scholes(100, 105, 1, .03, .2,
                                            dividend=0, option='call').values())),
    ])
    matrix = np.array([[.01, .02], [.02, .01], [-.01, .03], [.03, .00]])
    covariance = np.cov(matrix, rowvar=False, ddof=1)
    correlation = np.corrcoef(matrix, rowvar=False)
    records.append(('STAT-002', 'cov', list(covariance.ravel(order='C')) +
                    list(correlation.ravel(order='C'))))
    assert set(ARGUMENTS) == {formula for formula, _, _ in records}
    return records


def octave_executable():
    exe = shutil.which('octave-cli') or shutil.which('octave')
    if exe is None:
        raise RuntimeError('GNU Octave interpreter required; cannot skip MATLAB-compatible checks')
    return exe


def check(exe: str, formula: str, function: str, expected: list[float],
          *, args: str | None = None):
    with TemporaryDirectory(prefix='hyuncalc_octave_') as tmp:
        root = Path(tmp)
        source_dir = root / 'source'
        source_dir.mkdir()
        (source_dir / f'{function}.m').write_text(
            generate(formula, GenerationOptions(language='MATLAB')),
            encoding='utf-8')
        # Keep all variable paths under TemporaryDirectory: input fields are
        # fixed, not from user-supplied snippets or external downloads.
        text = ("addpath('source');\n"
                f"value = {function}({args if args is not None else ARGUMENTS[formula]});\n"
                "if ~isnumeric(value), error('Expected numeric result'); end\n"
                "fprintf('HYUN_RESULT ');\n"
                "fprintf('%.17g ', value(:));\n"
                "fprintf('\\n');\n")
        (root / 'check.m').write_text(text, encoding='utf-8')
        run = subprocess.run([exe, '--quiet', '--no-history', str(root / 'check.m')],
                             cwd=root, text=True, capture_output=True,
                             check=False, timeout=95)
        if run.returncode != 0:
            raise AssertionError(f'Octave {formula} exit {run.returncode}: '
                                 f'{run.stderr[-2400:]} {run.stdout[-600:]}')
        return verify_output(run.stdout, expected, formula, 'Octave')



def boundary_cases():
    """Independent reference values for numerical edge cases, same source ID."""
    return [
        ('FIN-006', 'loan', '1200,0,12,12', [100.0, 0.0, 100.0, 0.0]),
        ('BOND-002', 'ytm', '900,1000,0,3,2',
         [float(yield_to_maturity(900, 1000, 0, 3, 2))]),
        ('DERIV-001', 'bs', "100,105,1,0.03,0.2,0,'put'",
         list(black_scholes(100, 105, 1, .03, .2,
                            dividend=0, option='put').values())),
        ('STAT-001', 'normal', '0,0,1,0.01',
         list(normal_probabilities(0, 0, 1, 0.01).values())),
        ('RISK-002', 'normal_var', '0.002,0,0.95',
         list(normal_var_es(.002, 0, .95).values())),
    ]


def rejection_cases():
    """Wrong inputs must fail with expected formula guard, not a parse error."""
    return [
        ('FIN-005', 'calculate_irr', '[-100;230;-132]', 'Multiple IRRs'),
        ('STAT-001', 'normal', '0,0,0,0.95', 'Invalid normal inputs'),
        ('FIN-006', 'loan', '1200,-1,12,5', 'Invalid loan inputs'),
    ]


def check_rejection(exe: str, formula: str, function: str, args: str,
                    required_error: str):
    with TemporaryDirectory(prefix='hyuncalc_octave_invalid_') as tmp:
        root = Path(tmp)
        source_dir = root / 'source'
        source_dir.mkdir()
        (source_dir / f'{function}.m').write_text(
            generate(formula, GenerationOptions(language='MATLAB')),
            encoding='utf-8')
        (root / 'check.m').write_text(
            "addpath('source');\n" + f"value = {function}({args});\n" +
            "fprintf('UNEXPECTED_SUCCESS');\n", encoding='utf-8')
        run = subprocess.run([exe, '--quiet', '--no-history', str(root / 'check.m')],
                             cwd=root, text=True, capture_output=True,
                             check=False, timeout=95)
        if run.returncode == 0 or required_error not in run.stderr:
            raise AssertionError(f'{formula} must reject with {required_error}: '
                                 f'exit={run.returncode} {run.stderr[-700:]}')


def main():
    exe = octave_executable()
    passed, failures = 0, []
    records = all_cases()
    edge = boundary_cases()
    rejected = rejection_cases()
    for formula, fn, expected in records:
        try:
            got = check(exe, formula, fn, expected)
            passed += 1
            print(f'PASS Octave {formula} {got[:3]}', flush=True)
        except Exception as exc:
            failures.append((formula, str(exc)))
            print(f'FAIL Octave {formula} {exc}', flush=True)
    for formula, fn, args, expected in edge:
        try:
            got = check(exe, formula, fn, expected, args=args)
            passed += 1
            print(f'PASS Octave {formula} boundary {got[:3]}', flush=True)
        except Exception as exc:
            failures.append((formula, str(exc)))
            print(f'FAIL Octave {formula} boundary {exc}', flush=True)
    for formula, fn, args, message in rejected:
        try:
            check_rejection(exe, formula, fn, args, message)
            passed += 1
            print(f'PASS Octave {formula} invalid-input guard', flush=True)
        except Exception as exc:
            failures.append((formula, str(exc)))
            print(f'FAIL Octave {formula} invalid-input guard {exc}', flush=True)
    planned = len(records) + len(edge) + len(rejected)
    print(f'OCTAVE NATIVE NUMERIC SUMMARY: {passed} PASS; {len(failures)} FAIL; '
          f'{planned} planned cases', flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()