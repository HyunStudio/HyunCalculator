# Changelog

## v1.2.0-alpha.14 — R/C#/Julia CI and 175% GUI Reflow (2026-11-06)

- Added required GitHub Actions jobs running generated **R, C# (.NET 8)
  and Julia** source code against Python numerical references, six model
  samples in each language. Missing runtimes cause CI failure.
- Source-generation coverage remains **462/462**. Mandatory native smoke
  totals **57/57 verified representative cases** across C, C++, JavaScript,
  Rust, R, C# and Julia. Latest Python 3.11 and 3.12 regressions, and
  the 10-tab Tk/Xvfb accessibility test, also passed.
- Restructured the code-generation controls to avoid horizontal overflow:
  a 3+2 options grid, separate action-button row and vertically stacked
  class/rename fields. 175% zoom with a 1200px window is tested.
- Added `Ctrl+PageUp` and `Ctrl+PageDown` tab cycling.
- MATLAB/Octave, full 462-pair numerical compiler matrix, complete screen
  reader testing and advanced generator options are still outstanding.
- Sponsors remains pending approval; donation links are not activated.

## v1.2.0-alpha.13 — Accessible Desktop Themes (2026-11-06)

- Added mandatory CI for 6 generated **Rust** numerical code samples,
  compiled and executed with `rustc` (6 PASS / 0 FAIL), in addition to the
  33 C/C++/JavaScript native smoke cases (33 PASS / 0 FAIL). Latest Python
  3.11 and 3.12 runs each passed **154 tests**; Xvfb/Tk 10-tab accessibility
  test also passed. **39 representative native cases**, not full 462-pair
  compiler/numeric validation.

- Added reusable native Tk appearance module with dark/light/high-contrast
  palettes, toolbar selection, 100–175% text sizes, keyboard zoom/toggle,
  local validated preference persistence and atomic settings writes.
- Applied theme to Tk/ttk inputs, financial result areas, code editor,
  lists and Matplotlib chart labels/legends.
- Introduced 4 no-display appearance unit tests, and a dedicated Xvfb/Tk
  GUI smoke for ten tabs, live theme/zoom changes and persistence.
- Formula-to-Code source generator still covers 462/462 combinations;
  compiler/numerical verification remains partial. Full accessible layout
  review and Windows/macOS interaction testing are still pending.
- Github Sponsors remains approval-pending and non-payable.

## v1.2.0-alpha.12 — Reproducible ZIP Exports (2026-11-06)

- New required GitHub Actions `native-smoke` job compiles/executes
  **11 representative models × C/C++/JavaScript = 33 cases**, comparing
  numeric outputs with reference values. First run **33 PASS / 0 FAIL**.
  The Python 3.11 and 3.12 CI jobs each passed 150 tests. This is limited
  runtime coverage, not a blanket claim for 462 combinations.

- Added deterministic `bundle_bytes()` ZIP export for all 462 generated source
  profiles, including source, raw example fields, option manifest with SHA-256,
  offline integrity test, README and language dependency/compilation hints.
- New `--bundle OUTPUT.zip` CLI switch with validation that it is not combined
  with `--output`, and a bilingual **Project ZIP** button in the generator GUI.
- Added bundle safety, reproducibility, integrity, Python syntax and CLI tests.
  Archive contents do not execute generated code or assert numerical correctness.
- Source-emission matrix remains 462/462; cross-language compiler/numerical
  certification and premium UI/advanced options remain follow-up tasks.
- HyunStudio Sponsors remains pending; no payment controls enabled.

## v1.2.0-alpha.11 — All 462 Source-Generation Pairs (2026-11-06)

- Added **STAT-001 normal PDF/CDF/PPF, STAT-002 covariance/correlation,
  RISK-003 return performance, STRAT-002 single-asset backtest** to all
  thirteen non-Python language adapters, preserving the Python reference.
- Code-generation coverage: **33 formulas x 14 languages = 462/462**. New
  adapters restrict unverified class/loop/import/renaming options explicitly.
- Normal CDF/PPF use documented numerical approximations; covariance uses
  sample ddof=1, correlation marks zero variance with NaN. Risk performance
  uses sample volatility and downside semideviation. Backtest uses delayed
  signals, turnover costs, no terminal liquidation, and outputs 4*n+14 values.
- Native smoke samples were compiled/executed for C, C++, JavaScript,
  TypeScript, Java, Swift, Kotlin and Go with reference-value parity.
  R, C#, Rust, MATLAB and Julia emitted sources remain **runtime-unverified**.
  Full 462-way build/numerical certification is **not done**.
- Added regression/coverage tests and updated the design specification.
  Premium UI redesign, advanced library/structure options, ZIP bundles and
  verified Sponsors profile activation remain outstanding.

## v1.2.0-alpha.10 — Portable IRR & Loan Amortization (2026-11-06)

- Added **FIN-005** IRR and **FIN-006** selected-period loan amortization
  for the 13 non-Python languages; existing standalone Python profiles preserved.
