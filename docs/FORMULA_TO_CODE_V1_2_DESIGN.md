# HyunCalculator v1.2.0 — Formula to Code Generator 기획·기술 설계서

> 문서 상태: **DESIGN / PARTIALLY IMPLEMENTED (v1.2.0-alpha.17)**  
> 작성일: 2026-11-06  
> 프로젝트: [HyunStudio/HyunCalculator](https://github.com/HyunStudio/HyunCalculator)  
> 기준 버전: **v1.1.0** (현재 계산 엔진 유지)  
> 목표: 금융수학·금융공학 **기존 33개 등록 계산 기능 × 14개 프로그래밍 언어 = 462개 생성 조합**  
> **주의:** 본 문서는 개발 범위와 검증 기준을 규정하는 설계서이며, 코드 생성기 구현·컴파일·런타임 검증이 완료되었다는 뜻이 아니다.

### Implementation status — 2026-11-06 (v1.2.0-alpha.17)

- **Source generation:** all **462/462** formula-language pairs are supported (33 formulas × 14 targets).
- **Mandatory 14-language source-validation matrix:** all **462/462 source-level parse/build/type checks passed**. Previously checked 11 languages (363 pairs) plus newly added **Kotlin / Julia / MATLAB target under GNU Octave (99 pairs)**. Kotlin is fully compiled with `kotlinc` for each formula; Julia is parsed via `Meta.parseall`; Octave parses all MATLAB functions without executing financial calculations. R remains syntax-parse only. Other languages use the documented compilers, syntax or typecheck commands.
- **Defect discovered:** FIN-007 MATLAB CAGR generated a parameter literally called `end`, a reserved MATLAB keyword. Scalar source emitter now consistently renames this parameter to `ending_value` for MATLAB, leaving other language contracts unchanged.
- **Checker correction:** plain Octave `source()` ran function bodies without parameters. The checker now creates and invokes an otherwise-empty wrapper containing the generated definitions, forcing parse without invoking them. Octave remains only a MATLAB-compatible alternative, not proof of licensed MathWorks MATLAB compatibility.
- **Verified code-run evidence:** [GitHub Actions run 42178554024](https://github.com/HyunStudio/HyunCalculator/actions/runs/42178554024) succeeded for all 14 language matrix jobs and established Python, GUI, native smoke jobs. Prior **74 selected native numerical/negative-input execution checks** remain passing and separate from static-source checks.
- **Not complete:** full numerical execution for all 462 pairs, input-edge-value matrices, all platform/screen-reader accessibility acceptance, unrestricted class/loop/import options and production-grade financial certification.
- **Sponsors:** approval pending; no active/unverified donation links or payment actions.
- This is an alpha implementation progress record, not a declaration of finished v1.2.0. See [README](../README.md) and [CHANGELOG](../CHANGELOG.md).

## 1. 목적과 핵심 원칙

사용자가 HyunCalculator에서 수식을 선택하거나 계산한 뒤, 선택한 언어와 구현 옵션에 맞는 **실행 가능한 소스코드, 실행 예제, 테스트, 의존성 안내**를 생성한다.

1. **수학적 동등성 우선:** 화면 계산기와 생성 코드가 같은 입력 규칙, 계산 정의, 예외 조건 및 수치 허용 오차를 사용해야 한다.
2. **33개 전체 커버리지:** 현재 GUI에 등록된 Financial 9개와 Quant 24개를 *각각* 독립적인 코드 생성 대상으로 등록한다. 10개 분류는 탐색용; 실제 커버리지는 33개 기능 단위로 검증한다.
3. **14개 언어:** Python, R, C, C++, JavaScript, TypeScript, Java, C#, Swift, Kotlin, Go, Rust, MATLAB, Julia.
4. **구조와 알고리즘을 분리:** Class, Function, Script는 코드 구성 방식; for, while, vectorized, analytic은 계산 구현 방식이다. 한 옵션 그룹처럼 취급하지 않는다.
5. **자동 추천 + 수동 선택:** 수식/언어별 유효 조합만 표시하고, 불가능하거나 검증되지 않은 조합은 명확히 설명한다.
6. **허위 성공 금지:** 생성됨, 정적 검사 통과, 컴파일 통과, 실행값 검증 통과를 별도 상태로 표시한다. 미설치 컴파일러를 이유로 미검증한 경우 PASS로 처리하지 않는다.
7. **기존 기능 비파괴:** v1.1.0 Scientific, Graphing, Financial, Quant, Programmer 및 기존 ML/DL/RL 19개 기능·한영 전환·기존 테스트 유지.
8. **연구 및 교육 목적:** 실시간 시세 수집, 주문 실행, 다중 자산/이벤트 기반 실거래 백테스트, 미국형 옵션 프라이싱은 이 단계 범위 밖이다.

## 2. 현행 코드와 정확한 커버리지 기준

기준 소스:
- hyuncalculator/operations.py — 사용자 선택 메뉴, 한영 레이블 및 33개 계산 함수 등록
- hyuncalculator/finance.py — 금융 계산의 Python 원본 정의
- hyuncalculator/quant.py — 금융공학 계산의 Python 원본 정의
- hyuncalculator/gui.py — Tkinter UI
- tests/test_calculators.py, tests/test_quant_extended.py — 현행 테스트
- README.md, CHANGELOG.md — 모델 가정과 기존 제한

### 2.1 10개 영역 / 33개 Formula ID 레지스트리 초안

Formula ID는 v1.2.0부터 **안정적인 공개 식별자**로 고정한다. 왼쪽 ID → 기존 구현 함수의 일대일 매핑이 기본이며, 복수 영역에서 검색될 수 있는 함수는 태그로 교차 참조한다.

| 영역 | Formula ID — 기존 함수 | 생성 대상 내용 |
|---|---|---|
| 금융수학 (9) | FIN-001 — fin_fv | 이산/연속 복리 미래가치 |
| 금융수학 | FIN-002 — fin_pv | 현재가치 |
| 금융수학 | FIN-003 — fin_pmt | 원리금균등 상환액 |
| 금융수학 | FIN-004 — fin_npv | 순현재가치 |
| 금융수학 | FIN-005 — fin_irr | 내부수익률 수치 해법 |
| 금융수학 | FIN-006 — fin_loan | 회차별 이자/원금/잔액 |
| 금융수학 | FIN-007 — fin_cagr | 연평균 성장률 |
| 금융수학 | FIN-008 — fin_effective | 실효 연이율 |
| 금융수학 | FIN-009 — fin_annuity | 보통연금 현재가치 |
| 확률·통계 (2) | STAT-001 — qf_normal | 정규분포 PDF/CDF/분위수 |
| 확률·통계 | STAT-002 — qf_cov | 표본 공분산/상관계수 |
| 포트폴리오 (1) | PORT-001 — qf_portfolio | 가중 기대수익률/변동성/Sharpe |
| 자산배분 (3) | ALLOC-001 — qf_gmv | 전역 최소분산 |
| 자산배분 | ALLOC-002 — qf_target | 목표수익률 제약 Markowitz |
| 자산배분 | ALLOC-003 — qf_bl | Black–Litterman 사후 기대수익률 |
| 파생상품 (3) | DERIV-001 — qf_bs | 유럽형 Black–Scholes/Greeks |
| 파생상품 | DERIV-002 — qf_iv | 내재변동성 역산 |
| 파생상품 | DERIV-003 — qf_mc | 유럽형 옵션 몬테카를로 |
| 채권 (2) | BOND-001 — qf_bond | 고정쿠폰채 가격/듀레이션/컨벡서티 |
| 채권 | BOND-002 — qf_ytm | Dirty price → 명목 YTM 역산 |
| 리스크 관리 (3) | RISK-001 — qf_hist_var | 과거 손실 VaR/ES |
| 리스크 관리 | RISK-002 — qf_normal_var | 정규 가정 VaR/ES |
| 리스크 관리 | RISK-003 — qf_performance | Sharpe/Sortino/MDD 및 성과 |
| 시계열 분석 (3) | TS-001 — qf_ewma | EWMA 변동성 |
| 시계열 분석 | TS-002 — qf_garch | GARCH(1,1) 1스텝 분산 예측 |
| 시계열 분석 | TS-003 — qf_moving | SMA/EMA |
| 확률과정 (5) | STOCH-001 — qf_gbm | GBM 이론 모멘트 |
| 확률과정 | STOCH-002 — qf_ou | OU 이론 모멘트 |
| 확률과정 | STOCH-003 — qf_brownian | Brownian/산술 BM 경로 |
| 확률과정 | STOCH-004 — qf_gbm_paths | GBM 경로 시뮬레이션 |
| 확률과정 | STOCH-005 — qf_ou_paths | OU 경로 시뮬레이션 |
| 퀀트 전략 (2) | STRAT-001 — qf_cost | 수수료/슬리피지/반 스프레드 비용 |
| 퀀트 전략 | STRAT-002 — qf_backtest | 비용 차감 단일 자산 전략 백테스트 |

검증: 9 + 2 + 1 + 3 + 3 + 2 + 3 + 3 + 5 + 2 = **33**. Monte Carlo는 확률·통계 태그도 부여하고, RISK-003은 포트폴리오·전략 태그도 부여하여 중복 구현 없이 검색 가능하게 한다.

**범위 해석:** 현재 v1.1.0이 계산하는 기능의 **현행 의미**를 이식한다. 예컨대 미국형 옵션·공매도 금지 Markowitz·전체 GARCH 모수 추정·다중 자산 이벤트 엔진 등 신규 모델을 33개에 임의로 포함하지 않는다.

## 3. 지원 언어 매트릭스

모든 Formula ID를 아래 14개 대상 언어의 생성·검증 매트릭스에 등록한다. 플랫폼/런타임이 없는 환경에서 미실행된 출력은 '검증 대기'로 표시한다.

| 언어 | 소스 확장자 | 가능한 기본 형태 | 빌드/테스트 어댑터 예시 |
|---|---|---|---|
| Python | .py | function / class / module | python, unittest/pytest |
| R | .R | function / script / 선택적 R6 class | Rscript, testthat |
| C | .c + .h | function / struct+function (C에는 class 없음) | gcc/clang |
| C++ | .cpp + .hpp | function / class | g++/clang++ |
| JavaScript | .js | function / class / module | Node.js |
| TypeScript | .ts | function / class / module | tsc + Node.js |
| Java | .java | static method / class | javac/java |
| C# | .cs | static method / class | dotnet |
| Swift | .swift | function / struct / class | swiftc |
| Kotlin | .kt | top-level function / object / class | kotlinc |
| Go | .go | function / struct+method | go test |
| Rust | .rs | function / struct+impl | cargo test |
| MATLAB | .m | function / script / classdef | MATLAB + toolbox 확인 |
| Julia | .jl | function / module / struct+methods | julia + Test |

지원 불가 구조는 **지원되는 의미적으로 동등한 표현으로 안내하거나 명시적으로 비활성화**한다. 예: C class 선택 금지, Go/Rust의 'class'는 struct+method로 매핑, R6/MATLAB toolbox는 사용 가능 여부를 별도 검증. 지원 여부를 속이기 위한 빈 템플릿 출력 금지.

## 4. 사용자 워크플로 및 UI/UX

### 4.1 진입점

A. 현재 Financial/Quant 계산 항목 → **'코드 생성 / Generate Code'** 버튼: 현재 Formula ID, 입력값, 한국어/영어 설정을 코드 생성 화면에 전달.  
B. 좌측 **Formula to Code** 메뉴 → 영역/수식 검색 후 선택.  
C. 내보내기된 프로젝트의 manifest를 가져와 옵션 재편집(후속 단계).

### 4.2 단계별 화면

1. **Formula Library:** 10개 영역, 키워드/ID 검색, 수식 설명, 입력변수·단위·제약, 기존 구현 링크.
2. **Target Languages:** 기본 1개 언어 선택, 최대 14개 다중 선택, 상태표(지원/미지원/미검증).
3. **Implementation Options:** Auto / Advanced; 함수/클래스/모듈, 함수명·변수명, 알고리즘, 루프, 의존성, 자료형, 성능, 에러 처리 및 주석.
4. **Preview:** 원본 수학식, 선택된 옵션, 실제 생성 소스코드, 변경 내용 및 라이브러리 manifest를 나란히 표시.
5. **Validate:** 파싱→정적 검사→컴파일→예제 실행→기준값 비교의 상태와 로그, 실패 위치·원인·재시도 안내.
6. **Export:** 개별 파일/언어별 프로젝트/14개 언어 모음 ZIP, 테스트 데이터, README, 버전·검증 기록.

### 4.3 Advanced 옵션 (각각 독립)

| 축 | 옵션 | 규칙 |
|---|---|---|
| 코드 구성 | function, class, module, script, 언어별 구조체/메서드 | 언어의 문법/제약을 반영 |
| 함수·클래스·변수명 | 자동 생성/수동 입력 | Unicode 처리·예약어·식별자 정규화·충돌 검증 |
| 계산 전략 | analytic, root-finding, optimization, simulation, streaming/rolling | 해당 수식과 검증된 알고리즘 후보만 노출 |
| 반복 구현 | auto, for, while, vectorized, library-call | 알고리즘에 반복이 필요한 경우만 활성화 |
| Import 전략 | auto, standard-only, numerical-library | 필요한 의존성만; 표준 라이브러리로 불가능할 경우 이유 제공 |
| 수치 표현 | float64 기본, float32, decimal/고정소수, vector, matrix | 알고리즘/언어/정확도 제한 사전 검사 |
| 최적화 | readability, speed, memory | 실행 결과 동등성 유지 |
| RNG | seed, algorithm, common random samples | 시뮬레이션의 재현성·언어 간 비교 보장 정책 명시 |
| 오류 처리 | domain, shape, overflow, convergence, finite-check | 끌 수 없는 수학적 필수 검증 존재 |
| 주석·타입 | 한영 주석, 타입 선언, docstring, 수식 출처 | 결과물 문서화 옵션 |
| 테스트 | golden, boundary, property, cross-language | 모든 생성 출력에 최소 golden test 의무 |

'for/while'은 'class/function'과 별개이다. 예: 'Class + for + NumPy'도 유효하다. 특정 수식이 명시적 해석해인데 for를 강제하도록 허용하지 않는다. 알고리즘을 바꾸면 출력의 수학적 정의를 유지한 채 구현 방법만 변경한다.

### 4.4 공통 디자인/접근성

기존 HyunCalculator 프리미엄 다크 UI 시안의 색상·레이아웃을 바탕으로, **Light / Dark / High-contrast**, 한·영 전환, 14–20pt 이상 조절 가능한 글자, OS 돋보기 호환, 200% UI 확대, 키보드만으로 선택·코드 복사·내보내기, 포커스 표시, 오류 메시지 텍스트/스크린리더 지원을 목표로 한다. 긴 코드·테이블에는 별도 스크롤, 복사, 확대, 검색 기능 제공. 시안은 구현 완료 아님.

## 5. 아키텍처

~~~text
hyuncalculator/
  codegen/
    registry.py          # 33 canonical FormulaSpec + stable IDs
    schemas.py           # typed metadata, I/O, units, constraints, numeric policy
    parser.py            # AST whitelist / 사용자 수식 검증 (추후 사용자 수식 지원)
    ir/                  # typed, language-neutral math/algorithm intermediate representation
    algorithms/          # analytic, roots, matrix solve, optimize, series, simulation, backtest
    adapters/            # python, r, c, cpp, js, ts, java, csharp, swift, kotlin, go, rust, matlab, julia
    libraries.py         # dependency/import resolution + license metadata
    validators.py        # static checks, toolchain detection, benchmark, tolerance, audit
    exporters.py         # source/test/manifest/README/ZIP export
  ui/
    formula_to_code.py   # Tkinter screen + 14-language selector
tests/
  codegen/
    golden/              # input/output pairs and boundary cases
    integration/         # generated code compile/execute tests
    contracts/           # formula IDs, language/algorithm coverage checks
~~~

현행 operations.py는 레지스트리의 원본 설명 메타데이터로 재사용하되, 문자열 수식을 즉석 치환하는 방식으로 실행 코드를 만들지 않는다. **Typed IR**(스칼라/배열/행렬 타입, 함수 호출, 조건, 반복, 합계, 행렬 풀이, 확률 샘플링, 수치 최적화, 시간 인덱스)을 거쳐 언어별 emitter가 문법과 import를 생성한다.

### 5.1 FormulaSpec 계약

각 Formula ID에는 최소 다음 속성이 있어야 한다.

- id, domain, tags, title_ko/title_en, legacy_function, formula_latex, reference_version
- input_schema (name, type, unit, min/max/shape, example), output_schema, error_rules
- assumptions (연·월 기간, nominal/effective, decimal rate, seed, ddof, Greeks 단위 등)
- algorithm_profiles (지원 로직, 정확도/성능 트레이드오프, 선호 구현)
- language_support (supported, unsupported, planned, verified), import_capabilities
- golden_cases (정상, 경계, 오류, 상대/절대 허용 오차), numerical_invariants

예시 — 실제 파일이 아닌 계획 스키마:

~~~json
{
  "id": "DERIV-001",
  "legacy_function": "qf_bs",
  "domain": "derivatives",
  "output": {"price": "float64", "delta": "float64", "gamma": "float64", "vega": "float64"},
  "assumptions": {"exercise": "european", "rates": "annual_decimal", "vega_unit": "per_1.00_vol"},
  "implementation": {
    "language": "Python",
    "structure": "function",
    "algorithm": "analytic",
    "iteration": "none",
    "imports": "auto",
    "dtype": "float64",
    "fn_name": "black_scholes"
  },
  "tests": {"golden": true, "boundary": true, "numeric_tolerance": {"atol": 1e-8, "rtol": 1e-7}}
}
~~~

실제 스키마는 Python dataclass 또는 검증 가능한 JSON Schema 중 하나를 단일 소스로 정의하고, schema_version을 포함하여 내보내기 호환성을 관리한다.

### 5.2 수치 알고리즘 및 라이브러리 선택

- **직접 계산:** 복리·PV·CAGR·Black–Scholes. 단순 수식에 불필요한 루프 생성 금지.
- **근 찾기:** IRR, IV, YTM — 구간 탐색, 이분법/Brent 우선, 허용 오차/최대 반복/비수렴 예외 명시.
- **행렬:** Markowitz, BL — 명시적 역행렬보다는 선형 시스템 풀이 사용; 대칭성/양정치성/차원 검사.
- **시계열:** SMA/EMA/EWMA/GARCH — 순서·초기 상태·window·누락 값 처리 계약을 고정.
- **시뮬레이션:** BM/GBM/OU/MC — RNG 소스·seed·경로/시간 축·통계적 오차를 명시.
- **백테스트:** 수익률 및 신호 정렬, 포지션 1기간 지연, turnover, bps 비용, 초기 현금/에쿼티, MDD/Sharpe/Sortino 정의 통일.

언어별 후보 라이브러리(설치/라이선스는 개발 시 확인): Python math/NumPy/SciPy; R stats; C libm 및 선택적 선형대수 라이브러리; C++ 표준 라이브러리/Eigen; JS/TS Math 및 선택적 mathjs; Java Math/Commons Math; C# System.Math/Math.NET; Swift Foundation/Accelerate; Kotlin kotlin.math/수치 라이브러리; Go math/Gonum; Rust nalgebra/statrs; MATLAB 내장 함수 및 조건부 toolbox; Julia LinearAlgebra/Statistics/Distributions/Optim. **실행되는 코드와 의존성 파일을 반드시 한 세트**로 생성한다. 미지원 패키지 조합은 성공 메시지 대신 오류와 대안을 제공한다.

## 6. 정합성·테스트 전략

### 6.1 462 생성 조합 검증

33 Formula IDs × 14 languages = **462개 필수 생성 대상**. 각 조합은 최소 다음 체크를 추적한다.

1. **생성 검증:** 해당 ID의 구현 코드 + 테스트 + 사용 예제가 비어 있지 않고 생성됨.
2. **정적 검증:** 언어별 형식/파싱, import/dependency 해석 및 금지 코드 검사.
3. **컴파일/실행:** 사용 가능한 toolchain으로 최소 1개 정상 예제 실행.
4. **수학 검증:** 현행 Python 기준 구현 및 별도 수동 검산한 Golden 결과와 수치 오차 범위 내 일치.
5. **경계/예외 검증:** 음수·0·NaN/inf·차원 오류·특이행렬·최대 반복/경로 제한 등.
6. **회귀 검증:** 기존 v1.1.0 계산기 테스트 및 GUI 스모크 테스트 통과.

진행 상태: NOT_STARTED → GENERATED → STATIC_OK → BUILD_OK → NUMERIC_OK → VERIFIED. 실패/스킵/툴체인 부재는 별도 명시. 검증되지 않은 조합은 내보낼 수 있더라도 **UNVERIFIED** 경고와 로그를 표시한다.

### 6.2 불변식 / 특별 검증

- 할인·복리의 역함수 관계; zero-rate 극한, NPV/IRR 잔차.
- 정규 PDF ≥ 0, CDF 단조성, 분위수 역관계; 표본 공분산의 대칭성.
- 포트폴리오 가중치 합 1; 공분산 행렬 SPD 조건; BL 행렬 크기.
- Black–Scholes put-call parity, Greeks 단위(per 1.00 vol/rate), T=0/σ=0 처리.
- 채권 가격과 YTM의 역대입, 쿠폰 주기, dirty price 가정.
- VaR/ES의 손실 부호 및 분포 정의, 변동성/소르티노 연환산 방식.
- SMA 초기 구간, EMA 초기화, GARCH 초기 상태/안정성 조건.
- Monte Carlo의 언어별 동일 seed는 동일 결과를 보장하지 않음: **공통 표준정규 표본 주입 테스트**와 독립 RNG 기반 신뢰구간 테스트를 구분.
- 백테스트의 position[t]=signal[t-1], 최종 실행되지 않은 신호 무시, 절대 turnover 기반 거래비용, 미포함 차입비용/종료 청산비용 명시.

수치 tolerances는 공통 임의값을 고정하지 않고 Formula ID와 알고리즘·dtype별로 지정한다. 버전/OS/라이브러리별 수치 차이가 정상적인 범위인지 검증한다.

### 6.3 CI/CD

- Python 3.11/3.12 현행 CI 유지 + 레지스트리/스키마/생성기 유닛 테스트.
- 언어별 toolchain 설치 가능한 GitHub Actions 매트릭스에서 표준 라이브러리 경로 우선 검증; 비용이 큰 MATLAB 등은 별도 runner/license 가능 여부를 명시.
- 14개 × 33개 상태표를 CI 아티팩트(JSON/Markdown)로 출력; 미실행을 성공으로 표시하지 않는다.
- 코드 생성에 사용되는 사용자 식별자는 escaping/예약어 검사를 하고, 사용자가 입력한 식 또는 생성 코드를 앱 내부에서 무제한 exec/eval하지 않는다.

## 7. 코드 내보내기 계약

~~~text
HyunCalculator_CodeExport/
  manifest.json            # generator_version, formula IDs, language, options, assumptions
  formula.json             # canonical formula, inputs, outputs, units, constraints
  README.md                # run/build/test instructions and limitations
  python/ ... julia/       # 선택한 각 언어의 소스 + 의존성 파일
  tests/                   # golden vector, boundaries, examples, test runners
  validation_report.json   # generated/static/build/numeric statuses, tolerances, logs
~~~

내보내기는 한 언어/여러 언어/전체 14개, 코드 복사, 파일, ZIP 지원. 생성된 코드의 날짜·generator 버전·Formula ID·의존성 버전을 기록한다. 사용자가 바꾼 함수명/변수명과 알고리즘 옵션은 manifest에 보존한다. 자동 생성 소스의 라이선스·외부 패키지 라이선스 확인 절차 별도 마련.

## 8. 구현 단계 / Definition of Done

| 단계 | 작업 | 완료 기준 |
|---|---|---|
| P0 Registry | 33개 Formula ID/입력·출력·단위·수치 규칙 정의 | 33개 모두 원본 함수·Golden case에 연결, 누락 0 |
| P1 IR/Algorithms | Typed IR와 6가지 알고리즘 계열 정의 | 일차 수식 치환이 아닌 실행 가능 IR 및 예외 처리 |
| P2 Adapters | 14개 언어 emitter와 빌드 템플릿 | 462 조합 생성, 허용하지 않는 선택은 명시적 오류 |
| P3 UI | 한영 Formula Library / Auto·Advanced / Preview / Export | 기존 8탭 손상 없이 접근성·키보드 경로 확인 |
| P4 Validation | 생성·정적·컴파일·수치 비교 | 462 조합별 status 기록, 검증 실패/미실행 투명 표시 |
| P5 Release | 테스트/문서/ZIP 패키징, 회귀 검사 | 변경 소스·README·CHANGELOG·CI가 일치하고 리뷰 완료 |

**릴리스 관문:** 33개의 기존 계산기가 계속 정상 동작하며, 14개 언어별 결과물/빌드 방법이 존재하고, 462개 조합의 검증 상태 및 미지원 사항이 공개되어야 v1.2.0 기능 완료로 표시한다. 모든 언어의 컴파일을 실행할 수 없는 경우 부분 지원임을 명시하고 버전 범위를 재조정한다.

## 9. 별도 후속 과제 (이번 범위 제외)

- ML/DL/RL 19개, Scientific, Graphing, Programmer 전체 코드 생성 연결은 33개 금융 코드 생성 안정화 이후.
- 실시간 금융 데이터, 다중 자산·이벤트 기반 백테스트, 실거래/브로커 연동.
- 생성 코드의 클라우드 실행/원격 컴파일은 보안 샌드박스, 리소스 제한, 실행 비용 관리 설계 후 별도 추진.
- 제작자 소개·연락처·후원 링크는 별도 About/Support 기획; 검증되지 않은 PayPal/GitHub Sponsors 수령 URL을 제품에 삽입하지 않음.

## 10. 구현 전에 확인할 의사결정 (ADR 후보)

- ADR-001: Python dataclass/Pydantic/JSON Schema 중 FormulaSpec 단일 출처 결정
- ADR-002: 언어별 표준 라이브러리 우선 vs 전문 수치 라이브러리 우선
- ADR-003: C/Go/Rust/R/MATLAB의 class 옵션 대체·비활성화 정책
- ADR-004: 벡터화·행렬·시뮬레이션의 수치적 등가성과 허용 오차
- ADR-005: 생성된 코드를 로컬에서 실행할 때의 제한/보안 및 오프라인 배포 정책
- ADR-006: 검증 불가 언어(MATLAB 라이선스 등)의 CI/릴리스 승인 기준

---

**현황 요약 (2026-11-06):** v1.2.0-alpha.17에서는 **33개 수식 × 14개 언어 = 462/462개 생성 조합**과 **462/462개 컴파일·타입·구문 검사**를 달성했다. Kotlin은 실제 컴파일, Julia 및 MATLAB 대상 Octave는 구문 검사다. MATLAB CAGR의 예약어 충돌을 수정했으며 기존 74개 대표 네이티브 실행 검증도 유지된다. 전체 조합의 수치 정확성 검증 및 정식 MATLAB·스크린리더·고급 코드옵션 검증은 미완성이고 Sponsors 승인은 대기 상태다.
