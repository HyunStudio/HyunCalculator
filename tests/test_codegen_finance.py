"""FIN-005/006 portable finance emitters and model constraints (alpha.10)."""
from __future__ import annotations

import math
import unittest

from hyuncalculator.codegen import (
    LANGUAGES, GenerationError, GenerationOptions, catalog, generate, get_formula,
)
from hyuncalculator.finance import irr, amortization


class PortableFinanceGenerationTests(unittest.TestCase):
    def test_coverage_and_full_source_emission(self):
        formulas = catalog()
        self.assertEqual(len(formulas), 33)
        self.assertEqual(sum(len(f.supported_languages) for f in formulas), 462)
        self.assertEqual(sum(len(f.supported_languages) == 14 for f in formulas), 33)
        self.assertEqual(sum(len(f.supported_languages) == 1 for f in formulas), 0)
        for fid, required in [('FIN-005', ('irr', 'flows')),
                              ('FIN-006', ('loan', 'principal'))]:
            self.assertEqual(get_formula(fid).supported_languages, LANGUAGES)
            for lang in LANGUAGES:
                with self.subTest(formula=fid, lang=lang):
                    source = generate(fid, GenerationOptions(language=lang))
                    self.assertGreater(len(source), 200)
                    self.assertNotIn('NotImplemented', source)
                    self.assertNotIn('TODO', source)
                    self.assertIn(required[1], source)
                    custom = generate(fid, GenerationOptions(language=lang,
                                                             function_name='custom_fin'))
                    self.assertIn('custom_fin', custom)

    def test_options_outside_audited_implementation_rejected(self):
        for fid in ('FIN-005','FIN-006'):
            for extra in (
                {'structure':'class'}, {'iteration':'for'}, {'iteration':'while'},
                {'variable_names':(('rate','interest_rate'),)},
                {'imports':'numerical'}, {'variant':'continuous'},
            ):
                with self.subTest(formula=fid, options=extra), self.assertRaises(GenerationError):
                    generate(fid, GenerationOptions(language='JavaScript', **extra))

    def test_standalone_python_preserves_reference(self):
        p = {}; exec(compile(generate('FIN-005', GenerationOptions(language='Python')),
                             '<finance_irr>', 'exec'), p)
        self.assertAlmostEqual(p['calculate_irr']([-100,60,60]), irr([-100,60,60]), places=10)
        with self.assertRaises(ValueError):
            p['calculate_irr']([-100,230,-132])  # Multiple sign-changing roots
        l = {}; exec(compile(generate('FIN-006', GenerationOptions(language='Python')),
                             '<finance_loan>', 'exec'), l)
        for values in ((120000,.005,24,12),(120000,0,24,12)):
            with self.subTest(inputs=values):
                expected = amortization(*values)
                actual = l['loan'](*values)
                self.assertEqual(set(expected), set(actual))
                for key in expected:
                    self.assertTrue(math.isclose(expected[key],actual[key],abs_tol=1e-9,rel_tol=1e-9))

    def test_portable_irr_guards_and_loan_precision(self):
        # In source form the portables must include explicit multi-root rejection,
        # finite-value guards, a bounded bisection and a zero-rate loan branch.
        for lang in LANGUAGES:
            if lang == 'Python':
                continue
            with self.subTest(lang=lang):
                ir = generate('FIN-005',GenerationOptions(language=lang))
                lo = generate('FIN-006',GenerationOptions(language=lang))
                self.assertIn('120',ir)  # Maximum bisection iterations
                self.assertIn('1e-7',ir) # Multiple-root deduplication threshold
                self.assertIn('1e-14',lo)
                self.assertIn('period',lo)
                self.assertIn('payment',lo)


if __name__ == '__main__':
    unittest.main()
