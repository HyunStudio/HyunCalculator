# HyunCalculator

**v1.2.0-alpha.1** · **한국어 / English** · Desktop (Windows, macOS, Linux) · Python 3.11+

An integrated scientific, graphing, financial, quantitative finance, programmer and ML/DL/RL calculator, based on the original bilingual 19-function Tkinter calculator.

## v1.2.0-alpha.1 — Formula to Code (initial implementation)

The first **working** Formula to Code tab and CLI are available. The goal remains
**33 Financial/Quant formulas × 14 languages (462 combinations)**, but **this
alpha currently exports only 7 complete formulas across 14 language emitters
(98 source-generation combinations)**. The other 26 formulas are listed as
**PLANNED**, and attempting to generate their code raises a clear error instead
of emitting misleading placeholders. All seven have codegen unit tests; only
installed compiler toolchains have been runtime-tested.

**Currently exportable:** FIN-001 Future Value (periodic/continuous), FIN-002 Present
Value, FIN-003 Loan Payment, FIN-004 Net Present Value, FIN-007 CAGR, FIN-008
Effective Annual Rate, FIN-009 Annuity Present Value. NPV supports `for` and
`while` loop choices; analytic formulas reject irrelevant loop selections.

**Languages:** Python, R, C, C++, JavaScript, TypeScript, Java, C#, Swift, Kotlin,
Go, Rust, MATLAB, Julia. **Class architecture:** supported only for Python,
C++, JavaScript, TypeScript, Java, C#, Swift and Kotlin in scalar-formula mode.
Custom function/class names and variable renames are validated to block
invalid identifiers. Imports are currently automatic or standard-library-only;
external scientific-library choice is not yet implemented.

### Example: generate source files

~~~bash
python -m hyuncalculator --list-formulas
python -m hyuncalculator --generate FIN-001 --language Python --output future_value.py
python -m hyuncalculator --generate FIN-002 --language Java --structure class --class-name FinanceMath --function-name discount --rename fv=face_value --output FinanceMath.java
python -m hyuncalculator --generate FIN-004 --language C++ --loop while --output npv.cpp
~~~

Use the new **Code Generator** tab to preview, copy, and save source code. A generated
file is not automatically compiled or executed in the UI; verify correctness and
required toolchains for your target language. The [v1.2 design specification](docs/FORMULA_TO_CODE_V1_2_DESIGN.md)
describes the remaining 26 formula adapters, validation matrix, deployment and advanced
controls. The project's existing Scientific/Graphing/Financial/Quant/Programmer/ML/DL/RL
calculations are retained.

### About, creator, and sponsorship

**Creator:** 황현기 / HyunGi Hwang (HyunStudio)  
**Public project contact:** hyungi2344@gmail.com  
**GitHub:** https://github.com/HyunStudio/HyunCalculator

**GitHub Sponsors status: pending approval as of 2026-11-06**. The sponsor profile
has been submitted but is not live. The app's About tab displays a pending notice;
**there is no active donation/payment button or unverified PayPal link**. Activate a
verified sponsorship link only after GitHub approves the HyunStudio profile.

## Features / 주요 기능

| Tab | Available functions / 주요 기능 |
| --- | --- |
| **Scientific / 공학용** | Safe expression evaluator; arithmetic, powers, `sin/cos/tan`, inverse trig, radians/degrees, `log/ln`, `sqrt/cbrt/root`, factorial/permutations/combinations, memory, history, Ans |
| **Graphing / 그래프** | Plot up to 8 functions `y=...` or `f(x)=...`, adjustable domain/sample count, RAD/DEG, zoom via Matplotlib toolbar (when enabled), PNG export |
| **Financial / 금융** | FV/PV, periodic & continuous compounding, PMT, NPV/IRR, amortization, CAGR, effective annual rate, ordinary annuity |
| **Quant / 금융공학** | Black–Scholes (dividend-adjusted), Greeks, implied volatility, antithetic Monte Carlo, portfolio moments, unconstrained minimum variance and Markowitz target return, Black–Litterman posterior, historical/normal VaR and ES, Sharpe/Sortino/drawdown, fixed-coupon bond price/duration/convexity, EWMA/GARCH(1,1), GBM/OU moments, sample covariance/correlation, normal PDF/CDF/quantiles, nominal bond YTM inversion, SMA/EMA, seeded Brownian/GBM/OU path simulation, explicit transaction costs, no-lookahead single-asset backtest with fees/slippage, equity curves and CAGR |
| **Programmer / 프로그래머** | Base 2/8/10/16 conversion, 8/16/32/64-bit signed/unsigned two's complement, AND/OR/XOR/NAND/NOR/NOT, logical/arithmetic shifts, rotations, popcount |
| **ML, DL, RL / 인공지능** | Original **19 functions preserved**, including linear prediction, MSE/MAE, binary metrics/BCE, sigmoid/ReLU/softmax, dense/conv, gradient step, discounted return, TD target/error, Q-learning, Bellman and epsilon-greedy |

**Not included:** Computer algebra / symbolic integration, 3D graphing, real-time market prices, broker execution, American option pricing, proprietary risk-model calibration, multi-asset/event-driven backtesting or production trading infrastructure. These are concrete computational tools, not a universal mathematics engine.

## Install & run / 설치 및 실행

```powershell
# Windows PowerShell, from the project root
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m hyuncalculator
```

