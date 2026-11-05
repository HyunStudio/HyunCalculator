"""Headless, independent tests: original AI regressions + 4 calculator modes + quant."""
import math
import unittest
import numpy as np
from numpy.testing import assert_allclose
from hyuncalculator import legacy_ml as ai, operations as ops, finance as fin, quant as qf, programmer as pg
from hyuncalculator.scientific import calculate
from hyuncalculator.graphing import sample_curves


class ScientificTests(unittest.TestCase):
    def test_arithmetic_and_precedence(self):
        self.assertEqual(calculate('2+3*4'),14)
        self.assertEqual(calculate('(2+3)*4'),20)
        self.assertEqual(calculate('2^3'),8)
    def test_basic_functions(self):
        self.assertAlmostEqual(calculate('sqrt(81)+log(100)+ln(e)'),12)
        self.assertAlmostEqual(calculate('sin(pi/6)'),.5)
        self.assertAlmostEqual(calculate('sin(30)',degrees=True),.5)
        self.assertAlmostEqual(calculate('asin(.5)',degrees=True),30)
    def test_combinatorics(self):
        self.assertEqual(calculate('factorial(5)+comb(5,2)+perm(4,2)'),142)
    def test_ans_variables(self):
        self.assertEqual(calculate('Ans^2 + 1',variables={'Ans':3}),10)
    def test_complex_number(self):
        self.assertEqual(calculate('(1+2j)*(1-2j)'),5)
    def test_block_injection(self):
        for expression in ('__import__("os")','x.__class__','[1,2,3]',
                           'open("/etc/passwd")','(lambda: 3)()', 'sin(x=1)',
                           '2 if 1 else 3'):
            with self.subTest(expression=expression),self.assertRaises(ValueError):
                calculate(expression)
    def test_reject_divide_by_zero(self):
        with self.assertRaises(ValueError): calculate('1/0')
    def test_large_number_limit(self):
        with self.assertRaises(ValueError): calculate('9**10001')
    def test_domain(self):
        with self.assertRaises(ValueError): calculate('sqrt(-1)')


class GraphTests(unittest.TestCase):
    def test_sin_cos_and_parabola(self):
        curves=sample_curves('y=sin(x);y=cos(x)\ny=x^2',-1,1,201)
        self.assertEqual(len(curves),3)
        self.assertAlmostEqual(curves[0][2][100],0,places=9)
        self.assertAlmostEqual(curves[1][2][100],1,places=9)
        self.assertAlmostEqual(curves[2][2][200],1,places=9)
    def test_constant_line(self):
        curves=sample_curves('y=3',-1,1,20)
        assert_allclose(curves[0][2],3)
    def test_degrees(self):
        curves=sample_curves('sin(x)',0,90,91,degrees=True)
        self.assertAlmostEqual(curves[0][2][-1],1,places=9)
    def test_reject_no_real_values(self):
        with self.assertRaises(ValueError): sample_curves('sqrt(-x^2-1)',-1,1)
    def test_reject_many_functions(self):
        with self.assertRaises(ValueError): sample_curves(';'.join(['x']*9))
    def test_safe_ast(self):
        with self.assertRaises(ValueError): sample_curves('x.__class__')


class FinancialTests(unittest.TestCase):
    def test_future_value_compound(self):
        self.assertAlmostEqual(fin.future_value(1000,.05,2),1102.5)
    def test_future_value_continuous(self):
        self.assertAlmostEqual(fin.future_value(1000,.05,2,compounding='continuous'),1000*math.exp(.1))
    def test_present_value(self):
        self.assertAlmostEqual(fin.present_value(1102.5,.05,2),1000)
    def test_payment_zero_interest(self):
        self.assertEqual(fin.payment(1200,0,12),100)
    def test_payment_standard(self):
        self.assertAlmostEqual(fin.payment(1000,.01,12),88.84878867834168)
    def test_npv(self):
        self.assertAlmostEqual(fin.npv(.1,[-100,60,60]),4.13223140495867)
    def test_irr(self):
        self.assertAlmostEqual(fin.irr([-100,60,60]),.130662386291807,places=8)
    def test_multiple_irrs_rejected(self):
        with self.assertRaisesRegex(ValueError,'Multiple'): fin.irr([-100,230,-132])
    def test_no_irr(self):
        with self.assertRaises(ValueError): fin.irr([1,2,3])
    def test_loan_last_balance(self):
        info=fin.amortization(1000,.01,12,12)
        self.assertAlmostEqual(info['Remaining balance'],0,places=8)
    def test_cagr(self):
        self.assertAlmostEqual(fin.fin_cagr({'start':'100','end':'121','years':'2'}),.1)
    def test_annuity(self):
        self.assertAlmostEqual(fin.fin_annuity({'payment':'100','rate':'0','n':'12'}),1200)
    def test_negative_rate_rejected(self):
        with self.assertRaises(ValueError): fin.payment(100,-1,12)