- Full 14-language source generation grows to **29/33 formulas** and
  **410/462 formula-language pairs (88.7%)**; 4 functions and 52 other-language
  generation pairs remain.
- IRR: 680-point finite search and 120-step bisection for sign-changing roots,
  rejects multiple detected IRRs and invalid cash flows, with explicit limits
  (not guaranteed to find tangent/off-grid roots). Loan: zero-interest branch,
  amortization payment/interests/principal/remaining balance, parameter guards.
- Selected native compiler/runtime comparisons passed on **C, C++, JavaScript,
  TypeScript, Java, Swift, Kotlin and Go**. R, C#, Rust, MATLAB and Julia emitted
  sources are **runtime-unverified** in this iteration. Generation coverage is
  not equivalent to full 462-way runtime certification.
- Updated registry, test coverage assertions and documentation; added
  `test_codegen_finance.py` and optional `toolchain_finance_smoke.py`.
- Pending GitHub Sponsors profile remains non-payable. Extended GUI/UI themes,
  alternative imports and complete standalone project bundles are still planned.

## v1.2.0-alpha.9 — Brownian / GBM / OU Path Simulation (2026-11-06)

- Added 13 non-Python standalone language adapters for **STOCH-003** arithmetic
  Brownian motion, **STOCH-004** exact-step GBM and **STOCH-005** exact-step OU
  path simulation, preserving the existing NumPy-based Python implementations.
- Both theoretical terminal moments and Monte Carlo terminal mean / sample
  standard deviation, plus a complete first trajectory, are generated.
  Portable output is a numeric vector of `steps + 5` items; C returns a
  `HyunPathResult` struct containing a length and fixed-capacity buffer.
- 14-language support grows to **27/33 formulas**, **384/462 source-generation
  pairs (83.1%)**; **6 formulas** remain Python-only (**78 pairs**).
- The 13 portable languages share Park–Miller 16807 / Box–Muller RNG with
  path-major sampling order; original Python NumPy `default_rng` remains intact,
  so matching Python/other-language seeds do not guarantee identical samples.
  Portable path bounds: steps 1..5000; paths 2..100000; at most 2 million draws;
  seed 1..2147483646. Function/auto/standard-math-only options for portable paths.
- **131 local Python automated tests passed** including 42 newly enabled
  generation combinations, zero-volatility limits, reference parity and
  unsupported option errors. C/C++/JavaScript/TypeScript/Java/Swift/Kotlin
  generated examples compiled/ran and matched the independent portable numeric
  reference. **Go/R/C#/Rust/MATLAB/Julia outputs are runtime-unverified** in this
  iteration; Go timed out during execution checks.
- Existing financial/quant/ML/DL/RL calculation functions and pending
  GitHub Sponsors placeholder remain unchanged. Full 462-way build verification,
  project export bundles, advanced options and dark UI redesign remain pending.

## v1.2.0-alpha.8 — Portable Antithetic Monte Carlo in 14 Languages (2026-11-06)

- Implemented `DERIV-003` European Monte Carlo option-price code generation in
  the remaining **13 non-Python languages**. Now **24/33 formulas** across all
  14 languages: **345/462 source-generation pairs (74.7%)**; remaining
  **9 formulas** are Python-only (**117 non-Python pairs**).
- Standalone portable targets generate shared Park–Miller/Box–Muller seeded
  standard-normal pairs, antithetic GBM terminal prices, discounted payoffs,
  Welford paired sample standard error and 95% confidence bounds.
- Non-Python seed range **1..2,147,483,646** and even path count
  **100..1,000,000**. The original Python NumPy `default_rng` stream stays
  unchanged: cross-language *same-seed* parity is only for the portable
  non-Python languages, not for Python's existing implementation.
- **125 local Python automated tests passed**; independent portable numerical
  reference, option calls and puts, zero volatility, invalid code options, and
  full supported source-generation matrix included. Selected generated
  C/C++/JS/TS/Java/Swift/Kotlin/Go examples compiled or executed and matched
  the portable reference. Missing R/C#/Rust/MATLAB/Julia toolchains mean their
  generated programs remain runtime **unverified**.
- Existing scientific/financial/quant/ML/DL/RL tools and Sponsors **pending**
  placeholder retained unchanged. No active donation/payment link.

## v1.2.0-alpha.7 — Black–Litterman Cross-Language Code Generation (2026-11-06)

- Added `ALLOC-003` `qf_bl` to the 13 non-Python language emitters, completing
  23/33 formulas in all 14 languages: **332/462 source-generation pairs**;
  10 formulas / 130 non-Python pairs remain. Python remains 33/33.
- New dependency-free generated implementations use Cholesky solves to
  compute equilibrium returns, posterior expected returns, and **predictive
  covariance**. R, MATLAB and Julia use validated native linear solves.
