"""v1.2.0-alpha.6 Markowitz GMV/target allocation generation contracts."""
from __future__ import annotations
import math
import unittest
import numpy as np
from hyuncalculator.codegen import catalog, generate, GenerationOptions, GenerationError, LANGUAGES
from hyuncalculator.quant import global_minimum_variance, minimum_variance_target

IDS=('ALLOC-001','ALLOC-002')
COV=[[.04,.01],[.01,.09]]
MU=[.08,.12]

class AllocationCodegenTests(unittest.TestCase):
    def test_coverage_matrix(self):
        registry=catalog()
        self.assertEqual(len(registry),33)
        self.assertEqual(sum(map(lambda x:len(x.supported_languages),registry)),410)
        self.assertEqual(sum(len(x.supported_languages)==14 for x in registry),29)
        self.assertEqual(sum(len(x.supported_languages)==1 for x in registry),4)
        for fid in IDS:
            spec=next(x for x in registry if x.id==fid)
            self.assertEqual(set(spec.supported_languages),set(LANGUAGES))

    def test_sources_generated_all_languages(self):
        for fid in IDS:
            for lang in LANGUAGES:
                with self.subTest(fid=fid,lang=lang):
                    source=generate(fid,GenerationOptions(language=lang))
                    self.assertGreater(len(source),400)
                    self.assertNotIn('TODO',source)
                    self.assertNotIn('NotImplemented',source)
                    self.assertTrue(('gmv' if fid=='ALLOC-001' else 'target_portfolio') in source)

    def test_names_and_unsupported_settings(self):
        for fid in IDS:
            for lang in LANGUAGES:
                self.assertIn('chosen_allocation',generate(fid,GenerationOptions(language=lang,function_name='chosen_allocation')))
            for extra in ({'structure':'class'}, {'iteration':'for'}, {'iteration':'while'},
                          {'variable_names':(('cov','risk_covariance'),)},
                          {'imports':'numerical'},{'variant':'continuous'}):
                with self.subTest(fid=fid,extra=extra),self.assertRaises(GenerationError):
                    generate(fid,GenerationOptions(language='C++',**extra))

    def test_python_generated_matches_reference_two_and_three_assets(self):
        for fid in IDS:
            code=generate(fid,GenerationOptions(language='Python'))
            ns={};exec(compile(code,'<codegen>','exec'),ns)
            fn=ns['gmv' if fid=='ALLOC-001' else 'target_portfolio']
            for cov,mu,target in [
                (COV,MU,.1),
                ([[.04,.01,.005],[.01,.09,.02],[.005,.02,.07]],[.08,.12,.15],.11)
            ]:
                expected=global_minimum_variance(cov) if fid=='ALLOC-001' else minimum_variance_target(mu,cov,target)
                actual=fn(cov) if fid=='ALLOC-001' else fn(mu,cov,target)
                weights=actual['Weights']
                np.testing.assert_allclose(weights,expected,atol=1e-9,rtol=1e-9)
                self.assertAlmostEqual(sum(weights),1.,places=9)
                if fid=='ALLOC-002':
                    self.assertAlmostEqual(actual['Expected portfolio return'],target,places=9)
                else:
                    self.assertAlmostEqual(actual['Portfolio variance'],float(np.asarray(weights) @ np.asarray(cov) @ np.asarray(weights)),places=9)

    def test_reject_invalid_covariance_and_rank(self):
        for fid in IDS:
            for cov in ([[1.,1.],[1.,1.]],[[1.,2.],[0.,1.]],[[float('nan'),0],[0,1]]):
                with self.subTest(fid=fid,cov=cov):
                    code=generate(fid,GenerationOptions(language='Python'))
                    ns={};exec(code,ns)
                    fn=ns['gmv' if fid=='ALLOC-001' else 'target_portfolio']
                    with self.assertRaises(ValueError):
                        if fid=='ALLOC-001':fn(cov)
                        else:fn(MU,cov,.1)
            if fid=='ALLOC-002':
                with self.assertRaises(ValueError):minimum_variance_target([.1,.1],COV,.1)

if __name__=='__main__':unittest.main()
