"""v1.2.0-alpha.4 portable Black–Scholes, risk, SMA/EMA and portfolio contracts.

The 13 non-Python code emitters do not execute in the unit test runner.
Optional tests/toolchain_*_smoke.py provide separate compiler/runtime checks.
"""
from __future__ import annotations
import unittest
from hyuncalculator.codegen import catalog,generate,GenerationOptions,GenerationError,LANGUAGES
from hyuncalculator.quant import black_scholes,historical_var_es,moving_averages,portfolio_stats

NEW_IDS=('DERIV-001','PORT-001','RISK-001','TS-003')


class ExpandedPortableCodegenTests(unittest.TestCase):
    def test_full_coverage_matrix(self):
        formulas=catalog()
        self.assertEqual(len(formulas),33)
        self.assertEqual(sum(len(f.supported_languages) for f in formulas),332)
        self.assertEqual(sum('Python' in f.supported_languages for f in formulas),33)
        self.assertEqual(sum('Java' in f.supported_languages for f in formulas),23)
        for fid in NEW_IDS:
            f=next(f for f in formulas if f.id==fid)
            self.assertEqual(set(f.supported_languages),set(LANGUAGES))

    def test_generates_all_new_languages_without_placeholders(self):
        for fid in NEW_IDS:
            for lang in LANGUAGES:
                with self.subTest(formula=fid,language=lang):
                    code=generate(fid,GenerationOptions(language=lang))
                    self.assertGreater(len(code),400)
                    self.assertNotIn('TODO',code)
                    self.assertNotIn('NotImplemented',code)
                    self.assertIn('return' if lang not in ('MATLAB','R') else ('result' if lang=='MATLAB' else 'return'),code)

    def test_generated_source_supports_custom_function_name(self):
        for fid in NEW_IDS:
            for lang in LANGUAGES:
                with self.subTest(formula=fid,language=lang):
                    code=generate(fid,GenerationOptions(language=lang,function_name='custom_model'))
                    self.assertIn('custom_model',code)

    def test_rejects_unimplemented_options_explicitly(self):
        for fid in NEW_IDS:
            for options in ({'structure':'class'},{'iteration':'for'},
                            {'variable_names':(('rate','renamed_rate'),)},
                            {'variant':'continuous'},{'imports':'numerical'}):
                with self.subTest(formula=fid,options=options),self.assertRaises(GenerationError):
                    generate(fid,GenerationOptions(language='C++',**options))

    def test_reference_black_scholes_edges_and_put_call_parity(self):
        call=black_scholes(100,100,1,.05,.2,dividend=.01,option='call')
        put=black_scholes(100,100,1,.05,.2,dividend=.01,option='put')
        import math
        self.assertAlmostEqual(call['Price']-put['Price'],100*math.exp(-.01)-100*math.exp(-.05),places=11)
        for fid in NEW_IDS:
            self.assertIn('Python',next(f for f in catalog() if f.id==fid).supported_languages)

    def test_reference_portfolio_historical_risk_moving(self):
        p=portfolio_stats([.6,.4],[.08,.12],[[.04,.01],[.01,.09]],.02)
        self.assertAlmostEqual(p['Expected return'],.096)
        self.assertGreater(p['Volatility'],0)
        self.assertGreater(p['Sharpe ratio'],0)
        r=historical_var_es([-.02,.01,.005,-.04,.02,-.01,.03],.95)
        self.assertAlmostEqual(r['VaR (signed loss quantile)'],.034)
        self.assertAlmostEqual(r['Expected Shortfall'],.04)
        a=moving_averages([100.,102.,101.,104.,106.,105.],3)
        self.assertEqual(len(a['SMA (from first complete window)']),4)
        self.assertEqual(len(a['EMA (first value seeded)']),6)


if __name__=='__main__':unittest.main()
