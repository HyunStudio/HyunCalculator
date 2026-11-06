# HyunCalculator

**v1.2.0-alpha.17** · **한국어 / English** · Desktop (Windows, macOS, Linux) · Python 3.11+

An integrated scientific, graphing, financial, quantitative finance, programmer and ML/DL/RL calculator, based on the original bilingual 19-function Tkinter calculator.

## v1.2.0-alpha.17 — Full 462-Pair Source Validation Matrix

**All 33 Financial/Quant formulas × 14 languages (462/462) now pass
the mandatory source-level compilation, typechecking or parsing gate.**

The original 363-pair compiler CI matrix now also covers:

- **Kotlin:** every generated Kotlin source compiles independently with
  `kotlinc` (**33/33**).
- **Julia:** every source passes `Meta.parseall` with Julia 1.11 (**33/33**);
  this is a parser check, not numerical execution or full type validation.
- **MATLAB target:** all 33 source files pass GNU Octave function-body
  parsing (**33/33**), performed using a non-executing wrapper. GNU Octave
  is **not** the proprietary MathWorks MATLAB runtime.

**Detected and fixed:** MATLAB output for FIN-007 CAGR used `end` as a
parameter name, which is a language keyword. It now uses
`ending_value` consistently in the generated signature and expression.
An initial Octave test mistakenly invoked input-dependent functions while
trying to parse them; the checker now calls an otherwise-empty wrapper
containing the generated functions, so calculation bodies are parsed but
not invoked.

