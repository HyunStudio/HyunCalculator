"""Bilingual metadata for the original 19 AI operations and 30+ new modes."""
from __future__ import annotations

from . import legacy_ml as old
from . import finance as fin, quant as qf, programmer as pg


def register(title_ko, title_en, description_ko, description_en, formula,
             fields, fn):
    """fields = [(key, Korean label, English label, example), ...]."""
    original = tuple(old.f(key, ko, example) for key, ko, en, example in fields)
    old.EN_OPERATIONS[fn.__name__] = (title_en, description_en, formula,
                                      {key: en for key, ko, en, example in fields})
    return old.Operation(title_ko, description_ko, formula, original, fn)


FINANCE = (
    register('미래가치·연속복리', 'Future Value / Continuous Interest', '일정 기간 뒤 자산의 가치', 'Future value after N periods.',
             'FV=PV(1+r)^n / FV=PV exp(rn)', [('pv','현재가치','Present value','1000'),('rate','기간별 수익률','Rate per period (decimal)','0.05'),('n','기간 수','Periods','10'),('continuous','연속복리(1)/이산복리(0)','Continuous (1) / discrete (0)','0')],fin.fin_fv),
    register('현재가치', 'Present Value', '미래 현금흐름의 할인 가치', 'Discounted value of a future lump sum.',
             'PV=FV/(1+r)^n', [('fv','미래가치','Future value','1628.8946'),('rate','기간별 할인율','Discount rate (decimal)','0.05'),('n','기간 수','Periods','10')],fin.fin_pv),
    register('원리금균등 상환액', 'Loan Payment', '기간당 균등 상환액', 'Constant amortizing payment per period.',
             'PMT=P*r/(1-(1+r)^(-n))', [('principal','대출 원금','Principal','300000'),('rate','기간당 이자율','Rate per period (decimal)','0.005'),('n','총 상환기간','Number of payments','360')],fin.fin_pmt),
    register('순현재가치(NPV)', 'Net Present Value', '초기 투자금 포함 현금흐름을 할인', 'Discount cash flows (first flow at time 0).',
             'NPV=sum(CF_t/(1+r)^t)', [('rate','기간별 할인율','Rate per period (decimal)','0.1'),('flows','현금흐름 (t=0부터)','Cash flows from t=0','-100, 60, 60')],fin.fin_npv),
    register('내부수익률(IRR)', 'Internal Rate of Return', 'NPV=0인 연 수익률 (여러 해는 오류 처리)', 'Rate that makes NPV zero; reject multiple solutions.',
             'NPV(IRR)=0', [('flows','기간별 현금흐름','Cash flows from t=0','-100, 60, 60')],fin.fin_irr),
    register('대출 상환표 한 회차', 'Loan Amortization Period', '특정 회차 이자·원금·잔액', 'Interest, principal and balance at a selected installment.',
             'Interest_t=Balance_(t-1)*r', [('principal','대출 원금','Principal','120000'),('rate','기간별 이자율','Rate per payment period','0.005'),('n','총 상환 횟수','Total payments','24'),('period','조회 회차','Selected payment number','12')],fin.fin_loan),
    register('연평균 성장률(CAGR)', 'Compound Annual Growth Rate', '기간 전체의 연복리 성장률', 'Annualized compound growth between values.',
             'CAGR=(End/Start)^(1/years)-1', [('start','초기 값','Starting value','100'),('end','종료 값','Ending value','150'),('years','기간(년)','Years','3')],fin.fin_cagr),
    register('실효 연이율', 'Effective Annual Rate', '명목 연이율과 연간 복리 횟수로 환산', 'Effective annual rate with m compounds per year.',
             'EAR=(1+r/m)^m-1', [('rate','명목 연이율','Nominal annual rate','0.12'),('m','연간 복리 횟수','Compounds per year','12')],fin.fin_effective),
    register('연금 현재가치', 'Ordinary Annuity Present Value', '기간 말 지급 연금의 현재가치', 'PV of end-of-period payments.',
             'PV=PMT*(1-(1+r)^-n)/r', [('payment','기간별 지급액','Payment per period','100'),('rate','기간별 할인율','Rate per period','0.04'),('n','지급 기간 수','Periods','12')],fin.fin_annuity),
)


