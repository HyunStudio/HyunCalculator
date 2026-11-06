"""Portable fixed-income and EWMA generator contracts (no toolchain required)."""
import unittest
from hyuncalculator.codegen import (catalog, generate, GenerationOptions, GenerationError, LANGUAGES)


class PortableLoopGenerationTests(unittest.TestCase):
    def test_new_formula_matrix_is_real_code(self):
        for fid in ('BOND-001', 'BOND-002', 'TS-001'):
            with self.subTest(formula=fid):
                form=next(f for f in catalog() if f.id==fid)
                self.assertEqual(set(form.supported_languages), set(LANGUAGES))
                for lang in LANGUAGES:
                    code=generate(fid,GenerationOptions(language=lang))
                    self.assertIn('return' if lang not in ('R','MATLAB') else ('result' if lang=='MATLAB' else 'return'),code)
                    self.assertGreater(len(code),250)
    def test_unsupported_opts_are_rejected(self):
        for fid in ('BOND-001','BOND-002','TS-001'):
            for kw in ({'iteration':'for'},{'structure':'class'},
                       {'variable_names':(('face','face_value'),)}):
                with self.subTest(formula=fid,opts=kw),self.assertRaises(GenerationError):
                    generate(fid,GenerationOptions(language='C++',**kw))
    def test_total_generated_combinations(self):
        self.assertEqual(sum(len(f.supported_languages) for f in catalog()),332)

if __name__=='__main__':unittest.main()