class ProgrammerTests(unittest.TestCase):
    def test_base_and_twos_complement(self):
        self.assertEqual(pg.represent(-1,8)['Hexadecimal'],'0xFF')
        self.assertEqual(pg.represent(255,8)['Signed decimal'],-1)
        self.assertEqual(pg.parse_int('0b1010',2),10)
        self.assertEqual(pg.parse_int('FF',16),255)
    def test_logic(self):
        self.assertEqual(pg.bitwise(0xF0,0x0F,'XOR',8)['Unsigned decimal'],255)
        self.assertEqual(pg.bitwise(0xF0,0x0F,'AND',8)['Unsigned decimal'],0)
        self.assertEqual(pg.bitwise(0,0,'NOT A',8)['Unsigned decimal'],255)
    def test_shifts(self):
        self.assertEqual(pg.shift(-16,2,'ARITH RIGHT',8)['Signed decimal'],-4)
        self.assertEqual(pg.shift(-16,2,'RIGHT',8)['Unsigned decimal'],60)
        self.assertEqual(pg.shift(1,2,'LEFT',8)['Unsigned decimal'],4)
    def test_rotate(self):
        self.assertEqual(pg.rotate(0x81,1,'LEFT',8)['Unsigned decimal'],3)
        self.assertEqual(pg.rotate(0x81,1,'RIGHT',8)['Unsigned decimal'],0xC0)
    def test_popcount(self):
        self.assertEqual(pg.prog_count({'a':'0xF0','base':'16','width':'8'})['Set bits'],4)
    def test_invalid_width(self):
        with self.assertRaises(ValueError): pg.represent(1,13)
    def test_negative_shift(self):
        with self.assertRaises(ValueError): pg.shift(1,-1,'LEFT')


