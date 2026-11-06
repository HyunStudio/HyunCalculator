# HyunCalculator

**v1.2.0-alpha.5** · **한국어 / English** · Desktop (Windows, macOS, Linux) · Python 3.11+

An integrated scientific, graphing, financial, quantitative finance, programmer and ML/DL/RL calculator, based on the original bilingual 19-function Tkinter calculator.

## v1.2.0-alpha.5 — Implied Volatility and Normal VaR/ES (partial implementation)

The v1.1.0 calculator still supports **33 Financial/Quant formulas**. The Formula
Generator now exports standalone **Python for all 33** and source in **all 14
languages for 20 formulas**: Python, R, C, C++, JavaScript, TypeScript, Java,
C#, Swift, Kotlin, Go, Rust, MATLAB, and Julia. **293 of 462 requested source
pairs (63.4%)** are implemented; **13 formulas remain Python-only**, leaving
**169 non-Python pairs**. The generator rejects unsupported pairs explicitly.

### Newly available in 14 languages

| Formula ID | Implementation | Key numerical conventions |
| --- | --- | --- |
| `DERIV-002` — `qf_iv` | Invert European call/put Black–Scholes price using bounded bisection and the shared dividend-adjusted Black–Scholes helper | Spot/strike/price in matching currency units, T in years, rates/vol decimals; no-arbitrage bounds; maximum volatility bracket 10.0; returns NaN or error on invalid/no bracket according to target language |
| `RISK-002` — `qf_normal_var` | Gaussian signed-loss VaR and expected shortfall using the Acklam rational inverse-standard-normal approximation | Outputs `[VaR, ES]` (R/Julia use named outputs), `confidence` in (0,1), mean/vol in the same **per-period** units; approximation ~1e-9 in z under normal conditions |

For non-Python `DERIV-002`, an internal Black–Scholes helper is bundled to keep
an exported file standalone without scientific dependencies. `RISK-002` uses
standard mathematical functions only. Python retains the existing SciPy numerical
reference. These two new profiles support function structure, automatic iteration,
and fixed input names only; unsupported Class/Loop/rename requests fail clearly.

**Verification:** **109 local automated regression/generation tests** pass.
Representative C/C++/JavaScript/TypeScript/Java/Swift/Kotlin/Go generated code
was compiled/executed and compared with the existing Python calculator on
multiple cases. **R, C#, Rust, MATLAB and Julia have not been executed in
this environment**; generation is NOT proof of language-wide numerical validity.
The optional executable sample check is `python tests/toolchain_iv_normal_smoke.py`
(requires the target-language toolchains). Previous model-specific smoke tests
remain under `tests/toolchain_*_smoke.py`.

**Constraints:** Large or near-singular inputs, extreme normal-tail probabilities,
and near-arbitrage IV boundaries require independent numerical verification.
Code generation is an educational/research feature, not a trading engine or
investment recommendation. A given language's compiled/run status must be
tracked separately from its generation status.

**Previous alpha.4 support preserved:** dividend-adjusted Black–Scholes/Greeks,
portfolio statistics, empirical VaR/ES, SMA/EMA, bond pricing/duration/YTM,
EWMA, GARCH(1,1), GBM/OU analytical moments, transaction costs and original
financial calculations. The original ML/DL/RL and other calculator screens remain.

The complete 462-pair compiler/numerical verification matrix, advanced algorithm
and import selection, project ZIP bundles, and premium dark UI redesign are **not
complete**. See [v1.2 design specification](docs/FORMULA_TO_CODE_V1_2_DESIGN.md).
HyunStudio Sponsors remains **pending approval**; no live donation or PayPal
payment button is enabled.

### CLI examples / 코드 생성 예제

~~~bash
python -m hyuncalculator --list-formulas
python -m hyuncalculator --generate DERIV-002 --language C++ --output iv.cpp
python -m hyuncalculator --generate RISK-002 --language TypeScript --output normal_var.ts
python -m hyuncalculator --generate DERIV-001 --language Python --output black_scholes.py
python -m hyuncalculator --generate STRAT-002 --language Python --output backtest.py
python -m hyuncalculator --generate TS-002 --language JavaScript --output garch.js
python -m hyuncalculator --generate STOCH-001 --language C++ --output gbm.cpp
python -m hyuncalculator --generate BOND-001 --language Java --output GeneratedCalculator.java
python -m hyuncalculator --generate BOND-002 --language Swift --output ytm.swift
python -m hyuncalculator --generate TS-001 --language C++ --output ewma.cpp
python -m hyuncalculator --generate FIN-004 --language C++ --loop while --output npv.cpp
~~~

The bilingual Code Generator tab offers formula/language selection, source
preview, copy and save. Non-supported language/formula combinations are disabled.
The generated code is **not executed automatically by the UI**.
The [v1.2 technical design](docs/FORMULA_TO_CODE_V1_2_DESIGN.md) describes the
remaining 169 source-generation combinations, systematic toolchain testing,
advanced model algorithms, output packaging and accessibility goals.
Existing Scientific/Graphing/Financial/Quant/Programmer/ML/DL/RL calculators
are preserved.

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

GitHub Actions runs unit tests on Python 3.11 and 3.12. The **98 automated tests** include existing regression, financial/quant, and code generation verification; all computational tests run without GUI/display. See [CHANGELOG.md](CHANGELOG.md) for the 10-domain implementation checklist.

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
