"""Black-Litterman 14-language source generation and reference contracts."""
from __future__ import annotations
import unittest
import numpy as np
from hyuncalculator.codegen import (LANGUAGES, GenerationError, GenerationOptions,
                                     catalog, generate, get_formula)
from hyuncalculator.quant import black_litterman

COV=[[.04,.01],[.01,.09]]
MARKET=[.6,.4]
P=[[1.,-1.]]
Q=[.02]
OMEGA=[.001]

class BlackLittermanCodegenTest(unittest.TestCase):
    def test_registry_coverage_and_names(self):
        formulas=catalog()
        self.assertEqual(len(formulas),33)
        self.assertEqual(sum(len(x.supported_languages) for x in formulas),345)
        self.assertEqual(sum(len(x.supported_languages)==14 for x in formulas),24)
        self.assertEqual(sum(len(x.supported_languages)==1 for x in formulas),9)
        self.assertEqual(get_formula('ALLOC-003').function,'qf_bl')
        self.assertEqual(set(get_formula('ALLOC-003').supported_languages),set(LANGUAGES))

    def test_all_languages_source_generation(self):
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                src=generate('ALLOC-003',GenerationOptions(language=lang))
                self.assertGreater(len(src),550)
                self.assertNotIn('TODO',src)
                self.assertNotIn('NotImplemented',src)
                renamed=generate('ALLOC-003',GenerationOptions(language=lang,function_name='custom_bl'))
                self.assertIn('custom_bl',renamed)

    def test_invalid_options_fail_closed(self):
        for extra in ({'structure':'class'}, {'iteration':'for'}, {'iteration':'while'},
                      {'variable_names':(('cov','sigma'),)}, {'imports':'numerical'},
                      {'variant':'continuous'}):
            with self.subTest(extra=extra):
                with self.assertRaises(GenerationError):
                    generate('ALLOC-003',GenerationOptions(language='C++',**extra))

    def test_python_generated_reference(self):
        code=generate('ALLOC-003',GenerationOptions(language='Python'))
        ns={};exec(compile(code,'<generated bl>','exec'),ns)
        self.assertIn('bl',ns)
        samples=[
            (COV,MARKET,2.5,.05,P,Q,OMEGA),
            ([[.04,.01,.005],[.01,.09,.02],[.005,.02,.07]],
             [.5,.3,.2],2.5,.05,[[1.,-1.,0.],[0.,1.,-1.]],[.025,.01],[.002,.003]),
        ]
        for args in samples:
            expected=black_litterman(*args)
            actual=ns['bl'](*args)
            for key in expected:
                with self.subTest(key=key,n=len(args[0])):
                    np.testing.assert_allclose(actual[key],expected[key],rtol=1e-9,atol=1e-10)

    def test_python_invalid_inputs(self):
        code=generate('ALLOC-003',GenerationOptions(language='Python'))
        ns={};exec(code,ns)
        cases=[
          ([[.04,.01],[.01,.09]],[.8,.4],2.5,.05,P,Q,OMEGA),
          ([[.04,.01],[.01,.09]],MARKET,2.5,0.,P,Q,OMEGA),
          ([[.04,.01],[.01,.09]],MARKET,2.5,.05,P,Q,[0.]),
          ([[.04,.01],[.01,.09]],MARKET,2.5,.05,[[1.]],Q,OMEGA),
          ([[1.,1.],[1.,1.]],MARKET,2.5,.05,P,Q,OMEGA),
        ]
        for args in cases:
            with self.subTest(args=args),self.assertRaises(ValueError):
                ns['bl'](*args)

if __name__=='__main__':unittest.main()