class QuantTests(unittest.TestCase):
    def test_black_scholes_reference(self):
        call=qf.black_scholes(100,100,1,.05,.2)
        put=qf.black_scholes(100,100,1,.05,.2,option='put')
        self.assertAlmostEqual(call['Price'],10.450583572185565,places=7)
        self.assertAlmostEqual(put['Price'],5.573526022256971,places=7)
        self.assertAlmostEqual(call['Price']-put['Price'],100-100*math.exp(-.05),places=8)
        self.assertAlmostEqual(call['Delta'],.6368306511756191,places=8)
    def test_implied_vol(self):
        price=qf.black_scholes(100,100,1,.05,.2)['Price']
        self.assertAlmostEqual(qf.implied_volatility(price,100,100,1,.05),.2,places=9)
    def test_price_bounds(self):
        with self.assertRaises(ValueError): qf.implied_volatility(150,100,100,1,.05)
    def test_maturity_zero(self):
        self.assertEqual(qf.black_scholes(110,100,0,.02,.2)['Price'],10)
    def test_mc_reproducible_close_to_bs(self):
        x=qf.european_mc(100,100,1,.05,.2,paths=40000,seed=9)
        y=qf.european_mc(100,100,1,.05,.2,paths=40000,seed=9)
        self.assertEqual(x,y)
        self.assertLess(abs(x['Monte Carlo price']-qf.black_scholes(100,100,1,.05,.2)['Price']),.2)
        self.assertGreater(x['Std. error (paired)'],0)
    def test_portfolio(self):
        c=np.array([[.04,.01],[.01,.09]])
        d=qf.portfolio_stats([.6,.4],[.08,.12],c,.02)
        self.assertAlmostEqual(d['Expected return'],.096)
        self.assertAlmostEqual(d['Volatility'],math.sqrt(.6**2*.04+2*.6*.4*.01+.4**2*.09))
    def test_gmv_optimality(self):
        c=np.array([[.04,.01],[.01,.09]])
        w=qf.global_minimum_variance(c)
        self.assertAlmostEqual(w.sum(),1)
        self.assertAlmostEqual(w[0],.7272727272727273)
    def test_target_return_constraint(self):
        w=qf.minimum_variance_target([.08,.12],[[.04,.01],[.01,.09]],.10)
        self.assertAlmostEqual(w.sum(),1)
        self.assertAlmostEqual(w @ np.array([.08,.12]),.10)
    def test_black_litterman(self):
        d=qf.black_litterman([[.04,.01],[.01,.09]],[.6,.4],2.5,.05,[[1,-1]],[.02],[.001])
        self.assertEqual(d['Posterior expected returns'].shape,(2,))
        self.assertTrue(np.linalg.eigvalsh(d['Posterior predictive covariance']).min()>0)
        self.assertFalse(np.allclose(d['Posterior expected returns'],d['Equilibrium returns']))
    def test_singular_matrix_rejected(self):
        with self.assertRaises(ValueError): qf.global_minimum_variance([[1,1],[1,1]])
    def test_normal_var_es(self):
        info=qf.normal_var_es(0,1,.95)
        self.assertAlmostEqual(info['VaR (signed loss quantile)'],1.6448536269514722)
        self.assertAlmostEqual(info['Expected Shortfall'],2.062712807507425)
    def test_historical_tail(self):
        d=qf.historical_var_es([-.04,-.02,0,.01,.05],.8)
        self.assertAlmostEqual(d['VaR (signed loss quantile)'],.024)
        self.assertAlmostEqual(d['Expected Shortfall'],.04)
    def test_drawdown(self):
        d=qf.risk_metrics([.1,-.2,.05],0,12)
        self.assertAlmostEqual(d['Max drawdown'],-.2)
    def test_bond_par_and_duration(self):
        d=qf.bond_metrics(1000,.05,.05,5,2)
        self.assertAlmostEqual(d['Price'],1000,places=8)
        self.assertTrue(0<d['Modified duration (years)']<5)
        self.assertGreater(d['Convexity (years²)'],0)
    def test_ewma(self):
        d=qf.ewma_volatility([.01,-.02],.94)
        self.assertAlmostEqual(d['EWMA variance'],.94*.01**2+.06*.02**2)
    def test_garch(self):
        d=qf.garch_forecast(.0004,-.01,.00001,.08,.9)
        self.assertAlmostEqual(d['Forecast variance'],.00001+.08*.01**2+.9*.0004)
    def test_gbm(self):
        d=qf.gbm_moments(100,.05,.2,1)
        self.assertAlmostEqual(d['Expected price'],100*math.exp(.05))
    def test_ou(self):
        d=qf.ou_moments(2,1,.8,.2,0)
        self.assertEqual(d['Expected state'],2)
        self.assertEqual(d['Std. deviation'],0)
    def test_covariance(self):
        d=qf.covariance_correlation([[1,2],[2,4],[3,6]])
        self.assertAlmostEqual(d['Sample correlation'][0,1],1)
    def test_legacy_original_tests(self):
        self.assertAlmostEqual(ai.ml_linear({'x':'1,2,3','w':'0.2,0.4,0.6','b':'.1'}),2.9)
        self.assertAlmostEqual(ai.rl_return({'r':'1,2,3','gamma':'.9'}),5.23)
    def test_all_operation_translations(self):
        self.assertEqual(len(ai.MENU['ML'])+len(ai.MENU['DL'])+len(ai.MENU['RL']),19)
        self.assertEqual(len(ops.GROUPS),6)
        ids=[]
        for code, operations in ops.GROUPS.items():
            self.assertTrue(operations,code)
            for op in operations:
                code_id=ai.op_id(op); ids.append(code_id)
                title,description,formula,fields=ai.EN_OPERATIONS[code_id]
                self.assertTrue(title and description and formula)
                self.assertEqual(set(fields),{field.key for field in op.fields})
                # Execute each operation's example inputs; flags incorrect menu defaults.
                arguments={field.key:field.example for field in op.fields}
                with self.subTest(op=code_id):
                    result=op.compute(arguments)
                    self.assertIsNotNone(result)
        self.assertEqual(len(ids),len(set(ids)))


if __name__=='__main__':
    unittest.main()
