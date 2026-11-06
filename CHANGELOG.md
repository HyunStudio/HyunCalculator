# Changelog

## v1.2.0-alpha.3 — Multi-Language Coupon Bonds, YTM and EWMA (2026-11-06)

- Extended 13 non-Python emitters for **BOND-001** coupon bond dirty price, Macaulay/modified duration and convexity; **BOND-002** dirty-price YTM inversion via bounded bisection; and **TS-001** sequential EWMA variance and volatility.
- These three formulas are now exported in all 14 target languages (Python already supported), bringing source-generation coverage to **215 / 462** combinations; **19 formulas** remain Python-only (247 combinations outstanding).
- Explicit function-only profiles reject unsupported class, loop customization and variable renaming. Input constraints include finite rates/observations, payment period checks, and no accrued-interest adjustment.
- Added source-generation unit contracts and optional C/C++/JavaScript/TypeScript/Java/Swift/Kotlin/Go build-and-execute numerical smoke tests. **98 local Python regression and generator tests** pass. R, C#, Rust, MATLAB and Julia generated outputs still require runtime validation.
- Existing calculator functionality and Sponsors pending-approval behavior remain unchanged. Premium visual redesign and 462-combination runtime verification are still pending.

## v1.2.0-alpha.2 — Broad Python Export + Portable Quant Formulas (2026-11-06)

- Python code generation extended from 7 to **all 33 registered financial/quant formulas** through trusted-source AST extraction with standalone dependencies; sample numeric results compared with the existing calculator for all 33.
- Added 4 complete multi-output quantitative emitters for the other 13 languages: **GARCH(1,1)**, **GBM analytic moments**, **OU analytic moments**, **transaction costs**. Each output includes explicit field/index semantics.
- Current generation coverage **176 / 462 combinations** (33 Python + 11 × 13 other-language targets). All other language/formula pairs fail closed instead of returning incomplete output.
- Code Generator GUI now reacts to language/formula availability and disables unsupported combinations. CLI `--list-formulas` reports exact supported languages.
- Added comprehensive Python golden-value tests and portable source checks, plus optional compiler/runtime smoke suite. 95 automated unit tests pass locally; real runtime validation is partial and separately reported.
- HyunStudio GitHub Sponsors remains **pending approval**, and no donation/payment link is activated.
- Still alpha: high-fidelity dark UI redesign, remaining 286 adapters, complete 462-way numeric/runtime verification and project bundling are pending.


## v1.2.0-alpha.1 — Formula to Code initial implementation (2026-11-06)

- Added a stable, bilingual 33-formula Financial/Quant registry; 26 code adapters
  are explicitly marked **planned** and cannot be exported as placeholders.
- Working AST-based 14-language source emitters for **7 finance functions**:
  Future Value (periodic/continuous), Present Value, Loan Payment, NPV, CAGR,
  Effective Annual Rate, and Ordinary Annuity PV.
- Generated code can be configured with function names, eligible class wrappers,
  variable renames, appropriate NPV for/while loops and standard imports.
  Unsupported language/structure/algorithm combinations fail explicitly.
- Added desktop Code Generator preview/copy/save and CLI `--generate` and
  `--list-formulas`. Code generation never executes user-supplied programs.
- Added **About & Support** with creator 황현기 / HyunGi Hwang,
  project contact and HyunStudio GitHub Sponsors **pending approval** notice.
  No live donation button is shown while approval is pending.
- Preserved existing calculator tabs and included generator regression tests.
- This is an **alpha milestone**, not completion of the 462-combination design.


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
