"""v1.2.0-alpha.5: numerical implied volatility and Gaussian loss VaR/ES emitters.

Language emitters are not counted as runtime-verified by these source tests;
optional tests/toolchain_iv_normal_smoke.py executes selected real toolchains.
"""
from __future__ import annotations
import unittest
import math
from hyuncalculator.codegen import catalog, generate, GenerationOptions, GenerationError, LANGUAGES
from hyuncalculator.quant import black_scholes, implied_volatility, normal_var_es

NEW_IDS = ('DERIV-002', 'RISK-002')

class PortableInversionAndNormalRiskTests(unittest.TestCase):
    def test_coverage(self):
        fs = catalog()
        self.assertEqual(len(fs),33)
        self.assertEqual(sum(len(f.supported_languages) for f in fs),293)
        self.assertEqual(sum(len(f.supported_languages)==14 for f in fs),20)
        self.assertEqual(sum(len(f.supported_languages)==1 for f in fs),13)
        for fid in NEW_IDS:
            self.assertEqual(set(next(f for f in fs if f.id==fid).supported_languages),set(LANGUAGES))

    def test_new_emitter_source_present_in_all_languages(self):
        for fid in NEW_IDS:
            for lang in LANGUAGES:
                with self.subTest(fid=fid,lang=lang):
                    src=generate(fid,GenerationOptions(language=lang))
                    self.assertGreater(len(src),500)
                    self.assertNotIn('TODO',src)
                    self.assertIn('result' if lang=='MATLAB' else ('return' if fid=='DERIV-002' else ('VaR=' if lang=='R' else 'return')),src)

    def test_custom_name_and_unsafe_name_guards(self):
        for fid in NEW_IDS:
            for lang in LANGUAGES:
                with self.subTest(fid=fid,lang=lang):
                    self.assertIn('custom_quant',generate(fid,GenerationOptions(language=lang,function_name='custom_quant')))
            for invalid in ('eval()', 'if', 'a\nimport os','hyun_cdf','hyun_bs_for_iv'):
                with self.subTest(fid=fid,name=invalid):
                    if invalid.startswith('hyun_') and fid=='RISK-002':
                        continue  # reserved internal helpers differ by formula
                    with self.assertRaises(GenerationError):
                        generate(fid,GenerationOptions(language='C++',function_name=invalid))

    def test_unsupported_options_fail_closed(self):
        for fid in NEW_IDS:
            for opt in (dict(structure='class'),dict(iteration='for'),dict(iteration='while'),
                        dict(imports='numerical'),dict(variable_names=(('price','myprice'),)),
                        dict(variant='continuous')):
                with self.subTest(fid=fid,options=opt),self.assertRaises(GenerationError):
                    generate(fid,GenerationOptions(language='Go',**opt))

    def test_python_generated_iv_and_normal_match_existing_calculator(self):
        ivs = [(100,100,1,.05,.2,0,'call'),(100,110,.5,.03,.45,.01,'put'),
               (75,100,2,.02,.3,.03,'call')]
        code=generate('DERIV-002',GenerationOptions(language='Python'))
        ns={};exec(compile(code,'<codegen>','exec'),ns)
        for s,k,t,r,sigma,q,typ in ivs:
            price=black_scholes(s,k,t,r,sigma,dividend=q,option=typ)['Price']
            expected=implied_volatility(price,s,k,t,r,dividend=q,option=typ)
            self.assertAlmostEqual(ns['iv'](price,s,k,t,r,q,typ), expected, places=8)
            self.assertAlmostEqual(expected,sigma,places=7)
        with self.assertRaises(ValueError):
            ns['iv'](-1.,100,100,1.,.05,0.,'call')
        code=generate('RISK-002',GenerationOptions(language='Python'))
        ns={};exec(compile(code,'<codegen>','exec'),ns)
        for c in (.01,.05,.5,.95,.99):
            expected=normal_var_es(.001,.02,c)
            actual=ns['normal_var'](.001,.02,c)
            for name in expected:
                self.assertAlmostEqual(actual[name],expected[name],places=10)
        with self.assertRaises(ValueError):
            ns['normal_var'](.001,.02,1.0)

if __name__=='__main__': unittest.main()
