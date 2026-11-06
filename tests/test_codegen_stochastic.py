"""Cross-language stochastic process generation and independent RNG contracts."""
from __future__ import annotations

import math
import unittest

import numpy as np

from hyuncalculator.codegen import LANGUAGES, GenerationError, GenerationOptions, catalog, generate, get_formula
from hyuncalculator.quant import brownian_motion, gbm_simulation, ou_simulation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from toolchain_stochastic_smoke import CASES, reference

IDS = ('STOCH-003','STOCH-004','STOCH-005')


class StochasticCodegenTests(unittest.TestCase):
    def test_coverage(self):
        items=catalog()
        self.assertEqual(len(items),33)
        self.assertEqual(sum(len(x.supported_languages) for x in items),462)
        self.assertEqual(sum(len(x.supported_languages)==14 for x in items),33)
        self.assertEqual(sum(len(x.supported_languages)==1 for x in items),0)
        for fid in IDS:
            self.assertEqual(get_formula(fid).supported_languages, LANGUAGES)

    def test_all_42_combinations_generate(self):
        for fid in IDS:
            for lang in LANGUAGES:
                with self.subTest(fid=fid,lang=lang):
                    src=generate(fid,GenerationOptions(language=lang))
                    self.assertGreater(len(src),450)
                    self.assertNotIn('TODO',src)
                    self.assertNotIn('NotImplemented',src)
                    self.assertIn(CASES[fid][0],src)
                    self.assertIn('custom_stoch',generate(fid,GenerationOptions(language=lang,function_name='custom_stoch')))
                    if lang!='Python':
                        self.assertIn('2147483647',src)
                        self.assertIn('steps+5',src)

    def test_advanced_unsupported_options_fail_closed(self):
        for fid in IDS:
            for bad in ({'structure':'class'},{'iteration':'for'},{'iteration':'while'},
                        {'variable_names':(('sigma','vol'),)},{'imports':'numerical'},
                        {'variant':'continuous'}):
                with self.subTest(fid=fid,bad=bad),self.assertRaises(GenerationError):
                    generate(fid,GenerationOptions(language='JavaScript',**bad))

    def test_portable_rng_and_sample_paths(self):
        for fid,(_,_,args) in CASES.items():
            with self.subTest(fid=fid):
                result=reference(fid,args)
                self.assertEqual(len(result),int(args[1] if fid=='STOCH-003' else args[4] if fid=='STOCH-004' else args[5])+5)
                self.assertTrue(all(math.isfinite(x) for x in result))
                self.assertGreaterEqual(result[3],0.)
                self.assertGreaterEqual(result[1],0.)
                self.assertAlmostEqual(result[4],args[4] if fid=='STOCH-003' else args[0],places=12)
                self.assertAlmostEqual(result[-1],result[5+int(args[1] if fid=='STOCH-003' else args[4] if fid=='STOCH-004' else args[5])-1],places=12)
                self.assertEqual(result,reference(fid,args))

    def test_zero_volatility_analytic_limits(self):
        for fid,(_,_,args) in CASES.items():
            a=list(args)
            vol_index={'STOCH-003':6,'STOCH-004':2,'STOCH-005':3}[fid]
            a[vol_index]=0.0
            values=reference(fid,tuple(a))
            self.assertAlmostEqual(values[3],0.,delta=1e-10)
            self.assertAlmostEqual(values[2],values[0],delta=1e-10)
            self.assertAlmostEqual(values[1],0.,delta=1e-10)

    def test_python_preserves_original_numpy_contract(self):
        mapping={
            'STOCH-003':(brownian_motion,(1.,4,50,42,.5,.07,.2)),
            'STOCH-004':(gbm_simulation,(100.,.07,.2,1.,4,50,42)),
            'STOCH-005':(ou_simulation,(2.,1.,.8,.2,1.,4,50,42)),
        }
        for fid,(ref,args) in mapping.items():
            with self.subTest(fid=fid):
                ns={}
                exec(compile(generate(fid,GenerationOptions(language='Python')),'<generated>','exec'),ns)
                fn=CASES[fid][0]
                expected=ref(*args)
                actual=ns[fn](*args)
                for key,value in expected.items():
                    np.testing.assert_allclose(value,actual[key],atol=1e-11,rtol=1e-11)


if __name__=='__main__':unittest.main()