```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m hyuncalculator --lang en
```

**GUI note:** requires a local desktop session with Tkinter/Tk support. Linux might require `python3-tk` from the OS package manager; SSH/headless servers cannot show GUI windows.

### Test / 테스트

```bash
python -m hyuncalculator --test
# or
python -m unittest discover -s tests -v
# run historical regression suite
python hyuncalculator/legacy_ml.py --test
```

GitHub Actions runs unit tests on Python 3.11 and 3.12. The **80 automated tests** include regression and extended quantitative verification; all computational tests run without GUI/display. See [CHANGELOG.md](CHANGELOG.md) for the 10-domain implementation checklist.

### Examples / 예제

Scientific: `sin(pi/6) + sqrt(16)`, `factorial(6)`, `log(100)` (base 10), `ln(e)`.

Graphing: `y=sin(x); y=x^2/10` with X minimum `-10`, maximum `10`.

Financial: `NPV` takes cash flows starting at t=0: `-100, 60, 60`, discount rate `0.1`.

Quant: Black–Scholes `S=100, K=100, T=1, r=0.05, sigma=0.2, q=0, call` should return approximately `10.45058357`. Black–Litterman row input `0.04,0.01;0.01,0.09` is a 2×2 covariance matrix.

Programmer: base=16, value=`FF`, width=8 yields signed `-1`, unsigned `255`.

### Newly added examples (v1.1.0) / 추가 예제

- **Normal probabilities / 정규분포:** `x=1.96, mean=0, std=1, p=0.95` gives PDF, CDF, survival probability, Z-score, and the `p` quantile.
- **Bond YTM / 채권 만기수익률:** `price=1000, face=1000, coupon=0.05, years=5, freq=2` gives nominal annual YTM `0.05` (5%). Input price is the **dirty/full** price and assumes equal coupon periods with no accrued-interest adjustment.
- **Moving averages / 이동평균:** series `1,2,3,4,5` with window `3` gives SMA `[2,3,4]`; EMA is seeded by the first observation.
- **Brownian, GBM, OU:** generate seeded example paths as well as simulated and theoretical terminal mean/volatility. `paths * steps` is capped at 2 million. GBM/OU transitions are exact under the stated model parameters.
- **Transaction costs / 거래비용:** notional `100000`, commission `5` bps, slippage `3` bps, half-spread `2` bps, 2 sides yields estimated total cost `200`.
- **Backtest / 백테스트:** input period returns and close-of-period target weights in `[-1,1]`. The weight **is delayed by one full period** to avoid lookahead (`position[t]=signal[t-1]`). The initial position is zero and the final unexecuted signal is ignored. Commission and slippage are in basis points per unit of **absolute turnover**. The backtest reports net/gross returns, buy-and-hold, Sharpe/Sortino, CAGR, drawdown, wins, turnover, and the equity curve.

### Inputs, conventions and limitations / 입력 규칙

- **Rates and returns are decimals**, not percentages: `0.05` means 5%; maturities are in years where specified. Enter per-period rates for time-value/loan calculations.
- Separate vector values with commas or spaces. Separate matrix rows with **semicolons** (`;`).
- `^` is power in Scientific/Graphing modes, not XOR. Use `XOR` in Programmer mode.
- Graph functions use `x`. No arbitrary Python execution is permitted: the expression parser validates every AST node and function name, and does **not** use `eval`.
- Covariance matrices must be positive definite for inverse-based optimization. Portfolio weights are fully invested and **short-selling is permitted**; there are no transaction costs or constraints.
- Black–Scholes applies to **European** vanilla options; Greeks use changes of 1.00 in annual decimal vol/rate (divide Vega/Rho by 100 for per 1% point). At zero T or vol, undefined Greeks are NaN.
- Historical VaR is the quantile of **signed losses**; VaR can be negative in profitable scenarios. Historical ES is the mean of losses above/equal to the empirical quantile; small samples are noisy.
- IRR searches a finite range and rejects detected **multiple roots**; changing-sign roots can be missed in degenerate/tangent cases.
- Monte Carlo uses a fixed seed and antithetic paths, with pair-based standard errors; **use an even number of paths**.
- Backtest uses one instrument with fractional long/short weights limited to [-1,1] and applies close-to-close simple returns. It assumes immediate frictional execution, no borrowing/financing charges or market impact, and **no terminal liquidation charge**. Use research-grade, time-aligned return/position data; it is not a broker or production backtest engine.
- Brownian, GBM and OU path simulations are stochastic and reproducible given the same seed. Theoretical outputs assume constant parameters.
- UI field values remain intact when toggling Korean/English. No data is transmitted to a server.

This application is for education, research prototyping and numerical checks—not financial, investment or risk management advice. Validate model assumptions and numerical results independently for consequential decisions.

## Layout

```text
hyuncalculator/
  __main__.py       # launch GUI or tests
  gui.py            # bilingual Tkinter front-end + Matplotlib plot
  scientific.py     # safe scalar/array expression evaluator
  graphing.py       # sample and validate real-valued curves
  finance.py        # TVM / loans / cash-flow functions
  quant.py          # derivatives, portfolios, risk, distributions, time-series, simulation and strategy backtesting
  programmer.py     # integer representations and bit operations
  operations.py     # bilingual operation catalog and defaults
  legacy_ml.py      # original 19 ML/DL/RL operations & tests
```
