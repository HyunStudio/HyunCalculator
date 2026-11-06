"""Required Rust compiler smoke tests for six standalone code-generation profiles.

Runs native rustc output and compares numeric values with independent Python
math references. Not a substitute for all 33 Rust profiles or edge cases.
"""
from __future__ import annotations

import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hyuncalculator.codegen import generate, GenerationOptions


_IRR = (60 + math.sqrt(60**2 + 4*100*60))/(2*100) - 1
_LOAN_PAYMENT = 120000*.005/(1-(1+.005)**-24)
_LOAN_PREVIOUS = 120000*(1+.005)**11 - _LOAN_PAYMENT*((1+.005)**11-1)/.005
_Z = 1.6448536269514722
_NORMAL = [-.001+.02*_Z,
           -.001+.02*math.exp(-.5*_Z**2)/math.sqrt(2*math.pi)/.05]
_GBM_MEAN = 100*math.exp(.07)

CASES = (
    ('FIN-001', 'fv(1000.0,0.05,10)', [1000*1.05**10]),
    ('FIN-005', 'calculate_irr(&[-100.0,60.0,60.0])', [_IRR]),
    ('FIN-006', 'loan(120000.0,0.005,24,12)', [
        _LOAN_PAYMENT, _LOAN_PREVIOUS*.005,
        _LOAN_PAYMENT-_LOAN_PREVIOUS*.005,
        _LOAN_PREVIOUS-(_LOAN_PAYMENT-_LOAN_PREVIOUS*.005)]),
    ('RISK-002', 'normal_var(0.001,0.02,0.95)', _NORMAL),
    ('STOCH-001', 'gbm(100.0,0.07,0.2,1.0)', [
        _GBM_MEAN, _GBM_MEAN*math.sqrt(math.exp(.2*.2)-1)]),
    ('BOND-002', 'ytm(850.0,1000.0,0.0,2.0,2)', [
        2*((1000/850)**(1/4)-1)]),
)

_NUMBER = re.compile(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?|NaN|inf', re.I)


def check(formula_id, expression, expected):
    source = generate(formula_id, GenerationOptions(language='Rust'))
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        src = root / 'main.rs'
        src.write_text(source+'\nfn main() { println!("{:?}", '+expression+'); }\n', encoding='utf-8')
        command = ['rustc', '--edition=2021', '-O', str(src), '-o', str(root/'program')]
        compiled = subprocess.run(command, cwd=root, text=True, capture_output=True,
                                  timeout=60, check=False)
        if compiled.returncode:
            raise AssertionError('RUSTC: '+compiled.stderr[:3000])
        executed = subprocess.run([str(root/'program')], cwd=root, capture_output=True,
                                  text=True, timeout=10, check=False)
        if executed.returncode:
            raise AssertionError('RUST RUN: '+executed.stderr[:2500])
        actual = [float(x) for x in _NUMBER.findall(executed.stdout)]
        if len(actual) != len(expected):
            raise AssertionError(f'{formula_id}: got {actual!r}, expected {expected!r}')
        for index, (value, target) in enumerate(zip(actual, expected)):
            if not math.isclose(value, target, rel_tol=3e-7, abs_tol=3e-9):
                raise AssertionError(f'{formula_id}[{index}]: {value} vs {target}')
        return actual


def main():
    if not shutil.which('rustc'):
        raise RuntimeError('Required Rust compiler not installed: rustc')
    failed = []
    for formula_id, expression, expected in CASES:
        try:
            actual = check(formula_id, expression, expected)
            print('PASS Rust', formula_id, actual[:3], flush=True)
        except Exception as exc:
            failed.append(formula_id)
            print('FAIL Rust', formula_id, str(exc), flush=True)
    print(f'RUST NUMERIC SUMMARY: {len(CASES)-len(failed)} PASS; {len(failed)} FAIL; {len(CASES)} cases', flush=True)
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
