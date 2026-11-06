"""Independent checks for the complete 10-domain quantitative finance catalog."""
from __future__ import annotations

import math
import unittest
import numpy as np
from scipy.stats import norm

from hyuncalculator import quant as qf
from hyuncalculator import operations
from hyuncalculator import legacy_ml


class DistributionTests(unittest.TestCase):
    def test_normal_pdf_cdf_survival_and_quantile(self):
        d = qf.normal_probabilities(0, 0, 1, 0.95)
        self.assertAlmostEqual(d['PDF at x'], 1/math.sqrt(2*math.pi), places=12)
        self.assertAlmostEqual(d['CDF P(X <= x)'], .5)
        self.assertAlmostEqual(d['Survival P(X > x)'], .5)
        self.assertAlmostEqual(d['Quantile at probability'], 1.6448536269514722, places=10)

    def test_affine_normal(self):
        d = qf.normal_probabilities(13, 10, 2, 0.975)
        self.assertAlmostEqual(d['Z score'], 1.5)
        self.assertAlmostEqual(d['CDF P(X <= x)'], norm.cdf(1.5))
        self.assertAlmostEqual(d['Quantile at probability'], 10+2*norm.ppf(.975))

    def test_invalid_probability_or_std(self):
        for args in [(0,0,0,.95),(0,0,1,1.),(0,0,1,-.1),(float('nan'),0,1,.5)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                qf.normal_probabilities(*args)


class BondYieldTests(unittest.TestCase):
    def test_par_and_premium_yield(self):
        self.assertAlmostEqual(qf.yield_to_maturity(1000,1000,.05,5,2), .05, places=11)
        for y in (.01, .0425, .095, -.02):
            p = qf.bond_metrics(1000,.06,y,7,2)['Price']
            with self.subTest(y=y):
                self.assertAlmostEqual(qf.yield_to_maturity(p,1000,.06,7,2),y,places=10)

    def test_zero_coupon_yield(self):
        expected = 2*((1000/900)**(1/4)-1)
        self.assertAlmostEqual(qf.yield_to_maturity(900,1000,0,2,2),expected,places=12)

    def test_invalid_coupon_schedule_or_price(self):
        for args in [(0,1000,.05,5,2),(1000,1000,-.01,5,2),
                     (1000,1000,.04,5.1,2),(1000,1000,.05,0,2),
                     (1000,1000,.05,5,0)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                qf.yield_to_maturity(*args)

    def test_price_changes_directionally(self):
        p1 = qf.bond_metrics(1000,.05,.04,5,2)['Price']
        p2 = qf.bond_metrics(1000,.05,.06,5,2)['Price']
        self.assertGreater(p1,p2)
        self.assertLess(qf.yield_to_maturity(p1,1000,.05,5,2),qf.yield_to_maturity(p2,1000,.05,5,2))


class TimeSeriesTests(unittest.TestCase):
    def test_sma_and_ema_reference(self):
        d = qf.moving_averages([1,2,3,4,5],3)
        np.testing.assert_allclose(d['SMA (from first complete window)'],[2,3,4])
        np.testing.assert_allclose(d['EMA (first value seeded)'],[1,1.5,2.25,3.125,4.0625])
        self.assertEqual(d['Last SMA'], 4.)

    def test_window_one_and_full_window(self):
        data = [1,4,8]
        d = qf.moving_averages(data,1)
        np.testing.assert_array_equal(d['EMA (first value seeded)'],data)
        np.testing.assert_array_equal(d['SMA (from first complete window)'],data)
        self.assertAlmostEqual(qf.moving_averages(data,3)['Last SMA'],13/3)

    def test_window_rejections(self):
        for window in (0,5,1.5,True):
            with self.subTest(window=window), self.assertRaises(ValueError):
                qf.moving_averages([1,2,3],window)
        with self.assertRaises(ValueError):
            qf.moving_averages([1,math.nan,3],2)


class StochasticProcessTests(unittest.TestCase):
    def test_brownian_theoretical_moments(self):
        d = qf.brownian_motion(2,steps=40,paths=6000,seed=8,initial=5,drift=.2,diffusion=.8)
        self.assertAlmostEqual(d['Expected terminal state'],5.4,places=10)
        self.assertAlmostEqual(d['Theoretical terminal volatility'],.8*math.sqrt(2),places=10)
        self.assertAlmostEqual(d['Simulated terminal mean'],5.4,delta=.05)
        self.assertAlmostEqual(d['Simulated terminal volatility'],.8*math.sqrt(2),delta=.05)
        self.assertEqual(d['Sample path (t=0 to T)'].shape,(41,))
        self.assertEqual(d['Sample path (t=0 to T)'][0],5)

    def test_brownian_zero_diffusion(self):
        d = qf.brownian_motion(2,4,50,seed=1,initial=10,drift=-2,diffusion=0)
        self.assertAlmostEqual(d['Simulated terminal mean'],6)
        np.testing.assert_allclose(d['Sample path (t=0 to T)'],[10,9,8,7,6])

    def test_brownian_reproducibility(self):
        a = qf.brownian_motion(.5,5,20,seed=77)
        b = qf.brownian_motion(.5,5,20,seed=77)
        np.testing.assert_array_equal(a['Sample path (t=0 to T)'],b['Sample path (t=0 to T)'])

    def test_gbm_simulation_matches_theory(self):
        d = qf.gbm_simulation(100,.07,.2,1,30,6000,seed=81)
        theory=qf.gbm_moments(100,.07,.2,1)
        self.assertEqual(d['Sample price path (t=0 to T)'][0],100)
        self.assertTrue(np.all(d['Sample price path (t=0 to T)']>0))
        self.assertAlmostEqual(d['Expected terminal price'],theory['Expected price'])
        self.assertAlmostEqual(d['Simulated terminal mean'],theory['Expected price'],delta=1.)
        self.assertAlmostEqual(d['Simulated terminal volatility'],theory['Std. deviation'],delta=1.)

    def test_ou_exact_simulation_matches_theory(self):
        d = qf.ou_simulation(2,1,.8,.2,1,30,6000,seed=81)
        theory=qf.ou_moments(2,1,.8,.2,1)
        self.assertAlmostEqual(d['Expected terminal state'],theory['Expected state'])
        self.assertAlmostEqual(d['Simulated terminal mean'],theory['Expected state'],delta=.02)
        self.assertAlmostEqual(d['Simulated terminal volatility'],theory['Std. deviation'],delta=.02)
        self.assertEqual(d['Sample state path (t=0 to T)'].shape,(31,))

    def test_simulation_safety_limits(self):
        with self.assertRaises(ValueError): qf.brownian_motion(1,5000,5000)
        with self.assertRaises(ValueError): qf.brownian_motion(1,10,2,seed=-1)
        with self.assertRaises(ValueError): qf.brownian_motion(-1)
        with self.assertRaises(ValueError): qf.gbm_simulation(0,.05,.2,1)
        with self.assertRaises(ValueError): qf.ou_simulation(0,1,0,.2,1)


class CostAndBacktestTests(unittest.TestCase):
    def test_one_way_and_round_trip_cost(self):
        d = qf.transaction_cost(100000,5,3,2,2)
        self.assertEqual(d['One-way effective cost (bps)'],10)
        self.assertAlmostEqual(d['Total estimated trading cost'],200)
        self.assertAlmostEqual(d['Total traded notional'],200000)
        self.assertAlmostEqual(qf.transaction_cost(100000,5,3,2,1)['Total estimated trading cost'],100)

    def test_cost_rejects_invalid(self):
        with self.assertRaises(ValueError):qf.transaction_cost(1000,-1)
        with self.assertRaises(ValueError):qf.transaction_cost(1000,1,sides=3)

    def test_backtest_uses_delayed_signals_no_lookahead(self):
        # Massive gain in first period must not be earned by a signal seen after that period.
        d = qf.backtest_single_asset([.9,.1,.1,.1],[1,1,1,1])
        np.testing.assert_array_equal(d['Effective positions (1-period delayed)'],[0,1,1,1])
        np.testing.assert_allclose(d['Net returns per period'],[0,.1,.1,.1])
        self.assertAlmostEqual(d['Net compounded return'],1.1**3-1,places=12)
        self.assertAlmostEqual(d['Buy-and-hold compounded return'],1.9*1.1**3-1,places=12)
        self.assertEqual(d['Executed position changes'],1)

    def test_costs_paid_on_entry_exit_and_reentry(self):
        d = qf.backtest_single_asset([0,0,0,0],[1,0,1,0],commission_bps=5,slippage_bps=5)
        np.testing.assert_array_equal(d['Effective positions (1-period delayed)'],[0,1,0,1])
        np.testing.assert_allclose(d['Net returns per period'],[0,-.001,-.001,-.001])
        self.assertAlmostEqual(d['Total absolute turnover'],3)
        self.assertAlmostEqual(d['Total cost drag (sum of return fractions)'],.003)
        self.assertEqual(d['Executed position changes'],3)
        self.assertAlmostEqual(d['Net compounded return'],.999**3-1)

    def test_cost_zero_recovers_gross_result(self):
        d = qf.backtest_single_asset([.02,-.01,.03,-.02],[1,1,-1,-1])
        self.assertAlmostEqual(d['Net compounded return'],d['Gross compounded return'])
        self.assertAlmostEqual(d['Net returns per period'][0],0)
        self.assertEqual(len(d['Cumulative equity curve (start=1)']),5)
        self.assertGreaterEqual(d['Max drawdown'],-1)
        self.assertLessEqual(d['Max drawdown'],0)

    def test_short_and_final_signal_behavior(self):
        d = qf.backtest_single_asset([0,.05,-.1,.02],[-1,-1,-1,1])
        np.testing.assert_array_equal(d['Effective positions (1-period delayed)'],[0,-1,-1,-1])
        np.testing.assert_allclose(d['Net returns per period'],[0,-.05,.1,-.02])
        self.assertEqual(d['Executed position changes'],1)

    def test_invalid_backtests(self):
        cases = [([.01,.02],[1,1]),([.01,.02,.03],[1,1]),
                 ([.01,.02,.03],[1,2,1]),([.01,-1,.03],[1,1,1]),
                 ([math.nan,.02,.03],[1,1,1])]
        for returns,signals in cases:
            with self.subTest(returns=returns,signals=signals),self.assertRaises(ValueError):
                qf.backtest_single_asset(returns,signals)
        with self.assertRaises(ValueError):
            qf.backtest_single_asset([0,0,0],[1,0,0],commission_bps=-2)
        with self.assertRaises(ValueError):
            qf.backtest_single_asset([0,0,0],[1,0,0],periods_per_year=0)
        with self.assertRaises(ValueError):
            qf.backtest_single_asset([0,0,0],[1,0,0],commission_bps=2e4)


class IntegrationTests(unittest.TestCase):
    def test_all_domain_operations_both_languages_and_live_examples(self):
        new_ids = {f'qf_{x}' for x in ('normal','ytm','moving','brownian','gbm_paths','ou_paths','cost','backtest')}
        found={legacy_ml.op_id(op) for op in operations.GROUPS['Quant']}
        self.assertEqual(new_ids & found,new_ids)
        for operation in operations.GROUPS['Quant']:
            op_id=legacy_ml.op_id(operation)
            self.assertIn(op_id,legacy_ml.EN_OPERATIONS)
            self.assertTrue(legacy_ml.op_title(operation,'ko'))
            self.assertTrue(legacy_ml.op_title(operation,'en'))
            inputs={f.key:f.example for f in operation.fields}
            with self.subTest(op=op_id):
                result=operation.compute(inputs)
                self.assertIsNotNone(result)
                ko=legacy_ml.localized_result(result,'ko')
                en=legacy_ml.localized_result(result,'en')
                self.assertTrue(len(ko)>0)
                self.assertTrue(len(en)>0)


if __name__ == '__main__':
    unittest.main()