**Evidence:** [GitHub Actions 42178554024](https://github.com/HyunStudio/HyunCalculator/actions/runs/42178554024)
passed all **14 × 33** source checks plus the existing regression, GUI,
and representative native numerical jobs. Follow-up regression tests guard
the MATLAB reserved-identifier fix. The previous **74/74 selected native
execution and invalid-input checks** remain separate and passing.

**Important limitations:** the source gate measures parse/build/type
correctness, not per-formula numerical parity. R and Julia receive parser
checks; MATLAB uses GNU Octave parsing, not commercial MATLAB. Full
462-pair execution with expected-value/boundary matrices, advanced class,
iteration and library choices, cross-platform screen-reader acceptance
and release certification remain unfinished. GitHub Sponsors approval
is still pending and no live payment control is enabled.

## v1.2.0-alpha.16 — 363-Pair Source Build/Typecheck CI Matrix

**Code generation:** unchanged at **33 formulas × 14 languages =
462/462 supported source-generation profiles**.

**New required static/build CI matrix:** ALL **33 formulas** are independently
checked in **11 languages (363/363 formula-language pairs)**, using
real installed tools and no missing-toolchain skips:

| Language | Check | Result |
|---|---|---|
| Python | `python -m py_compile` | 33/33 |
| R | `Rscript parse()` (parse only, not execution) | 33/33 |
| C | `gcc -std=c11 -pedantic-errors -fsyntax-only` | 33/33 |
| C++ | `g++ -std=c++17 -pedantic-errors -fsyntax-only` | 33/33 |
| JavaScript | `node --check` | 33/33 |
| TypeScript | `tsc --noEmit` | 33/33 |
| Java | `javac` | 33/33 |
| C# | `dotnet build`, isolated .NET 8 library per formula | 33/33 |
| Swift | `swiftc -typecheck` | 33/33 |
| Go | `go test generated.go` | 33/33 |
| Rust | `rustc --crate-type=lib --emit=metadata` | 33/33 |

**A real C# generator defect was found and repaired:** GMV (ALLOC-001)
and target-return Markowitz (ALLOC-002) initially failed C# compilation
because an emitted `Enumerable.Repeat(...).ToArray()` call omitted
a required LINQ extension namespace. The adapter now uses
`Array.Fill` and no LINQ dependency. The expanded matrix caught this,
and the corrected **363/363** checks passed in
[GitHub Actions run 42176479044](https://github.com/HyunStudio/HyunCalculator/actions/runs/42176479044).

**Scope boundary:** the 363 checks validate syntax, compilation or types,
depending on the compiler; they do **not** run every numerical algorithm.
The prior **74 native execution/edge checks** continue to pass. **Kotlin,
Julia and MATLAB/Octave** are not yet covered by the complete 33-formula
build/typecheck matrix (99 pairs), although Julia and Octave have separate
representative numerical runtime tests. Actual proprietary MATLAB has
not been run. Full 462-way numerical parity, advanced generator options,
screen-reader acceptance and release hardening remain open.

## v1.2.0-alpha.15 — MATLAB-Compatible Octave Runtime & Edge Cases

The Formula to Code engine still exports **33 Financial/Quant formulas × 14
languages (462/462 generated source combinations)**. The mandatory CI
now checks selected source on **eight executable target/runtime families**:
C, C++, JavaScript, Rust, R, C# (.NET 8), Julia, and **GNU Octave**,
which runs source generated under the **MATLAB** target.

The Octave job installs `octave` on Ubuntu, requires `octave-cli`, and
runs **17 tests**: 9 distinct MATLAB-formula source examples with
independently compared Python reference outputs, 5 additional numerical
boundary/variant inputs, and 3 negative-input checks that assert expected
guard errors (not just any compiler/parser failure). Covered formulas:
FIN-001, FIN-005, FIN-006, DERIV-001, BOND-002, RISK-002, RISK-003,
STAT-001, STAT-002. Extra checks cover zero-rate loans, zero-coupon
bonds, put Greeks, lower normal quantiles, zero volatility and invalid
IRR/normal/loan arguments.

**CI verification summary:** prior **57 representative native numerical
cases** + **14 valid Octave numeric inputs** + **3 Octave rejection cases**
= **74 native execution checks, 74/74 passing** in
[GitHub Actions run 42174610695](https://github.com/HyunStudio/HyunCalculator/actions/runs/42174610695).
Both Python 3.11 and Python 3.12 regressions (154 tests each) and the
Xvfb/Tk accessibility smoke passed. This covers **66 distinct
formula-language/runtime sample pairs** including nine Octave cases,
plus variant and rejection checks; it does **not** certify the full
462-pair source-generation matrix or every input boundary case.

**Important distinction:** GNU Octave is a MATLAB-compatible open-source
interpreter; **commercial MathWorks MATLAB itself has not been run**.
Compatibility differences, platform accessibility acceptance and further
numeric/regression edge coverage remain outstanding. GitHub Sponsors
approval is pending; unverified donation/payment buttons remain disabled.

## v1.2.0-alpha.14 — R/C#/Julia Numerical CI and Responsive Codegen Controls

The source generator continues to cover **462/462 Financial/Quant
formula-language combinations**. The mandatory GitHub Actions workflow now
runs **57 representative native numerical cases across seven languages**:
33 C/C++/JavaScript sample cases (11 formula IDs each), six Rust cases,
plus **six R, six C# (.NET 8) and six Julia** cases. Generated source is
actually compiled/interpreted and its numerical output is compared against
the existing Python reference functions. On initial verification, all
**57/57 native cases** passed. Python 3.11 and 3.12 unit tests and the
Xvfb GUI accessibility smoke also passed.

The R, C# and Julia checks cover the same six representative functions:
FIN-001 future value, FIN-006 loan amortization, RISK-002 normal VaR/ES,
STAT-001 normal probabilities, RISK-003 risk-performance metrics, and
BOND-002 yield to maturity. Each runtime is required in its own CI job;
a missing interpreter/compiler causes failure, never a false PASS.
The CI scripts are in `tests/toolchain_r_csharp_smoke.py` and
`tests/toolchain_julia_smoke.py`.

**Accessibility layout:** the code-generator options now use a reflowed
3+2 grid; source actions and class/rename fields occupy separate rows.
A GUI smoke asserts Generate/Copy/Save/ZIP buttons remain visible at
**175% text size in a 1200px-wide desktop window**. Use
`Ctrl+PageDown`/`Ctrl+PageUp` to navigate the ten calculator tabs.
These tests do not certify all screen readers or display settings.

**Not yet verified:** MATLAB/Octave execution; the entire 462-pair
compiler/numeric matrix, diverse edge cases, all platform-specific
accessibility behavior, and advanced class/algorithm/import controls.
No real GitHub Sponsors payment link is enabled pending account approval.

## v1.2.0-alpha.13 — Dark, Light, High-Contrast & Large-Text Accessibility Pass

**Verified CI status for alpha.13:** The source repo now runs **154 Python
unit/regression tests on Python 3.11 and 3.12** (both passing), a required
**10-tab virtual-display Tk accessibility smoke** (passing), **33 numerical
C/C++/JavaScript native cases** (11 formula samples × 3 languages), and
**six additional native Rust numerical cases** (FIN-001, FIN-005, FIN-006,
RISK-002, STOCH-001, BOND-002). The six Rust sources compiled and executed
with `rustc` and agreed with numerical reference outputs. Total required
native smoke = **39 sample cases, all passing** in
[GitHub Actions run 42171893846](https://github.com/HyunStudio/HyunCalculator/actions/runs/42171893846).
Full 462-pair runtime/edge-case certification, plus R/C#/MATLAB/Julia
verification, is still outstanding.

The desktop GUI now supports **dark (default), light and high-contrast** themes
across Tk/ttk controls, editable code, lists, scientific results and Matplotlib
graphs. Settings can be changed using the toolbar and are stored locally at
`~/.hyuncalculator/appearance.json`, with validated values and atomic writes.
No account, network connection or telemetry is involved.

**Text size:** 100%, 125% (default), 150%, 175%. Theme and text-size
changes apply without restarting the application. Keyboard shortcuts:
`Ctrl++` / `Ctrl+-` increase/decrease text size, `Ctrl+0` resets to
100%, and `Alt+Shift+H` toggles high contrast. Text/background palettes
were checked for >=7:1 WCAG contrast for main reading surfaces; code editor
and graph palettes update with theme switches.

A separate Tk/Xvfb GUI smoke tests **10 tabs, theme switching, local setting
persistence and non-compounding font sizes**. Pure headless tests cover
contrast ratios, preference validation and corrupt-file fallback.
**Accessibility is an ongoing engineering goal:** full screen-reader behavior,
150-175% layouts on every display, platform-specific widgets and keyboard-only
user acceptance still require review. Computational formulas and the 462/462
source-generator scope are unchanged. Sponsors remains pending approval.

## v1.2.0-alpha.12 — Deterministic standalone ZIP project export

**Native compiler CI:** The automated GitHub Actions workflow now runs
**11 representative formulas × 3 available toolchains (C, C++, JavaScript) =
33 independent compile/execute/numeric comparison cases**. All 33 cases
passed in the initial run, alongside 150 Python tests on each of Python
3.11 and 3.12. The 11 formulas covered by this particular CI job are
FIN-001, FIN-005, FIN-006, PORT-001, DERIV-001, ALLOC-001,
ALLOC-003, RISK-001, TS-003, STOCH-003 and BOND-002. These are
**33 verified sample combinations out of 462**, not every formula/input
edge case or full 14-language runtime certification. Other existing
optional smoke scripts remain available for more languages.

The Formula to Code GUI now includes **Project ZIP / 프로젝트 ZIP**, and the
CLI supports `--generate FORMULA_ID --language LANGUAGE --bundle OUTPUT.zip`.

A ZIP contains:
- `source/<file>`: code from the existing audited language-specific emitter;
- `manifest.json`: selected formula, source digest, options, generator version,
  and an explicit `runtime_verified: false` flag;
- `examples/sample_inputs.json`: raw field examples (not fabricated executable test vectors);
- `tests/test_integrity.py`: **offline SHA-256 source integrity test** and
  Python syntax parsing when applicable;
- `README.md`: toolchain guidance and numerical-verification warnings;
- `requirements.txt` for Python (inferred from actual NumPy/SciPy source imports),
  plus relevant small language project files for JS, TS, Go or C#.

```bash
python -m hyuncalculator --generate FIN-005 --language Python --bundle irr_project.zip
python -m hyuncalculator --generate ALLOC-003 --language C++ --bundle bl_project.zip
python -m hyuncalculator --generate STAT-001 --language Java --bundle normal_project.zip
```

ZIP entry names are fixed and validated, and archive timestamps, ordering and
metadata are deterministic. Tests verify archive reproducibility, source digests,
language-specific scaffolding, unsafe identifier rejection and CLI conflict
handling. The bundled integrity test intentionally **does not execute generated
financial code or claim numerical/algorithm certification**; use a verified
reference and the appropriate external compiler/toolchain before production.
All **462/462 source combinations** remain supported, but **full compiler and
numeric validation across 14 languages is still incomplete**. Premium dark
GUI redesign and advanced structure/algorithm/import selection also remain pending.

## v1.2.0-alpha.11 — 462/462 formula-language source combinations (alpha)

**All 33 registered Financial/Quant formulas** now have source-generation
profiles in **all 14 programming languages**, totaling **462/462** combinations.
**This is SOURCE GENERATION coverage, not full runtime/compiler certification.**
The calculator still uses the original standalone Python reference implementations.

Newly added cross-language profiles (13 non-Python targets each):

- **STAT-001 — normal distribution:** z-score, PDF, CDF, survival and arbitrary
  probability quantile. Uses a standard five-term CDF approximation
  (typical absolute error below 8e-8) and Acklam inverse-normal approximation
  (typical z error approximately 1e-9). For extreme tails precision should be
  checked against SciPy; Python export retains the SciPy reference.
- **STAT-002 — sample covariance and correlation:** >=3 observations and >=2
  assets; sample covariance with ddof=1. Non-Python output is a flattened
  row-major array of 2*n_assets*n_assets numbers: covariance then correlation.
  A zero-variance column gives NaN correlations. C accepts row-major flat
  input and a caller-provided output buffer; no data are read from the web.
- **RISK-003 — return performance:** annualized arithmetic return, sample
  volatility, annualized Sharpe and Sortino, maximum drawdown and compounded
  total return, with period-specific decimal risk-free rate.
- **STRAT-002 — educational cost-aware single-asset backtest:** signals
  shifted by one return period to avoid lookahead; commissions/slippage in bps
  charged on absolute executed turnover; no final liquidation or financing.
  Non-Python flat result has **12 summary metrics + n delayed positions +
  n net returns + (n+1) equity + (n+1) buy-and-hold equity**, total **4*n+14**.

New portable profiles currently support **function/auto/standard imports**
with fixed parameter names. Unsupported combinations are rejected rather than
silently translated. R/C#/Rust/MATLAB/Julia sources are **not runtime-tested** in
this environment; selected representative **C/C++/JavaScript/TypeScript/Java/
Swift/Kotlin/Go** examples compiled/ran and agreed numerically with NumPy/SciPy
references. These tests do not cover all 462 combinations or all edge cases.

**Remaining before a stable v1.2.0:** full compiler/runtime and numerical matrix,
advanced class/loop/library options on all formulas, source/test ZIP project
exports, premium dark UI/UX and broader accessibility acceptance tests.
**HyunStudio GitHub Sponsors is still approval-pending**; payment and donation
controls stay inactive until approval and destination verification.

## v1.2.0-alpha.10 — IRR and Amortization in 14 Languages (partial implementation)

Formula to Code now exports **all 33 Financial/Quant functions in Python**, and
**29/33 formulas in each of the other 13 languages**: **410/462 source-generation
pairs (88.7%)**. **Four formulas remain Python-only (52 non-Python pairs).**

New portable functions in the 13 non-Python languages:

- **FIN-005 — Internal Rate of Return (IRR):** preserves the v1.1 philosophy
  of requiring cash flows of both signs and rejecting **multiple sign-changing
  IRRs**. Uses a bounded 680-point rate grid from **-99.99% to 10000000%**
  (decimal rate range [-0.9999, 100000]) and 120 bisection steps per bracket.
  This is a **finite scan**, not a proof of mathematical root uniqueness; even-
  multiplicity or off-grid roots can be missed. Maximum 10,000 cash flows.
  C/Go/Rust/Swift return **NaN** for invalid or ambiguous inputs; exception-based
  languages use their native error mechanism.
- **FIN-006 — Selected Loan Amortization Period:** computes periodic payment,
  interest paid, principal paid and remaining balance for a selected installment.
  Enforces principal ≥ 0, rate > -100%, n ≥ 1, and 1 ≤ period ≤ n; has a
  dedicated zero-interest branch. Portable result order is
  `[payment, interest, principal_paid, remaining_balance]` (C returns
  `HyunLoanResult`). Rates are **per payment period** as decimals, not APR.

**Options:** these new adapters permit function architecture, automatic
iteration, canonical variable names and standard math imports; unsupported
class/forced-loop/variable-rename requests fail explicitly. Python retains
the original `numpy/scipy` implementation and named results.

**Validation:** selected standalone examples in **C, C++, JavaScript,
TypeScript, Java, Swift, Kotlin and Go** compiled and numerically matched
reference results for standard inputs. **R, C#, Rust, MATLAB and Julia**
emit source but are not runtime-verified here. This does not establish
full correctness for all 410 generated combinations, rate ranges or edge cases.
Additional unit tests and an optional `tests/toolchain_finance_smoke.py` script
are included. The 462-way runtime matrix, premium dark UI redesign and
advanced code/import/project-bundle options remain incomplete.

## v1.2.0-alpha.9 — Three stochastic path models in 14 languages (partial implementation)

HyunCalculator Formula to Code now exports **all 33 Financial/Quant formulas in Python**,
and **27/33 formulas in each of the 13 other languages**: **384 / 462**
formula-language source-generation pairs (**83.1%**). The remaining six
formulas are Python-only (**78 non-Python pairs**).

New 14-language stochastic path generators (Python support already existed):

- **STOCH-003** — arithmetic Brownian motion, drifted terminal mean and
  sample standard deviation, and first simulated path.
- **STOCH-004** — exact-step GBM with theoretical terminal moments, terminal
  Monte Carlo mean/SD and one complete price trajectory.
- **STOCH-005** — exact-discretization Ornstein–Uhlenbeck mean reversion,
  theoretical moments, simulated terminal statistics and one state trajectory.

For **13 non-Python targets**, these standalone implementations use the same
*Park–Miller 16807 + Box–Muller* generator, traversing paths before time steps;
the **original Python** implementation retains NumPy `default_rng`, and matching
seeds **will not produce identical paths across Python and portable targets**.
Input restrictions: `years >= 0`, integer `steps` 1..5000, integer `paths`
2..100000, `steps * paths <= 2,000,000`, portable integer `seed` 1..2147483646,
nonnegative diffusion/volatility, positive GBM spot and positive OU speed.
Non-Python return contract is a **flat numeric array**:
`[theory_mean, theory_sd, simulated_mean, simulated_sd, path_at_t0, ..., path_at_tN]`
(length **steps+5**). C returns a fixed-capacity `HyunPathResult` struct with
`length=0` on invalid input; other languages use their documented native error
handling. For non-Python, only function structure, automatic iteration, canonical
variable names and standard math libraries are currently supported.

**Verification:** **131 local Python unit/regression/codegen tests passed**;
all 42 new language-formula source outputs were generated. Representative
standalone samples for **C, C++, JavaScript, TypeScript, Java, Swift and Kotlin**
compiled/executed and agreed numerically with an independent common-RNG model.
**Go, R, C#, Rust, MATLAB and Julia generated sources remain runtime-unverified
in this run** (Go's verification attempt exceeded the environment time limit).
These are source-generator coverage claims, **not** certification of all
384 source combinations or all input domains.

~~~bash
python -m hyuncalculator --generate STOCH-003 --language C++ --output brownian.cpp
python -m hyuncalculator --generate STOCH-004 --language TypeScript --output gbm.ts
python -m hyuncalculator --generate STOCH-005 --language Swift --output ou.swift
~~~

**Still planned:** the remaining six Python-only models across 13 non-Python
targets, full toolchain/numeric CI, advanced algorithm and import selection,
complete project ZIP export and premium visual redesign. HyunStudio GitHub Sponsors
remains **approval pending**; no donation or unverified payment link is active.

### Previous: v1.2.0-alpha.8 — Monte Carlo option code generation

The existing HyunCalculator retains **33 Financial/Quant calculator operations** and
all previous UI tabs. Formula to Code now emits standalone **Python for 33/33**
formulas and source for **24/33 formulas in all 14 target languages**: Python,
R, C, C++, JavaScript, TypeScript, Java, C#, Swift, Kotlin, Go, Rust, MATLAB,
and Julia. This is **345 of 462 source-generation pairs (74.7%)**; **9 formulas
remain Python-only**, with **117 non-Python pairs still to implement**.
Unsupported language/formula and advanced-option combinations fail explicitly.

### New in alpha.8: Antithetic Monte Carlo option (DERIV-003)

`DERIV-003` generates standalone European call/put option Monte Carlo pricing code
in **all 14 languages**, including GBM terminal price simulation, antithetic
standard-normal pairs, standard error estimated across *pair means* (`ddof=1`),
and a two-sided normal-approximation 95% confidence interval.

- The **13 non-Python code generators** use the shared *Park–Miller 16807*
  31-bit linear congruential RNG with *Box–Muller* normal transforms for
  deterministic cross-language reproductions. Require integer `seed` in
  **1..2,147,483,646**; `paths` must be **even, 100..1,000,000**.
- **Python retains the original NumPy `default_rng` generator**, as in v1.1.0.
  Consequently **the same seed does not produce the same sample path between
  Python and the other languages**. Mathematical estimator/discounting/paired
  confidence interval semantics agree, but numerical estimates only agree
  statistically. The portable implementation is a reproducible educational
  RNG, **not cryptographic or suitable for production trading**.
- Non-Python output order: `[price, paired_se, ci_lower, ci_upper]`.
  C returns `HyunMCResult` with named members. Python returns its original
  named dictionary. Invalid input handling varies by language (e.g., exception
  or NaN result); see generated signatures and comments.
- Function structure + `iteration=auto` + standard math imports are supported
  for the 13 portable adapters; class/loop forcing/parameter renaming remain
  unavailable there. The generated samples use one scalar time-to-maturity
  transition (no intermediate path trace or American exercise simulation).
- **125 Python unit/regression/generator tests pass locally.** Real representative
  source executions for **C, C++, JavaScript, TypeScript, Java, Swift, Kotlin
  and Go** matched an independent Python implementation of the common portable
  RNG for 4,000-path sample(s); other toolchains **R, C#, Rust, MATLAB, Julia**
  were not available for runtime verification. This is source-generation
  coverage, **not** 345-pair full compiler/numerical certification.

~~~bash
python -m hyuncalculator --generate DERIV-003 --language C++ --output monte_carlo.cpp
python -m hyuncalculator --generate DERIV-003 --language Java --output GeneratedCalculator.java
python -m hyuncalculator --generate DERIV-003 --language Python --output monte_carlo.py
~~~

### Previously added in alpha.7: Black–Litterman (ALLOC-003)

`ALLOC-003` now generates self-contained source for all 14 languages, with
**market equilibrium returns**, **posterior expected returns**, and the
**posterior predictive covariance matrix**, preserving the existing
`hyuncalculator.quant.black_litterman` model.

- Required inputs: symmetric positive-definite `cov` (n × n), market weights
  summing to approximately 1, positive risk aversion `delta` and prior scale
  `tau`, view matrix `p` (m × n), view returns `q` (m), and strictly positive
  diagonal view variances `omega` (m). Standalone non-Python versions limit
  2 ≤ n ≤ 128 assets and 1 ≤ m ≤ 128 views.
- Non-Python output is a **flat numeric vector of length `2*n + n*n`**:
  `[prior(n), posterior(n), posterior predictive covariance (n*n, row-major)]`.
  Python retains the calculator's **named dictionary** output. C uses flat
  row-major input arrays and a **caller-owned output buffer** of sufficient
  length, returning `0` on success and `-1` on failure; Go returns `nil`,
  Rust returns `Result`, and Swift throws on invalid inputs.
- No matrix inversion is used in generated C/C++/JS/TS/Java/C#/Swift/Kotlin/Go/Rust;
  triangular Cholesky solves compute the posterior. R/MATLAB/Julia use
  built-in SPD-validated linear solves. Only the function/automatic iteration
  and standard import profile is supported for non-Python export.
- The **119 automated local tests pass**. Representative C, C++, JavaScript,
  TypeScript, Java, Swift, Kotlin and Go generated programs compiled or ran
  successfully and matched the Python reference for the 2-asset/1-view
  example. R, C#, Rust, MATLAB and Julia are **generated but NOT
  runtime-verified** here. Larger inputs, alternative view matrices, platform
  differences and non-Python edge cases require more testing.

~~~bash
python -m hyuncalculator --generate ALLOC-003 --language Java --output GeneratedCalculator.java
python -m hyuncalculator --generate ALLOC-003 --language C++ --output bl.cpp
~~~

### Previously available in 14 languages — Markowitz allocation

| Formula ID | Model | Computation and restrictions |
| --- | --- | --- |
| `ALLOC-001` — `qf_gmv` | Global Minimum Variance (Markowitz) | Fully-invested minimum-variance portfolio, unrestricted short-selling; solve Σ·x=1, normalize weights; compute portfolio variance |
| `ALLOC-002` — `qf_target` | Minimum Variance with Target Return | Fully-invested weights constrained to a requested expected return; solve Σ·x=1 and Σ·z=μ using Cholesky, then solve 2×2 Gram system; return realized expected return |

Both adapters require a **finite, symmetric, positive-definite covariance matrix**,
at least two assets, and matching dimensions. The target-return formulation
requires meaningfully distinct expected returns. Numerical inversion is avoided:
all standalone non-Python generated code uses Cholesky triangular solves,
except R, MATLAB and Julia, which use native SPD-validated linear-system solvers.
No transaction costs, leverage limits, box constraints, long-only weights or
portfolio rebalancing are modeled by these two formula IDs.

**Output convention:** for non-Python target languages, the returned vector has
**n+1** values: `[weight_1, ..., weight_n, portfolio_variance]` (GMV) or
`[weight_1, ..., weight_n, realized_expected_return]` (target return). Python
keeps the reference **named dictionary** convention. C specifically takes a
row-major `cov` array and a **caller-provided output buffer of length >= n+1**;
it returns `0` for success and `-1` for invalid inputs. Java and C# expose
static class methods; Swift returns `throws`, Rust returns a `Result`, and Go
returns `nil` for invalid inputs. Check the generated signature before use.

**Options:** these new non-Python profiles support `structure=function`,
`iteration=auto`, `imports=auto/standard`, fixed input names, and a configurable
safe function name. Unsupported class architecture, loop-forcing, import packs,
field renaming and irrelevant formula variants are rejected, not silently ignored.

**Previous alpha.6 verification:** **114 local Python unit/regression/generator tests passed**.
The current 345 enabled source-generation pairs are covered by generation tests. Representative
C, C++, JavaScript, TypeScript, Java, Swift, Kotlin and Go generated programs
were compiled and executed with matching numerical reference values for both
new Markowitz models. **R, C#, Rust, MATLAB and Julia source files were generated
but not executed here**; neither their compilation nor their numerical accuracy
should be regarded as verified. See `tests/toolchain_allocation_smoke.py` for
the optional real-toolchain checks. Input conditioning, large matrices and
cross-platform numerical stability still require deeper testing.

**Prior alpha support preserved:** financial TVM, Black–Scholes/Greeks and IV,
normal/historical VaR-ES, portfolio statistics, SMA/EMA, bonds/YTM, EWMA,
GARCH, GBM/OU moments and transaction costs. Other Financial/Quant formulas
remain exportable to Python; ML/DL/RL, Scientific, Graphing and Programmer
calculator functionality remains available.

**Not yet complete:** remaining 117 non-Python formula-language pairs, exhaustive
462-pair compile/run/numeric verification, advanced algorithm/import choices,
reusable ZIP project bundles and premium dark UI redesign. See the
[v1.2 technical design](docs/FORMULA_TO_CODE_V1_2_DESIGN.md). The creator
is 황현기 / HyunGi Hwang (HyunStudio); **GitHub Sponsors is still pending
approval** and no payment/donation link is activated.

### CLI examples / 코드 생성 예제

~~~bash
python -m hyuncalculator --list-formulas
python -m hyuncalculator --generate ALLOC-001 --language C++ --output gmv.cpp
python -m hyuncalculator --generate ALLOC-002 --language Java --output GeneratedCalculator.java
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
remaining 117 source-generation combinations, systematic toolchain testing,
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
