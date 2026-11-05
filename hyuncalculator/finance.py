"""Time value of money, cash flows and loans. Annual rates are decimals."""
from __future__ import annotations

import math
import numpy as np
from scipy.optimize import brentq
from .legacy_ml import number, integer, vector


def future_value(pv: float, rate: float, periods: int, *, compounding: str = 'periodic') -> float:
    if periods < 0:
        raise ValueError('Periods must be nonnegative')
    if compounding == 'continuous':
        return pv * math.exp(rate * periods)
    if compounding != 'periodic' or rate <= -1:
        raise ValueError('Periodic rate must be > -100%')
    return pv * (1 + rate) ** periods


def present_value(fv: float, rate: float, periods: int) -> float:
    if periods < 0 or rate <= -1:
        raise ValueError('Invalid periods or rate')
    return fv / (1 + rate) ** periods


def payment(principal: float, rate: float, periods: int) -> float:
    if periods <= 0 or principal < 0 or rate <= -1:
        raise ValueError('Principal must be nonnegative, periods positive, rate > -100%')
    if abs(rate) < 1e-14:
        return principal / periods
    return principal * rate / (1 - (1 + rate) ** (-periods))


def npv(rate: float, cash_flows) -> float:
    if rate <= -1:
        raise ValueError('Discount rate must be greater than -100%')
    cash_flows = np.asarray(cash_flows, dtype=float)
    if cash_flows.size < 1 or not np.isfinite(cash_flows).all():
        raise ValueError('At least one finite cash flow is required')
    return float(sum(float(cf) / (1 + rate) ** i for i, cf in enumerate(cash_flows)))


def irr(cash_flows) -> float:
    flows = np.asarray(cash_flows, dtype=float)
    if flows.size < 2 or not (np.any(flows > 0) and np.any(flows < 0)):
        raise ValueError('IRR needs at least two periods and both positive/negative cash flows')
    # Scan for rate sign changes; non-conventional flows may have multiple IRRs.
    rates = np.r_[np.linspace(-0.9999, -0.9, 80), np.linspace(-0.9, 1, 400),
                  np.geomspace(2, 1e5, 200)]
    roots = []
    prev_rate, prev_val = float(rates[0]), npv(float(rates[0]), flows)
    for rate in rates[1:]:
        value = npv(float(rate), flows)
        if prev_val * value < 0:
            root = brentq(lambda r: npv(r, flows), prev_rate, float(rate))
            if not any(abs(root - other) < 1e-7 for other in roots):
                roots.append(root)
        elif value == 0 and not any(abs(float(rate) - other) < 1e-7 for other in roots):
            roots.append(float(rate))
        prev_rate, prev_val = float(rate), value
    if not roots:
        raise ValueError('No IRR root found in the scanned range (-99.99%, 10000000%)')
    if len(roots) > 1:
        raise ValueError(f'Multiple IRRs found: {[round(x, 7) for x in roots]}. IRR is ambiguous.')
    return roots[0]


def amortization(principal: float, rate: float, periods: int, period: int):
    if not 1 <= period <= periods:
        raise ValueError('Selected period must be within 1..periods')
    pmt = payment(principal, rate, periods)
    if abs(rate) < 1e-14:
        balance = max(0., principal - pmt * period)
        interest = 0.
        principal_paid = pmt
    else:
        prev = principal * (1 + rate) ** (period - 1) - pmt * (((1 + rate) ** (period - 1) - 1) / rate)
        interest = prev * rate
        principal_paid = pmt - interest
        balance = max(0.0, prev - principal_paid)
    return {'Payment': pmt, 'Interest (selected period)': interest,
            'Principal (selected period)': principal_paid,
            'Remaining balance': balance}


def fin_fv(v):
    pv, r, n = number(v['pv']), number(v['rate']), integer(v['n'], minimum=0)
    continuous = integer(v['continuous'], minimum=0)
    if continuous not in (0, 1):
        raise ValueError('Continuous mode must be 0 or 1')
    return future_value(pv, r, n, compounding='continuous' if continuous else 'periodic')


def fin_pv(v):
    return present_value(number(v['fv']), number(v['rate']), integer(v['n'], minimum=0))


def fin_pmt(v):
    return payment(number(v['principal']), number(v['rate']), integer(v['n'], minimum=1))


def fin_npv(v):
    return npv(number(v['rate']), vector(v['flows']))


def fin_irr(v):
    return irr(vector(v['flows']))


def fin_loan(v):
    return amortization(number(v['principal']), number(v['rate']),
                        integer(v['n'], minimum=1), integer(v['period'], minimum=1))


def fin_cagr(v):
    start, end = number(v['start']), number(v['end'])
    years = number(v['years'])
    if start <= 0 or end < 0 or years <= 0:
        raise ValueError('Start must be >0, end >=0, years >0')
    return (end / start) ** (1 / years) - 1


def fin_effective(v):
    r, m = number(v['rate']), integer(v['m'], minimum=1)
    if r / m <= -1:
        raise ValueError('Periodic rate must be > -100%')
    return (1 + r / m) ** m - 1


def fin_annuity(v):
    pmt, r, n = number(v['payment']), number(v['rate']), integer(v['n'], minimum=1)
    if r <= -1:
        raise ValueError('Rate must be > -100%')
    return pmt * (n if abs(r) < 1e-14 else (1 - (1 + r) ** -n) / r)
