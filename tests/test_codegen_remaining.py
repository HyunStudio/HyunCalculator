"""alpha.11: 462 source-generation matrix and four final portable profiles.

These tests cover generator contracts. Optional native compiler smoke checks
remain separate because not all 14 runtimes are installed in CI.
"""
from __future__ import annotations

import unittest
import math
import numpy as np
from scipy.stats import norm

from hyuncalculator.codegen import (
    LANGUAGES, GenerationError, GenerationOptions, catalog, generate, get_formula,
)
from hyuncalculator.quant import (
    covariance_correlation, normal_probabilities, risk_metrics, backtest_single_asset,
)

NEW_IDS = ('STAT-001','STAT-002','RISK-003','STRAT-002')


class LastFourFormulaGenerationTests(unittest.TestCase):
    def test_entire_462_language_formula_matrix_has_explicit_source(self):
        formulas=catalog()
        self.assertEqual(len(formulas),33)
        self.assertEqual(sum(len(x.supported_languages) for x in formulas),462)
        self.assertTrue(all(tuple(x.supported_languages)==LANGUAGES for x in formulas))
        for f in formulas:
            for language in LANGUAGES:
                with self.subTest(id=f.id,language=language):
                    code=generate(f.id,GenerationOptions(language=language))
                    self.assertGreater(len(code),60)
                    self.assertNotIn('NotImplemented',code)
                    self.assertNotIn('TODO',code)
                    self.assertNotIn('import hyuncalculator',code)
                    self.assertNotIn('from hyuncalculator',code)

    def test_four_new_profiles_available_in_all_languages(self):
        for fid in NEW_IDS:
            self.assertEqual(get_formula(fid).supported_languages,LANGUAGES)
            for lang in LANGUAGES:
                with self.subTest(formula=fid,lang=lang):
                    source=generate(fid,GenerationOptions(language=lang,function_name='generated_model'))
                    self.assertIn('generated_model',source)
                    self.assertGreater(len(source),350)

    def test_unsupported_advanced_controls_rejected_in_portable_profiles(self):
        for fid in NEW_IDS:
            for spec in ({'structure':'class'},{'iteration':'for'},
                         {'iteration':'while'},{'imports':'numerical'},
                         {'variable_names':(('x','spot'),)},
                         {'variant':'continuous'}):
                with self.subTest(formula=fid,options=spec),self.assertRaises(GenerationError):
                    generate(fid,GenerationOptions(language='C++',**spec))

    def test_normal_reference_has_correct_pdf_cdf_quantile_and_tails(self):
        for x,mean,std,p in [(100,100,20,.95),(-2,1,3,.001),(4,-1,2,.999),(.0,0,1,.5)]:
            with self.subTest(x=x,mean=mean,p=p):
                d=normal_probabilities(x,mean,std,p)
                self.assertAlmostEqual(d['PDF at x'],norm.pdf(x,mean,std),places=12)
                self.assertAlmostEqual(d['CDF P(X <= x)'],norm.cdf(x,mean,std),places=12)
                self.assertAlmostEqual(d['Quantile at probability'],norm.ppf(p,mean,std),places=10)

    def test_covariance_reference_sample_ddof_and_zero_std(self):
        x=np.array([[.05,.1,.08],[.1,.02,.07],[-.05,.03,.01],[.02,-.04,.06]])
        d=covariance_correlation(x)
        np.testing.assert_allclose(d['Sample covariance'],np.cov(x,rowvar=False,ddof=1))
        np.testing.assert_allclose(d['Sample correlation'],np.corrcoef(x,rowvar=False))
        flat=np.r_[d['Sample covariance'].ravel(),d['Sample correlation'].ravel()]
        self.assertEqual(len(flat),18)
        for lang in ('C','JavaScript','Swift','Go','Rust'):
            source=generate('STAT-002',GenerationOptions(language=lang))
            self.assertIn('cols',source)

    def test_performance_reference_annualization_downside_and_mdd(self):
        returns=np.array([.05,-.02,.01,-.03,.04,.015])
        rf=.001;ppy=252
        d=risk_metrics(returns,rf,ppy)
        ex=returns-rf
        self.assertAlmostEqual(d['Annualized volatility'],np.std(ex,ddof=1)*math.sqrt(ppy))
        self.assertAlmostEqual(d['Annualized Sortino'],np.mean(ex)/math.sqrt(np.mean(np.minimum(ex,0)**2))*math.sqrt(ppy))
        wealth=np.r_[1.,np.cumprod(1+returns)]
        self.assertAlmostEqual(d['Max drawdown'],np.min(wealth/np.maximum.accumulate(wealth)-1))

    def test_backtest_no_lookahead_and_curve_output_contract(self):
        r=[.02,-.01,.03,.01,-.02,.04]
        signals=[1,1,-1,0,.5,0]
        d=backtest_single_asset(r,signals,3,2,.0001,252)
        np.testing.assert_allclose(d['Effective positions (1-period delayed)'],[0,1,1,-1,0,.5])
        self.assertEqual(len(d['Net returns per period']),6)
        self.assertEqual(len(d['Cumulative equity curve (start=1)']),7)
        self.assertAlmostEqual(d['Cumulative equity curve (start=1)'][0],1)
        self.assertEqual(len(d['Buy-and-hold equity curve (start=1)']),7)
        self.assertAlmostEqual(d['Annualized CAGR'],(1+d['Net compounded return'])**(252/6)-1)
        code=generate('STRAT-002',GenerationOptions(language='C'))
        self.assertIn('4*n+14',code)
        self.assertIn('sig[t-1]',code)


if __name__=='__main__':
    unittest.main()
