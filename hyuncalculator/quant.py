"""Quantitative finance formulas for educational/research scenarios (not trading advice).

Rates, returns, volatilities are DECIMALS. Annualized inputs where indicated.
Monte Carlo is seeded and implements antithetic sampling for reproducibility.
Portfolio optimizers allow short positions and ignore transaction costs.
"""
from __future__ import annotations

import math
import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm
from .legacy_ml import number, integer, vector, matrix


def _covariance(sigma):
    m = np.asarray(sigma, dtype=float)
    if m.ndim != 2 or m.shape[0] != m.shape[1] or m.shape[0] < 2:
        raise ValueError('Covariance matrix must be square with dimension >= 2')
    if not np.isfinite(m).all() or not np.allclose(m, m.T, atol=1e-9):
        raise ValueError('Covariance must be finite and symmetric')
    if np.linalg.eigvalsh(m).min() <= 1e-12:
        raise ValueError('Covariance must be positive definite (no singular matrix)')
    return m


def black_scholes(spot, strike, maturity, rate, volatility, *, dividend=0., option='call'):
    s, k, t, r, sig, q = map(float, (spot, strike, maturity, rate, volatility, dividend))
    if s <= 0 or k <= 0 or t < 0 or sig < 0 or option not in ('call', 'put'):
        raise ValueError('Spot/strike must be >0, T/vol >=0, option call/put')
    sign = 1 if option == 'call' else -1
    if t == 0:
        return {'Price': max(sign * (s - k), 0.), 'Delta': float('nan'),
                'Gamma': float('nan'), 'Vega (per 1.00 vol)': 0.,
                'Theta (per year)': float('nan'), 'Rho (per 1.00 rate)': 0.}
    if sig == 0:
        call = max(s * math.exp(-q*t) - k * math.exp(-r*t), 0.)
        put = max(k * math.exp(-r*t) - s * math.exp(-q*t), 0.)
        return {'Price': call if sign == 1 else put, 'Delta': float('nan'),
                'Gamma': float('nan'), 'Vega (per 1.00 vol)': 0.,
                'Theta (per year)': float('nan'), 'Rho (per 1.00 rate)': float('nan')}
    root = sig * math.sqrt(t)
    d1 = (math.log(s/k) + (r-q+0.5*sig*sig)*t) / root
    d2 = d1 - root
    dq, dr = math.exp(-q*t), math.exp(-r*t)
    price = sign * (s*dq*norm.cdf(sign*d1) - k*dr*norm.cdf(sign*d2))
    delta = sign*dq*norm.cdf(sign*d1)
    gamma = dq*norm.pdf(d1)/(s*root)
    vega = s*dq*norm.pdf(d1)*math.sqrt(t)
    theta = (-s*dq*norm.pdf(d1)*sig/(2*math.sqrt(t))
             + sign*q*s*dq*norm.cdf(sign*d1)
             - sign*r*k*dr*norm.cdf(sign*d2))
    rho = sign*k*t*dr*norm.cdf(sign*d2)
    return {'Price': price, 'Delta': delta, 'Gamma': gamma,
            'Vega (per 1.00 vol)': vega, 'Theta (per year)': theta,
            'Rho (per 1.00 rate)': rho}


def implied_volatility(price, spot, strike, maturity, rate, dividend=0., option='call'):
    if maturity <= 0:
        raise ValueError('Implied volatility requires T > 0')
    sign = 1 if option == 'call' else -1
    if sign not in (1, -1):
        raise ValueError('Invalid option')
    if spot <= 0 or strike <= 0 or price < 0:
        raise ValueError('Spot/strike > 0 and price >= 0 required')
    discounted_s, discounted_k = spot*math.exp(-dividend*maturity), strike*math.exp(-rate*maturity)
    lower = max(sign*(discounted_s-discounted_k), 0.)
    upper = discounted_s if option == 'call' else discounted_k
    if price < lower - 1e-9 or price >= upper:
        raise ValueError('Price violates no-arbitrage bounds or implies infinite volatility')
    if price <= lower + 1e-12:
        return 0.
    return brentq(lambda vol: black_scholes(spot, strike, maturity, rate, vol,
                                           dividend=dividend, option=option)['Price']-price,
                  1e-10, 10., xtol=1e-12)