QUANT = (
    register('Black–Scholes 옵션·Greeks', 'Black–Scholes + Greeks', '유럽형 옵션·연속배당, 연간 Greeks', 'European option, continuous dividend yield and Greeks.',
             'd1=[ln(S/K)+(r-q+sigma²/2)T]/(sigma sqrt(T))', [('s','기초자산 S','Spot S','100'),('k','행사가 K','Strike K','100'),('t','잔존만기(년)','Maturity T (years)','1'),('r','무위험 연이율','Risk-free annual rate','0.05'),('sigma','연변동성','Annual volatility','0.2'),('q','연배당수익률','Annual dividend yield','0.0'),('type','옵션 종류 call/put','Option type: call/put','call')],qf.qf_bs),
    register('내재변동성', 'Implied Volatility', '옵션 시장가격으로 변동성을 역산', 'Solve Black–Scholes volatility from observed premium.',
             'BS(IV)=market price', [('price','시장 옵션가격','Market option price','10.45058357'),('s','기초자산 S','Spot','100'),('k','행사가 K','Strike','100'),('t','잔존만기(년)','Maturity (years)','1'),('r','무위험 연이율','Risk-free rate','0.05'),('q','연배당수익률','Dividend yield','0'),('type','종류 call/put','Option: call/put','call')],qf.qf_iv),
    register('몬테카를로 옵션', 'Monte Carlo European Option', 'GBM과 대칭변수로 시뮬레이션', 'Seeded antithetic-path option Monte Carlo with confidence interval.',
             'exp(-rT) E[max(±(S_T-K),0)]', [('s','기초자산 S','Spot S','100'),('k','행사가 K','Strike K','100'),('t','만기(년)','Maturity T','1'),('r','무위험 이율','Annual rate','0.05'),('sigma','연변동성','Annual volatility','0.2'),('q','배당수익률','Dividend yield','0'),('type','옵션 call/put','Option call/put','call'),('paths','경로 수(짝수)','Even simulation path count','20000'),('seed','난수 시드','Random seed','42')],qf.qf_mc),
    register('포트폴리오 위험·성과', 'Portfolio Risk / Return', '가중치·공분산 기반 연간 성과', 'Expected portfolio return and volatility.',
             'mu_p=wᵀmu; sigma_p=sqrt(wᵀΣw)', [('w','자산 가중치','Asset weights','0.6, 0.4'),('mu','기대수익률','Expected returns','0.08, 0.12'),('cov','공분산 행렬','Covariance rows separated by ;','0.04, 0.01; 0.01, 0.09'),('rf','무위험 이율','Risk-free return','0.02')],qf.qf_portfolio),
    register('최소분산 포트폴리오', 'Global Minimum Variance', '공매도 허용 완전투자 포트폴리오', 'Minimum-variance weights, shorts allowed.',
             'w=Σ^-1 1/(1ᵀΣ^-1 1)', [('cov','자산 공분산 행렬','Asset covariance matrix','0.04, 0.01; 0.01, 0.09')],qf.qf_gmv),
    register('목표수익률 최소분산', 'Target Return Markowitz', '공매도 허용 평균분산 최적화', 'Minimum variance with target return; shorts allowed.',
             'min wᵀΣw; 1ᵀw=1; muᵀw=target', [('mu','기대수익률','Expected returns','0.08, 0.12'),('cov','공분산 행렬','Covariance matrix','0.04, 0.01; 0.01, 0.09'),('target','목표수익률','Target expected return','0.1')],qf.qf_target),
    register('Black–Litterman 배분', 'Black–Litterman Posterior', '균형수익률과 사용자 뷰의 사후 기대수익률', 'Bayesian blending of equilibrium returns and investor views.',
             'pi=delta Σw; mu=pi+tau ΣPᵀ(P tau ΣPᵀ+Ω)^-1(Q-Ppi)', [('cov','공분산 행렬','Covariance Σ','0.04,0.01;0.01,0.09'),('market','시장 비중','Market cap weights','0.6,0.4'),('delta','위험회피계수','Risk aversion δ','2.5'),('tau','사전 불확실성','Prior scale τ','0.05'),('views','뷰 행렬 P (행 구분 ;)','View matrix P (rows ;)','1,-1'),('returns','뷰 수익률 Q','View returns Q','0.02'),('omega','뷰 오차 분산 대각','Diagonal view variances Ω','0.001')],qf.qf_bl),
    register('과거수익률 VaR·ES', 'Historical VaR / ES', '손실 분포 분위수와 역사적 기대손실', 'Historical signed-loss quantile and tail average.',
             'Loss=-return; VaR=Q_c(Loss)', [('r','수익률 목록','Simple returns (decimals)','-0.02,0.01,0.005,-0.04,0.02,-0.01,0.03'),('confidence','신뢰수준','Confidence (0..1)','0.95')],qf.qf_hist_var),
    register('정규분포 VaR·ES', 'Parametric Normal VaR / ES', '정규 수익률 분포를 가정', 'Normal return distribution, signed loss values.',
             'VaR=-mu+z sigma; ES=-mu+sigma phi(z)/(1-c)', [('mean','평균 수익률','Mean return','0.001'),('sigma','수익률 표준편차','Return standard deviation','0.02'),('confidence','신뢰수준','Confidence','0.95')],qf.qf_normal_var),
    register('샤프·소르티노·MDD', 'Sharpe / Sortino / Drawdown', '수익률 시계열의 연환산 지표', 'Annualized mean, volatility, ratios and max drawdown.',
             'Sharpe=sqrt(P)*(mean(r-rf)/stdev(r-rf))', [('r','기간별 단순수익률','Simple returns per period','0.01,-0.02,0.015,0.007,-0.005,0.02'),('rf','기간당 무위험 수익률','Risk-free per period','0'),('ppy','연 환산 기간수','Periods per year','252')],qf.qf_performance),
    register('채권가격·듀레이션', 'Bond Price / Duration / Convexity', '고정금리 쿠폰채 할인·민감도', 'Coupon bond dirty price and yield sensitivity.',
             'P=sum(CF_t/(1+y/m)^t)', [('face','액면가','Face value','1000'),('coupon','연 쿠폰율','Annual coupon rate','0.05'),('yield','연 명목 YTM','Annual nominal yield','0.04'),('years','만기(년)','Maturity years','5'),('freq','연간 지급 횟수','Payments per year','2')],qf.qf_bond),
    register('EWMA 변동성', 'EWMA Volatility', 'RiskMetrics 스타일 지수가중 변동성', 'Exponentially weighted next-state variance.',
             'var_t=lambda*var_(t-1)+(1-lambda)*r_t²', [('r','수익률 열','Return series','0.01,-0.02,0.015,0.005'),('decay','감쇠계수 lambda','Decay lambda','0.94')],qf.qf_ewma),
    register('GARCH(1,1) 예측', 'GARCH(1,1) One-Step', '다음 기간 조건부 분산', 'One-step conditional variance forecast.',
             'v_next=omega+alpha*epsilon²+beta*v', [('lastvar','직전 분산','Previous variance','0.0004'),('shock','직전 잔차','Previous shock','-0.01'),('omega','상수 omega','Omega','0.00001'),('alpha','충격계수 alpha','Alpha','0.08'),('beta','지속계수 beta','Beta','0.9')],qf.qf_garch),
    register('GBM 가격 확률모멘트', 'GBM Moments', '기하브라운운동의 기댓값·표준편차', 'Expected terminal price and standard deviation of GBM.',
             'E[S_T]=S0 exp(mu T)', [('s','시작가격','Initial price','100'),('mu','연 드리프트','Annual drift','0.07'),('sigma','연 변동성','Annual volatility','0.2'),('t','기간(년)','Years','1')],qf.qf_gbm),
    register('OU 평균회귀 모멘트', 'Ornstein–Uhlenbeck Moments', '평균회귀 확률과정의 기댓값·표준편차', 'Expected state and volatility of mean-reverting OU.',
             'E[X_T]=theta+(X0-theta) exp(-kappa T)', [('x','초기 상태','Initial state','2'),('level','장기 평균','Long-run mean','1'),('kappa','회귀속도','Mean reversion speed','0.8'),('sigma','확산계수','Diffusion volatility','0.2'),('t','기간(년)','Years','1')],qf.qf_ou),
    register('표본 공분산·상관관계', 'Covariance / Correlation', '행별 시점, 열별 자산 수익률', 'Sample covariance and correlation across asset return columns.',
             'Cov_ij=Σ (r_i-mean_i)(r_j-mean_j)/(n-1)', [('returns','관측값 행렬 (행=시간)','Return matrix (rows=time)','0.01,0.02;0.02,0.01;-0.01,-0.02;0.03,0.01')],qf.qf_cov),
)


