# Changelog

## v1.1.0 — Quantitative Finance Completeness Update

The ten requested quantitative finance domains are now reachable in the **Quant / 금융공학** tab.

- Financial mathematics: compound/continuous growth, present/future values (Financial tab).
- Probability and statistics: normal PDF, CDF, survival function, inverse CDF, covariance and correlation, Monte Carlo pricing.
- Portfolio analytics: weighted expected returns, volatility and Sharpe ratio.
- Allocation: Markowitz minimum variance / target return and Black–Litterman posterior.
- Derivatives: dividend-adjusted Black–Scholes call/put prices and Greeks, implied volatility, European Monte Carlo.
- Fixed-income: coupon bond price, **YTM solved from dirty price**, Macaulay/modified duration, convexity.
- Risk: historical/normal VaR and expected shortfall, maximum drawdown, Sharpe/Sortino.
- Time series: **SMA/EMA**, EWMA and one-step GARCH(1,1) forecast.
- Stochastic processes: analytical GBM/OU moments, **Brownian motion simulation** and **exact-increment GBM / exact-discretization OU path simulation**.
- Quant strategy: **non-lookahead single-asset backtest**, commissions and slippage in bps, transaction costs, position change counts, equity curves and risk-adjusted performance.

The eight new finance operations are registered for both Korean and English UI. The original 19 ML/DL/RL operations remain intact, as do the Scientific, Graphing, Financial and Programmer tabs.

### Validation

- 80 automated unit/regression tests (56 original + 24 extended).
- Korean and English Tkinter window smoke tests (eight tabs per language).
- Headless GUI calculation and language-switch smoke tests for all eight new operations.
- Tests are suitable for GitHub Actions (Python 3.11/3.12).

### Assumptions

Use decimal annual or per-period rates as indicated. Fixed income excludes coupon stubs and accrued interest. The strategy backtest is a single-instrument teaching tool: target positions are delayed one period, transaction costs are assessed on changes in position, and financing/borrow fees and end-of-test liquidation are not modeled.