- Non-Python return contract is a flat vector of length `2*n+n*n`, with
  posterior covariance in row-major order. C requires explicitly sized
  buffers; n/m input dimensions are capped at 128 in standalone adapters.
- Added tests for 14 emitters, invalid configuration, Python 2-/3-asset
  numerical parity, and malformed matrix/weight/view inputs. **119 local
  automated tests passed**.
- Optional smoke checks compiled/ran real generated source on C, C++,
  JavaScript, TypeScript, Java, Swift, Kotlin and Go for the representative
  2-asset/1-view case with Python-reference numeric parity. R, C#, Rust,
  MATLAB and Julia are **not runtime-verified** by this run.
- Preserved existing Financial/Quant/Scientific/Graphing/Programmer/ML/DL/RL
  functionality. Sponsor profile is still **pending approval**; no payment
  button or unverified sponsor URL is active.

## v1.2.0-alpha.6 — Markowitz GMV and Target-Return Multilingual Export (2026-11-06)

- Added **ALLOC-001** global minimum variance and **ALLOC-002** Markowitz minimum variance with target return in **13 additional languages**, preserving the existing standalone Python implementations. Finite symmetric SPD covariance validation and Cholesky/linear-solve implementation are used; short positions are permitted, and no leverage/long-only constraints are imposed.
- **319 / 462 source-generation combinations** (33 Python + 22×13 other languages). **11 formulas** still support Python only, leaving **143 non-Python adapters** to implement. Standalone non-Python output layout: n weights followed by the portfolio variance or realized expected return, while Python uses named dictionaries.
- Added **5 Python unit/regression tests** for the new model pair, all-language source emission, option validation, Python parity on two and three assets, and covariance/target edge checks. **114 total Python tests passed locally**.
- New optional toolchain smoke tests compiled/executed both models for C, C++, JS, TS, Java, Swift, Kotlin and Go and compared numeric values against the existing Python calculator. R, C#, Rust, MATLAB and Julia are **generated only, not runtime-verified** here.
- Fixed strict C++ `-Werror` indentation issue discovered during test compilation. Advanced class/iteration/rename/import settings remain restricted and fail closed for the new portable models.
- Existing calculation tabs, alpha.5 emitters and pending-approval HyunStudio Sponsors state are retained. Full 462-way compile/numerical verification and premium dark UI remain pending.

## v1.2.0-alpha.5 — Implied Volatility and Gaussian VaR/ES (2026-11-06)

- Added **DERIV-002** option implied volatility via bounded Black–Scholes inversion for all 13 non-Python languages, reusing the verified dividend-adjusted price helper and explicit no-arbitrage bounds.
- Added **RISK-002** normal signed-loss VaR/ES via shared Acklam inverse-normal polynomial approximation for all 13 non-Python languages. Python retains SciPy inverse-normal reference.
- Source-generation coverage rises to **293 / 462 combinations (33 Python + 20×13 others)**; 13 formulas remain Python-only and 169 non-Python pairs outstanding.
- **109 Python regression/generator tests** pass locally, including the coverage matrix, custom names, forbidden settings, reference results and invalid inputs. Selected C/C++/JS/TS/Java/Swift/Kotlin/Go examples compiled/executed and matched reference values. Uninstalled R/C#/Rust/MATLAB/Julia runtimes are explicitly not verified.
- New models remain function-only with fixed inputs and standard math; unsupported advanced settings are rejected. No incomplete placeholders are exported.
- Maintained HyunStudio Sponsors pending-approval state and disabled payment links; all existing calculator functionality remains.
- Full 462-way runtime verification, advanced library choice, project ZIP export and premium UI rollout remain planned.

## v1.2.0-alpha.4 — Black–Scholes, Historical VaR/ES, Moving Averages and Portfolio (2026-11-06)

- Added **DERIV-001** Black–Scholes with call/put, dividend yield and all five Greeks using a high-accuracy series standard-normal CDF in each of 13 non-Python languages.
- Added **PORT-001** weighted portfolio expected return/volatility/Sharpe with covariance dimension, symmetry and positive-definiteness checks; C uses a flattened row-major covariance input.
- Added **RISK-001** empirical signed-loss VaR and ES with linear quantile interpolation and inclusive tail rule matching the existing reference.
- Added **TS-003** full SMA/EMA calculation including output series (EMA first-value seeded; SMA only for complete windows).
- **267 / 462** source-generation combinations (33 Python plus 18 formulas × 13 additional languages); 15 formulas still Python-only, 195 cross-language adapters outstanding.
- All **104 local automated regression/generation tests** pass; selected real toolchain checks for C/C++/JavaScript/TypeScript/Java/Swift/Kotlin/Go match reference numeric cases. Other ecosystems are still unverified.
- Formula-specific advanced-structure restrictions remain fail-closed; existing calculation engine and HyunStudio Sponsors pending status remain unchanged.
- Full 462-way compiler/numeric verification, dark UI overhaul, optional advanced imports and project ZIP export remain planned rather than claimed as shipped.

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
