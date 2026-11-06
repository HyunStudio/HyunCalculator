"""Tests for the v1.2 design-implementation slice; unsupported combinations fail closed."""
from __future__ import annotations
import math
import unittest
from hyuncalculator import finance
from hyuncalculator.codegen import catalog, get_formula, generate, GenerationOptions, GenerationError, LANGUAGES


class RegistryTests(unittest.TestCase):
    def test_catalog_exact_size_and_stability(self):
        fs=catalog()
        self.assertEqual(len(fs),33)
        self.assertEqual(len({f.id for f in fs}),33)
        self.assertEqual(len({f.function for f in fs}),33)
        self.assertEqual(sum(f.exportable for f in fs),33)
        self.assertEqual(get_formula('FIN-001').function,'fin_fv')
        self.assertEqual(get_formula('STRAT-002').function,'qf_backtest')
        self.assertEqual(get_formula('UNKNOWN'),None)

    def test_all_languages_have_outputs_for_supported_formulas(self):
        for f in catalog():
            for lang in LANGUAGES:
                with self.subTest(formula=f.id,language=lang):
                    if lang in f.supported_languages:
                        code=generate(f.id,GenerationOptions(language=lang))
                        self.assertGreater(len(code),60)
                        self.assertTrue(any(marker in code for marker in ('return','function','struct','fn ','def ','func ')))
                    else:
                        with self.assertRaises(GenerationError):generate(f.id,GenerationOptions(language=lang))

    def test_unsupported_options_fail_explicitly(self):
        for formula,options in [
            ('FIN-001',GenerationOptions(language='C',structure='class')),
            ('FIN-002',GenerationOptions(iteration='for')),
            ('FIN-003',GenerationOptions(imports='numerical')),
            ('FIN-003',GenerationOptions(function_name='import')),
            ('FIN-003',GenerationOptions(function_name='foo;exec("bad")')),
            ('FIN-003',GenerationOptions(variant='continuous')),
        ]:
            with self.subTest(formula=formula,options=options),self.assertRaises(GenerationError):
                generate(formula,options)

    def test_npv_supports_loop_choices(self):
        for lang in LANGUAGES:
            for iteration in ('for','while'):
                with self.subTest(language=lang,iteration=iteration):
                    code=generate('FIN-004',GenerationOptions(language=lang,iteration=iteration))
                    self.assertIn('for' if (lang=='Go' and iteration=='while') else iteration, code)
                    self.assertIn('total',code)

    def test_python_generated_code_matches_finance_reference(self):
        vectors=[('FIN-001', 'fv',[1000,.05,10], finance.future_value(1000,.05,10)),
                 ('FIN-002','pv',[1628.894626777442,.05,10],finance.present_value(1628.894626777442,.05,10)),
                 ('FIN-003','pmt',[120000,.005,24],finance.payment(120000,.005,24)),
                 ('FIN-007','cagr',[100,150,3],(1.5)**(1/3)-1),
                 ('FIN-008','effective',[.12,12],(1+.12/12)**12-1),
                 ('FIN-009','annuity',[100,.04,12],100*(1-(1+.04)**-12)/.04),
                 ('FIN-004','npv',[.1,[-100,60,60]],finance.npv(.1,[-100,60,60]))]
        for ident,name,values,expected in vectors:
            with self.subTest(formula=ident):
                namespace={}
                exec(generate(ident,GenerationOptions(language='Python')),namespace)
                self.assertAlmostEqual(namespace[name](*values), expected, places=9)

    def test_zero_rate_cases_and_continuous(self):
        for ident,params,result in [('FIN-003',(120.,0.,12),10.),('FIN-009',(5.,0.,12),60.)]:
            namespace={}
            exec(generate(ident),namespace)
            fn='pmt' if ident=='FIN-003' else 'annuity'
            self.assertAlmostEqual(namespace[fn](*params),result)
        ns={};exec(generate('FIN-001',GenerationOptions(variant='continuous')),ns)
        self.assertAlmostEqual(ns['fv'](1000,.05,10),1000*math.exp(.5))

    def test_python_safety_and_domain_guards(self):
        examples=[('FIN-001',[1,-1,2]),('FIN-002',[1,-1,2]),('FIN-003',[-1,.05,2]),
                  ('FIN-007',[0,1,2]),('FIN-008',[.05,0]),('FIN-009',[100,.05,0]),
                  ('FIN-004',[-1,[100,120]])]
        for ident,values in examples:
            with self.subTest(formula=ident):
                ns={};exec(generate(ident),ns)
                fn={'FIN-001':'fv','FIN-002':'pv','FIN-003':'pmt','FIN-007':'cagr',
                    'FIN-008':'effective','FIN-009':'annuity','FIN-004':'npv'}[ident]
                with self.assertRaises(ValueError):ns[fn](*values)

    def test_python_class_mode(self):
        namespace={}
        exec(generate('FIN-001',GenerationOptions(structure='class')),namespace)
        self.assertAlmostEqual(namespace['GeneratedCalculator'].fv(1000,.05,10),1628.894626777442)

class NamingTests(unittest.TestCase):
    def test_variable_and_class_names(self):
        from hyuncalculator.codegen import generate,GenerationOptions
        opts=GenerationOptions(language='Python',structure='class',function_name='discounted_value',
                               class_name='FinanceMath',variable_names=(('fv','future_value'),('rate','discount_rate')))
        code=generate('FIN-002',opts)
        ns={};exec(code,ns)
        self.assertIn('class FinanceMath:',code)
        self.assertAlmostEqual(ns['FinanceMath'].discounted_value(110,0.1,1),100)

    def test_reject_renaming_unrecognized_or_colliding_names(self):
        from hyuncalculator.codegen import generate,GenerationOptions,GenerationError
        for rename in ((('bogus','foo'),),(('pv','rate'),),(('rate','rate'),('pv','rate'))):
            with self.subTest(rename=rename),self.assertRaises(GenerationError):
                generate('FIN-001',GenerationOptions(variable_names=rename))

    def test_npv_renamed_arguments(self):
        from hyuncalculator.codegen import generate,GenerationOptions
        opts=GenerationOptions(variable_names=(('rate','discount'),('flows','cashflows')))
        code=generate('FIN-004',opts)
        ns={};exec(code,ns)
        self.assertAlmostEqual(ns['npv'](.1,[-100,60,60]),4.132231404958667)

if __name__=='__main__': unittest.main()
