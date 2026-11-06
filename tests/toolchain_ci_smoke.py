"""Real native toolchain numerical smoke checks for CI: C, C++ and JavaScript.

Exercises 21 named generated formula-language pairs per native target, NOT the
complete 462-pair matrix. Missing required toolchains are an error, not a pass.
The numerical references are supplied by the existing optional smoke modules.
Run from repository root: python tests/toolchain_ci_smoke.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from toolchain_smoke import check as scalar_check
from toolchain_finance_smoke import test as finance_check
from toolchain_portfolio_smoke import check as portfolio_check
from toolchain_bs_smoke import check as bs_check, CASES as BS_CASES
from toolchain_allocation_smoke import smoke as allocation_check
from toolchain_bl_smoke import smoke as bl_check
from toolchain_series_smoke import test as series_check
from toolchain_stochastic_smoke import check_toolchain as stochastic_check
from toolchain_ytm_smoke import check as bond_yield_check, CASES as YTM_CASES
from toolchain_quant_smoke import check as quant_check, CASES as QUANT_CASES
from toolchain_iv_normal_smoke import run_one as iv_normal_check, CASES as IV_CASES
from toolchain_mc_smoke import run_one as mc_check

TOOLS = {'C': 'gcc', 'C++': 'g++', 'JavaScript': 'node'}


def run_all() -> int:
    for language, executable in TOOLS.items():
        if not shutil.which(executable):
            raise RuntimeError(f'Required CI toolchain not installed: {language} ({executable})')
    cases = (
        ('FIN-001', lambda lang: scalar_check(lang, 'FIN-001', 'fv', 1628.894626777442)),
        ('FIN-005', lambda lang: finance_check(lang, 'fin_irr')),
        ('FIN-006', lambda lang: finance_check(lang, 'fin_loan')),
        ('PORT-001', lambda lang: portfolio_check(lang)),
        ('DERIV-001', lambda lang: bs_check(lang, BS_CASES[0])),
        ('ALLOC-001', lambda lang: allocation_check('ALLOC-001', lang)),
        ('ALLOC-003', lambda lang: bl_check(lang)),
        ('RISK-001', lambda lang: series_check(lang, 'RISK-001')),
        ('TS-003', lambda lang: series_check(lang, 'TS-003')),
        ('STOCH-003', lambda lang: stochastic_check(lang, 'STOCH-003')),
        ('BOND-002', lambda lang: bond_yield_check(lang, YTM_CASES[0])),
        # Independent portable quantitative-function checks.
        ('TS-002', lambda lang: quant_check(lang, *QUANT_CASES[0])),
        ('STOCH-001', lambda lang: quant_check(lang, *QUANT_CASES[1])),
        ('STOCH-002', lambda lang: quant_check(lang, *QUANT_CASES[2])),
        ('STRAT-001', lambda lang: quant_check(lang, *QUANT_CASES[3])),
        ('DERIV-002', lambda lang: iv_normal_check(lang, IV_CASES[0][0], IV_CASES[0][1])),
        ('RISK-002', lambda lang: iv_normal_check(lang, IV_CASES[2][0], IV_CASES[2][1])),
        ('ALLOC-002', lambda lang: allocation_check('ALLOC-002', lang)),
        ('DERIV-003', lambda lang: mc_check(lang, 'call', 4000, 42)),
        ('STOCH-004', lambda lang: stochastic_check(lang, 'STOCH-004')),
        ('STOCH-005', lambda lang: stochastic_check(lang, 'STOCH-005')),
    )
    if len(cases) != 21 or len({name for name, _ in cases}) != len(cases):
        raise AssertionError('Expected 21 distinct numerical formula cases')
    checks = 0
    failures = []
    for language in TOOLS:
        for formula, task in cases:
            try:
                value = task(language)
                # The FIN-005/006 helper returns (success, message), not an
                # exception; never confuse a false status with a test pass.
                if formula in ('FIN-005', 'FIN-006'):
                    valid, detail = value
                    if not valid:
                        raise AssertionError(detail)
                checks += 1
                print('PASS', language, formula, flush=True)
            except Exception as exc:
                failures.append((language, formula, str(exc)))
                print('FAIL', language, formula, str(exc)[:2500], flush=True)
    print(f'NATIVE TOOLCHAIN SUMMARY: {checks} PASS; {len(failures)} FAIL; '
          f'{len(TOOLS) * len(cases)} planned cases across {len(TOOLS)} languages', flush=True)
    if failures:
        raise SystemExit(1)
    return checks


if __name__ == '__main__':
    run_all()
