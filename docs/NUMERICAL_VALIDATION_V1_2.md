# HyunCalculator v1.2 numerical validation ledger

## Current alpha.19 runtime matrix

The required suites now execute all 33 catalog IDs per target.

| Targets | Unique formula/target pairs | Runtime |
|---|---:|---|
| Python | 33 | Python, compared with original calculator samples |
| C, C++, JavaScript | 99 | gcc / g++ / Node |
| TypeScript, Java, Swift, Kotlin, Go | 165 | tsc + Node / JVM / Swift / JVM / Go |
| R, Julia, Rust, C# | 132 | Rscript / Julia / rustc / .NET |
| **13 native targets** | **429** | Representative valid inputs |
| MATLAB source target | 33 | **GNU Octave compatibility runtime** |

This is not 462-pair licensed native execution: proprietary MathWorks MATLAB
has not been run. All cases check complete numerical outputs with finite-value
and shape validation. Stochastic results use independent portable PRNG references.
Individual tolerances remain model-specific; these representative cases do not
prove all ranges, precision, convergence or extreme-tail behavior.

`toolchain_extended_full_numeric.py` covers five extra targets;
`toolchain_catalog_numeric.py` covers R/Julia/Rust/C#/Octave. The latter also
supports a manually invoked `MATLAB` argument when a licensed local executable
is available. `test_numeric_properties.py` adds seeded time-value identities,
put-call parity, shared Greeks, covariance allocation constraints and rejected
invalid inputs in generated Python/JavaScript. These extra variants and
class-option tests are deliberately excluded from the unique-pair counts.

New runtime checks discovered two Julia emission errors (CAGR reserved argument
and implied-volatility ternary spacing). The historical Julia Meta.parseall
gate returned error expressions without rejecting them; alpha.19 recursively
rejects those expressions. Earlier 462/462 source-check results should be read
as the old gate outcome, not proof that those Julia sources were executable.

## Historical alpha.18 snapshot


**Snapshot:** v1.2.0-alpha.18, 2026-11-06.

This document separates **source generation**, **syntax/build/type checks**
and **executed numerical verification**. None of these alone establishes
financial-production certification, complete numerical equivalence, or
correctness for every possible input.

## 1. Source-level catalog (all 33 × 14 targets)

- **462/462** formula-language pairs emit standalone code.
- **462/462** emitted sources pass their CI's language-appropriate
  syntax, compilation, type or parse gate.
- Python: py_compile. R: parse. C/C++: compiler -fsyntax-only.
  JavaScript: node --check. TypeScript: tsc --noEmit.
  Java: javac. C#: .NET build. Swift: swiftc -typecheck.
  Kotlin: kotlinc. Go: go test. Rust: rustc emit metadata.
  Julia: Meta.parseall. MATLAB target: GNU Octave parsing only.
- A successful parser check does **not** imply native execution,
  type safety or numerical validity. Licensed MATLAB has not been run.

## 2. Mandatory native numerical runtime and validation checks

| Runtime(s) | Distinct formula IDs per runtime | Executed valid numeric cases | Invalid-input guard cases |
|---|---:|---:|---:|
| C, C++, JavaScript (common matrix) | 27 each (81 pairs) | 81 | 0 |
| JavaScript (remaining models) | 6 (6 pairs) | 6 | 3 |
| Rust | 6 | 6 | 0 |
| R | 6 | 6 | 0 |
| C# / .NET 8 | 6 | 6 | 0 |
| Julia | 6 | 6 | 0 |
| GNU Octave (MATLAB target) | 9 (9 pairs) | 14 | 3 |
| **Total** | **120 distinct pairs** | **125** | **6** |

The aggregate number of executed **cases** is **131 = 125 numerical
valid-input cases + 6 invalid-input rejection cases**. Additional Octave
variants account for five valid-input cases beyond its nine distinct pairs,
and the six negative cases are three in JavaScript plus three in Octave.
These are test-case counts, **not** a claim that 131 different functions
were implemented or that 131 source combinations have multiple inputs.