PROGRAMMER = (
    register('진법·2의 보수 변환', 'Base Conversion / Two\'s Complement', '고정 워드 길이로 모든 진법 출력', 'Convert to signed/unsigned binary, octal, decimal and hex.',
             'value mod 2^width', [('value','입력 정수','Integer input','-42'),('base','입력 진법 2/8/10/16','Input base 2/8/10/16','10'),('width','비트 수 8/16/32/64','Word width','16')],pg.prog_convert),
    register('비트 논리연산', 'Bitwise Logic', 'AND OR XOR NAND NOR NOT A', 'Fixed-word logical operations; choose AND/OR/XOR/NAND/NOR/NOT A.',
             'A op B (mod 2^width)', [('a','정수 A','Integer A','0xF0'),('b','정수 B','Integer B','0x0F'),('op','논리 연산명','Operation (AND/OR/XOR/NAND/NOR/NOT A)','XOR'),('base','입력 진법','Input base','16'),('width','비트 길이','Word width','8')],pg.prog_logic),
    register('시프트', 'Bit Shift', '왼쪽/논리 오른쪽/산술 오른쪽', 'Left, logical right and arithmetic right shifts.',
             'LEFT | RIGHT | ARITH RIGHT', [('a','정수 A','Integer A','-16'),('count','시프트 비트 수','Shift bits','2'),('direction','방향 LEFT/RIGHT/ARITH RIGHT','Direction','ARITH RIGHT'),('base','입력 진법','Input base','10'),('width','비트 길이','Word width','8')],pg.prog_shift),
    register('순환 시프트', 'Rotate Bits', '순환 왼쪽/오른쪽', 'Rotate bits within a fixed word.',
             'ROL / ROR', [('a','정수 A','Integer A','0x81'),('count','순환 비트 수','Rotate bits','1'),('direction','방향 LEFT/RIGHT','Direction','LEFT'),('base','입력 진법','Input base','16'),('width','비트 길이','Word width','8')],pg.prog_rotate),
    register('비트 수 세기', 'Population Count', '1 비트와 0 비트 개수', 'Count set/clear bits in fixed width.',
             'popcount(value mod 2^width)', [('a','정수 A','Integer A','0xF0'),('base','입력 진법','Input base','16'),('width','비트 길이','Word width','8')],pg.prog_count),
)

GROUPS = {'Financial': FINANCE, 'Quant': QUANT, 'Programmer': PROGRAMMER,
          'ML': old.MENU['ML'], 'DL': old.MENU['DL'], 'RL': old.MENU['RL']}
