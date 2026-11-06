"""Golden-value comparison of standalone Python code for all 33 finance formulas."""
from __future__ import annotations

import math
import unittest
import numpy as np

from hyuncalculator.codegen import catalog, generate, GenerationOptions, GenerationError
from hyuncalculator.operations import GROUPS


INTEGER_KEYS = frozenset({'n','m','period','ppy','freq','paths','steps','seed','window','sides'})


def _decode(field, example):
    if field == 'type':
        return example
    if ';' in example:
        return np.asarray([[float(c) for c in row.split(',')] for row in example.split(';')])
    if ',' in example:
        return np.asarray([float(c) for c in example.split(',')])
    if field in INTEGER_KEYS:
        return int(example)
    return float(example)


def _assert_equivalent(test, expected, actual, location='root'):
    if isinstance(expected, dict):
        test.assertIsInstance(actual, dict, location)
        test.assertEqual(set(expected), set(actual), location)
        for key in expected:
            _assert_equivalent(test, expected[key], actual[key], location+'.'+key)
    elif isinstance(expected, (np.ndarray, list, tuple)):
        np.testing.assert_allclose(np.asarray(actual), np.asarray(expected), rtol=1e-9, atol=1e-9, equal_nan=True,
                                   err_msg=location)
    elif isinstance(expected, (int,float,np.floating,np.integer)):
        actual=float(actual); expected=float(expected)
        if math.isnan(expected):
            test.assertTrue(math.isnan(actual), location)
        else:
            test.assertTrue(math.isclose(actual, expected, abs_tol=1e-9, rel_tol=1e-9),
                            f'{location}: expected {expected}, actual {actual}')
    else:
        test.assertEqual(expected,actual,location)


class PythonFullCoverageTests(unittest.TestCase):
    def test_all_33_formulas_match_v11_sample_inputs(self):
        operations={op.compute.__name__:op for group in ('Financial','Quant') for op in GROUPS[group]}
        for formula in catalog():
            with self.subTest(formula=formula.id):
                code=generate(formula.id,GenerationOptions(language='Python'))
                namespace={}
                exec(compile(code,'generated_'+formula.id+'.py','exec'),namespace)
                function_name={'qf_target':'target_portfolio','fin_irr':'calculate_irr'}.get(formula.function, formula.function.removeprefix('fin_').removeprefix('qf_'))
                fields=dict(formula.fields)
                expected=operations[formula.function].compute(fields)
                inputs=[_decode(key,example) for key,example in formula.fields]
                if formula.id=='FIN-001': inputs=inputs[:3]  # variant is selected in GenerationOptions
                if formula.id=='ALLOC-003':
                    inputs[-2]=np.atleast_1d(inputs[-2]); inputs[-1]=np.atleast_1d(inputs[-1])
                actual=namespace[function_name](*inputs)
                _assert_equivalent(self,expected,actual)

    def test_generated_class_custom_names_and_numeric_guard(self):
        opts=GenerationOptions(language='Python',structure='class',function_name='forecast',class_name='RiskModel',
                               variable_names=(('lastvar','previous_variance'),('shock','last_innovation')))
        namespace={}
        exec(generate('TS-002',opts),namespace)
        result=namespace['RiskModel'].forecast(0.0004,-0.01,0.00001,0.08,0.9)
        self.assertAlmostEqual(result['Forecast variance'],0.000378)
        with self.assertRaises(ValueError):
            namespace['RiskModel'].forecast(-1,0,0,0.1,0.2)

    def test_reject_unimplemented_language_and_invalid_options(self):
        for language in ('Java','C++','Go','R'):
            with self.subTest(language=language),self.assertRaises(GenerationError):
                generate('STAT-002',GenerationOptions(language=language))
        with self.assertRaises(GenerationError):
            generate('DERIV-001',GenerationOptions(language='Python',iteration='for'))
        with self.assertRaises(GenerationError):
            generate('ALLOC-003',GenerationOptions(language='Python',imports='standard'))

    def test_full_catalog_supported_language_counts(self):
        formulas=catalog()
        self.assertEqual(len(formulas),33)
        self.assertEqual(sum('Python' in f.supported_languages for f in formulas),33)
        self.assertEqual(sum('Java' in f.supported_languages for f in formulas),29)
        self.assertEqual(sum(len(f.supported_languages) for f in formulas),410)


if __name__=='__main__': unittest.main()