### Common C / C++ / JavaScript formula IDs (27 per runtime)

FIN-001, FIN-002, FIN-003, FIN-004, FIN-005, FIN-006, FIN-007,
FIN-008, FIN-009, PORT-001, DERIV-001, DERIV-002, DERIV-003,
ALLOC-001, ALLOC-002, ALLOC-003, RISK-001, RISK-002, TS-002, TS-003,
STOCH-001, STOCH-002, STOCH-003, STOCH-004, STOCH-005, STRAT-001,
BOND-002.

### Additional JavaScript formula IDs (six)

STAT-001 (normal distribution), STAT-002 (covariance/correlation),
BOND-001 (bond duration/convexity), RISK-003 (performance metrics),
TS-001 (EWMA volatility), STRAT-002 (cost-aware backtest).

**The union is exactly the 33 registered formula IDs with no duplicates.**
This invariant is checked automatically by the CI scripts.

### Runtime test scripts

- `tests/toolchain_ci_smoke.py` (C/C++/JavaScript 81 cases)
- `tests/toolchain_js_full_numeric.py` (6 JS numeric, 3 JS guards)
- `tests/toolchain_rust_smoke.py` (6 Rust cases)
- `tests/toolchain_r_csharp_smoke.py` (6 R and 6 C# cases)
- `tests/toolchain_julia_smoke.py` (6 Julia cases)
- `tests/toolchain_octave_smoke.py` (14 numeric and 3 validation cases)
- `.github/workflows/tests.yml` runs all required jobs; missing compilers
  fail instead of silently reporting success.

## 3. Accuracy and test-design caveats

- Individual scripts use model-specific absolute and relative tolerances.
  They also check the number and order of returned fields, including
  covariance matrices, full performance series and backtest equity curves.
- For stochastic paths and Monte Carlo pricing, the thirteen non-Python
  emitters use a portable Park–Miller/Box–Muller PRNG. Their reference
  compares the **portable stream**, not NumPy's different `default_rng`
  output for an identical seed.
- No exhaustive floating-point precision, overflow, extreme-tail, dense
  matrix, convergence, long-path or invalid-input matrix is established.
- Successful execution on GNU Octave is MATLAB compatibility evidence,
  not evidence of licensed MathWorks MATLAB execution.
- Source checks cover all 462 pairs; **numerical execution has not
  verified all 462 pairs**.
- Financial models are educational/research implementations. Shorting,
  cost assumptions, portfolio constraints, statistical definitions and
  numerical approximation error should be reviewed for each use case.

## 4. Next verification priorities

1. Add a broad set of deterministic, independently computed reference
   vectors and invalid-input cases for every formula in each runtime.
2. Extend execution and numerical verification beyond the 33/33
   JavaScript formula samples, particularly to C/C++ and Python.
3. Add CI property-based and metamorphic tests for portfolio symmetry,
   Black–Scholes call-put parity, tail risk monotonicity and curve shapes.
4. Run genuine MathWorks MATLAB where licensed, and test screen-reader,
   large-text and keyboard-only workflows on Windows/macOS/Linux.
5. Treat semantic parity, numerical error budgets and user-visible
   architecture/import options as separate release gates.

GitHub Sponsors profile approval is pending; no payment action is
enabled until a verified payment destination is available.

## Follow-up: C/C++ full representative coverage

The mandatory `tests/toolchain_native_full_numeric.py` adds the six missing
formula IDs in each of C and C++: 12 planned numerical cases. Every output
field is compared with the Python references and model-specific tolerances
used by the JavaScript suite. Combined coverage must match all 33 unique
catalog IDs. Missing compilers, compilation errors and nonfinite results fail.

The alpha.18 totals above remain the historical baseline. Once the added
CI step passes, totals become 143 cases (137 numerical, 6 rejection),
132 distinct formula/runtime pairs, and 33 formulas each in C/C++/JS.
These additions do not establish exhaustive input or boundary coverage.
