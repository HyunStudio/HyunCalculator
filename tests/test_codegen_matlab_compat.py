"""Regression checks for MATLAB-safe scalar identifiers.

Octave parser checks are performed separately in mandatory GitHub Actions;
these tests ensure the emitted source contract cannot regress silently.
"""
import unittest

from hyuncalculator.codegen import GenerationOptions, generate


class MatlabCagrReservedWordTests(unittest.TestCase):
    def test_cagr_never_uses_end_keyword_as_parameter(self):
        source = generate("FIN-007", GenerationOptions(language="MATLAB"))
        self.assertIn("function result = cagr(start, ending_value, years)", source)
        self.assertIn("ending_value", source)
        self.assertNotIn("cagr(start, end, years)", source)
        self.assertNotIn("(end / start)", source)

    def test_other_language_cagr_contract_unchanged(self):
        source = generate("FIN-007", GenerationOptions(language="Python"))
        self.assertIn("def cagr(", source)
        self.assertIn("end", source)


if __name__ == "__main__":
    unittest.main()