def european_mc(spot, strike, maturity, rate, volatility, dividend=0.,
                option='call', paths=20000, seed=42):
    if spot <= 0 or strike <= 0 or maturity <= 0 or volatility < 0:
        raise ValueError('Spot/strike/T >0 and volatility >=0 required')
    if option not in ('call', 'put') or not 100 <= paths <= 1_000_000 or paths % 2:
        raise ValueError('Option must be call/put; even path count 100..1,000,000')
    rng = np.random.default_rng(int(seed))
    z = rng.standard_normal(paths//2)
    z = np.r_[z, -z]
    st = spot * np.exp((rate-dividend-0.5*volatility**2)*maturity + volatility*math.sqrt(maturity)*z)
    sign = 1 if option == 'call' else -1
    payoff = np.maximum(sign*(st-strike), 0.)*math.exp(-rate*maturity)
    # Antithetic observations aren't iid; estimate standard error from PAIRS.
    paired = payoff[:paths//2] + payoff[paths//2:]
    pair_means = paired/2
    estimate = float(np.mean(payoff))
    stderr = float(np.std(pair_means, ddof=1)/math.sqrt(pair_means.size))
    return {'Monte Carlo price': estimate, 'Std. error (paired)': stderr,
            '95% CI lower': estimate - 1.96*stderr,
            '95% CI upper': estimate + 1.96*stderr}


def portfolio_stats(weights, expected_returns, sigma, risk_free=0.):
    w = np.asarray(weights, dtype=float)
    mu = np.asarray(expected_returns, dtype=float)
    cov = _covariance(sigma)
    if w.ndim != 1 or mu.shape != w.shape or cov.shape[0] != w.size:
        raise ValueError('Weights/returns/covariance dimensions must agree')
    if not np.isclose(w.sum(), 1., atol=1e-8):
        raise ValueError('Portfolio weights must sum to 1')
    ret = float(w @ mu)
    vol = math.sqrt(max(float(w @ cov @ w), 0))
    return {'Expected return': ret, 'Volatility': vol,
            'Sharpe ratio': (ret-risk_free)/vol if vol > 0 else float('nan')}


def global_minimum_variance(sigma):
    cov = _covariance(sigma)
    ones = np.ones(cov.shape[0]); inv_ones = np.linalg.solve(cov, ones)
    return inv_ones / (ones@inv_ones)


def minimum_variance_target(expected_returns, sigma, target):
    cov = _covariance(sigma)
    mu = np.asarray(expected_returns, float)
    if mu.shape != (cov.shape[0],):
        raise ValueError('Expected return vector length mismatches covariance')
    a = np.vstack([np.ones(cov.shape[0]), mu]).T
    if np.linalg.matrix_rank(a) < 2:
        raise ValueError('Assets require distinct expected returns for a target-return constraint')
    sol = np.linalg.solve(cov, a)
    w = sol @ np.linalg.solve(a.T @ sol, np.array([1., target]))
    return w


def black_litterman(sigma, market_weights, risk_aversion, tau, views, view_returns, omega):
    cov = _covariance(sigma)
    market = np.asarray(market_weights, dtype=float)
    p = np.atleast_2d(np.asarray(views, dtype=float))
    q = np.asarray(view_returns, dtype=float)
    errors = np.asarray(omega, dtype=float)
    n = cov.shape[0]
    if market.shape != (n,) or not np.isclose(market.sum(), 1., atol=1e-8):
        raise ValueError('Market weights must match covariance and sum to 1')
    if tau <= 0 or risk_aversion <= 0:
        raise ValueError('tau and risk aversion must be positive')
    if p.shape[1] != n or q.shape != (p.shape[0],) or errors.shape != (p.shape[0],):
        raise ValueError('View matrix/returns/uncertainties dimensions mismatch')
    if (errors <= 0).any():
        raise ValueError('View variances must be strictly positive')
    prior = risk_aversion*(cov @ market)
    prior_cov = tau*cov
    a = p@prior_cov@p.T+np.diag(errors)
    innovation = np.linalg.solve(a, q-p@prior)
    posterior = prior + prior_cov@p.T@innovation
    posterior_mu_cov = prior_cov - prior_cov@p.T@np.linalg.solve(a, p@prior_cov)
    return {'Equilibrium returns': prior, 'Posterior expected returns': posterior,
            'Posterior predictive covariance': cov + posterior_mu_cov}


def historical_var_es(returns, confidence=0.95):
    r = np.asarray(returns, float)
    if r.ndim != 1 or r.size < 3 or not np.isfinite(r).all() or not 0 < confidence < 1:
        raise ValueError('At least 3 finite returns and 0 < confidence < 1 are required')
    losses = -r
    cutoff = float(np.quantile(losses, confidence))
    # Equal-weight empirical tail (discrete sample ES estimate).
    tail = losses[losses >= cutoff - 1e-12]
    return {'VaR (signed loss quantile)': cutoff, 'Expected Shortfall': float(np.mean(tail))}


def normal_var_es(mean, volatility, confidence=0.95):
    if volatility < 0 or not 0 < confidence < 1:
        raise ValueError('Volatility >= 0 and 0 < confidence < 1 required')
    z = norm.ppf(confidence)
    return {'VaR (signed loss quantile)': -mean + z*volatility,
            'Expected Shortfall': -mean + volatility*norm.pdf(z)/(1-confidence)}


def risk_metrics(returns, risk_free_per_period=0, periods_per_year=252):
    r = np.asarray(returns, float)
    if r.ndim != 1 or r.size < 3 or np.any(r <= -1) or not np.isfinite(r).all():
        raise ValueError('Provide at least 3 finite simple returns greater than -100%')
    if periods_per_year < 1:
        raise ValueError('Periods per year must be positive')
    excess = r - risk_free_per_period
    std = float(np.std(excess, ddof=1))
    downside = math.sqrt(float(np.mean(np.minimum(excess, 0)**2)))
    wealth = np.r_[1., np.cumprod(1+r)]
    peak = np.maximum.accumulate(wealth)
    total = float(wealth[-1])
    return {'Annualized arithmetic mean': float(np.mean(r)*periods_per_year),
            'Annualized volatility': std*math.sqrt(periods_per_year),
            'Annualized Sharpe': float(np.mean(excess)/std*math.sqrt(periods_per_year)) if std else float('nan'),
            'Annualized Sortino': float(np.mean(excess)/downside*math.sqrt(periods_per_year)) if downside else float('nan'),
            'Max drawdown': float(np.min(wealth/peak-1)),
            'Compounded total return': total-1}


def bond_metrics(face, coupon_rate, yield_rate, maturity_years, payments_per_year=2):
    if face <= 0 or maturity_years <= 0 or payments_per_year < 1:
        raise ValueError('Face, years and payment frequency must be positive')
    if abs(maturity_years*payments_per_year - round(maturity_years*payments_per_year)) > 1e-8:
        raise ValueError('Years * frequency must be an integer number of coupon payments')
    freq = int(payments_per_year)
    if yield_rate/freq <= -1:
        raise ValueError('Yield per period must exceed -100%')
    n = round(maturity_years*freq)
    t = np.arange(1, n+1)
    cfs = np.full(n, face*coupon_rate/freq)
    cfs[-1] += face
    discount = (1+yield_rate/freq)**t
    pv = cfs / discount
    price = float(pv.sum())
    macaulay = float((t*pv).sum()/price/freq)
    modified = macaulay/(1+yield_rate/freq)
    convexity = float(np.sum(t*(t+1)*pv)/(price*freq**2*(1+yield_rate/freq)**2))
    return {'Price': price, 'Macaulay duration (years)': macaulay,
            'Modified duration (years)': modified, 'Convexity (years²)': convexity}


def ewma_volatility(returns, decay=0.94):
    r = np.asarray(returns, float)
    if r.ndim != 1 or r.size < 2 or not np.isfinite(r).all() or not 0 <= decay < 1:
        raise ValueError('Need >= 2 returns and 0 <= decay < 1')
    variance = float(r[0]**2)
    for obs in r[1:]:
        variance = decay*variance + (1-decay)*float(obs**2)
    return {'EWMA variance': variance, 'EWMA volatility': math.sqrt(variance)}


def garch_forecast(last_variance, last_shock, omega, alpha, beta):
    if min(last_variance, omega, alpha, beta) < 0 or alpha+beta >= 1:
        raise ValueError('Variances/parameters >=0 and alpha+beta < 1 required')
    next_variance = omega + alpha*last_shock**2 + beta*last_variance
    return {'Forecast variance': next_variance, 'Forecast volatility': math.sqrt(next_variance),
            'Unconditional variance': omega/(1-alpha-beta)}


def gbm_moments(spot, drift, volatility, years):
    if spot <= 0 or volatility < 0 or years < 0:
        raise ValueError('S0 >0, volatility >=0, T >=0')
    mean = spot*math.exp(drift*years)
    variance = spot**2*math.exp(2*drift*years)*(math.exp(volatility**2*years)-1)
    return {'Expected price': mean, 'Std. deviation': math.sqrt(max(variance, 0.))}


def ou_moments(initial, mean_level, speed, volatility, years):
    if speed <= 0 or years < 0 or volatility < 0:
        raise ValueError('Mean reversion speed >0; T and volatility >=0')
    mean = mean_level + (initial-mean_level)*math.exp(-speed*years)
    variance = volatility**2*(1-math.exp(-2*speed*years))/(2*speed)
    return {'Expected state': mean, 'Std. deviation': math.sqrt(max(variance,0.))}


def covariance_correlation(returns_matrix):
    data = np.asarray(returns_matrix, float)
    if data.ndim != 2 or data.shape[0] < 3 or data.shape[1] < 2:
        raise ValueError('Rows=observations (>=3), columns=assets (>=2)')
    cov = np.cov(data, rowvar=False, ddof=1)
    return {'Sample covariance': cov, 'Sample correlation': np.corrcoef(data, rowvar=False)}


# GUI adapters: dict-of-strings contract reused from existing ML/DL/RL UI.
def qf_bs(v):
    return black_scholes(number(v['s']), number(v['k']), number(v['t']), number(v['r']),
                         number(v['sigma']), dividend=number(v['q']), option=v['type'].strip().lower())


def qf_iv(v):
    return implied_volatility(number(v['price']), number(v['s']), number(v['k']), number(v['t']),
                              number(v['r']), number(v['q']), option=v['type'].strip().lower())


def qf_mc(v):
    return european_mc(number(v['s']), number(v['k']), number(v['t']), number(v['r']),
                       number(v['sigma']), number(v['q']), option=v['type'].strip().lower(),
                       paths=integer(v['paths'], minimum=100), seed=integer(v['seed']))


def qf_portfolio(v):
    return portfolio_stats(vector(v['w']), vector(v['mu']), matrix(v['cov']), number(v['rf']))


def qf_gmv(v):
    w = global_minimum_variance(matrix(v['cov']))
    return {'Weights': w, 'Portfolio variance': float(w@matrix(v['cov'])@w)}


def qf_target(v):
    w = minimum_variance_target(vector(v['mu']), matrix(v['cov']), number(v['target']))
    return {'Weights': w, 'Expected portfolio return': float(w@vector(v['mu']))}


def qf_bl(v):
    return black_litterman(matrix(v['cov']), vector(v['market']), number(v['delta']),
                          number(v['tau']), matrix(v['views']), vector(v['returns']), vector(v['omega']))


def qf_hist_var(v):
    return historical_var_es(vector(v['r']), number(v['confidence']))


def qf_normal_var(v):
    return normal_var_es(number(v['mean']), number(v['sigma']), number(v['confidence']))


def qf_performance(v):
    return risk_metrics(vector(v['r']), number(v['rf']), integer(v['ppy'], minimum=1))


def qf_bond(v):
    return bond_metrics(number(v['face']), number(v['coupon']), number(v['yield']),
                        number(v['years']), integer(v['freq'], minimum=1))


def qf_ewma(v):
    return ewma_volatility(vector(v['r']), number(v['decay']))


def qf_garch(v):
    return garch_forecast(number(v['lastvar']), number(v['shock']), number(v['omega']),
                          number(v['alpha']), number(v['beta']))


def qf_gbm(v):
    return gbm_moments(number(v['s']), number(v['mu']), number(v['sigma']), number(v['t']))


def qf_ou(v):
    return ou_moments(number(v['x']), number(v['level']), number(v['kappa']), number(v['sigma']), number(v['t']))


def qf_cov(v):
    return covariance_correlation(matrix(v['returns']))
