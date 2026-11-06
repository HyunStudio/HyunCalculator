"""Offline deterministic ZIP project packaging; no generated code is executed."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from hyuncalculator.codegen import LANGUAGES, GenerationError, GenerationOptions, catalog
from hyuncalculator.codegen.bundle import bundle_bytes


class BundleExportTests(unittest.TestCase):
    def _archive(self, fid, language, **kwargs):
        data = bundle_bytes(fid, GenerationOptions(language=language, **kwargs))
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            self.assertEqual(z.testzip(), None)
            filenames = z.namelist()
            self.assertEqual(filenames, sorted(filenames))
            self.assertEqual(len(filenames), len(set(filenames)))
            self.assertTrue(all(not p.startswith('/') and '..' not in Path(p).parts for p in filenames))
            manifest = json.loads(z.read('manifest.json'))
            self.assertEqual(manifest['formula_id'], fid)
            self.assertEqual(manifest['language'], language)
            self.assertFalse(manifest['runtime_verified'])
            src = manifest['source_file']
            self.assertTrue(src.startswith('source/'))
            self.assertIn(src, filenames)
            self.assertEqual(hashlib.sha256(z.read(src)).hexdigest(), manifest['sha256'])
            self.assertIn('examples/sample_inputs.json', filenames)
            self.assertIn('tests/test_integrity.py', filenames)
            self.assertIn('README.md', filenames)
        return data

    def test_all_14_languages_have_complete_archives(self):
        for lang in LANGUAGES:
            for fid in ('FIN-001', 'FIN-005', 'STAT-001', 'STRAT-002'):
                with self.subTest(language=lang, formula=fid):
                    self._archive(fid, lang)

    def test_all_33_python_formulas_archive(self):
        for f in catalog():
            with self.subTest(formula=f.id):
                self._archive(f.id, 'Python')

    def test_zip_is_bitwise_reproducible(self):
        first = self._archive('DERIV-003', 'Go')
        second = self._archive('DERIV-003', 'Go')
        self.assertEqual(first, second)
        self.assertEqual(hashlib.sha256(first).digest(), hashlib.sha256(second).digest())

    def test_python_dependency_file_is_generated_from_source(self):
        for fid in ('FIN-001', 'ALLOC-003'):
            with self.subTest(fid=fid):
                with zipfile.ZipFile(io.BytesIO(self._archive(fid, 'Python'))) as z:
                    deps = z.read('requirements.txt').decode('utf-8')
                    if fid == 'FIN-001':
                        self.assertEqual(deps, '')
                    else:
                        self.assertIn('numpy', deps)

    def test_scaffold_for_special_language_build_systems(self):
        for lang, expected in (('JavaScript','package.json'),('TypeScript','tsconfig.json'),
                               ('Go','go.mod'),('C#','HyunCalculator.Generated.csproj')):
            with self.subTest(language=lang):
                with zipfile.ZipFile(io.BytesIO(self._archive('FIN-001', lang))) as z:
                    self.assertIn(expected, z.namelist())
        with zipfile.ZipFile(io.BytesIO(self._archive('FIN-001', 'Java'))) as z:
            self.assertIn('source/GeneratedCalculator.java', z.namelist())

    def test_reject_unsafe_names_before_archiving(self):
        with self.assertRaises(GenerationError):
            bundle_bytes('FIN-001', GenerationOptions(function_name='../../danger'))
        with self.assertRaises(GenerationError):
            bundle_bytes('UNKNOWN')
        with self.assertRaises(GenerationError):
            bundle_bytes('FIN-001', GenerationOptions(language='BadLanguage'))
        with self.assertRaises(GenerationError):
            bundle_bytes('STAT-002', GenerationOptions(language='C',structure='class'))

    def test_extracted_integrity_tests_execute_offline(self):
        data = self._archive('FIN-005', 'Python')
        with tempfile.TemporaryDirectory() as temp:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                z.extractall(temp)
            result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                                    cwd=temp, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            with open(Path(temp)/'source'/'calculate_irr.py', 'a', encoding='utf-8') as source:
                source.write('\n# tampered\n')
            result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                                    cwd=temp, capture_output=True, text=True, timeout=20)
            self.assertNotEqual(result.returncode, 0, 'Digest should detect modification')

    def test_cli_creates_zip_and_rejects_conflicting_destinations(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'model.zip'
            result = subprocess.run([sys.executable, '-m', 'hyuncalculator', '--generate', 'FIN-001',
                                     '--language', 'Python', '--bundle', str(path)],
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(path.exists())
            with zipfile.ZipFile(path) as z:
                self.assertIn('manifest.json', z.namelist())
            bad = subprocess.run([sys.executable, '-m', 'hyuncalculator', '--generate', 'FIN-001',
                                  '--bundle', str(path), '--output', str(Path(temp)/'model.py')],
                                 capture_output=True, text=True, timeout=20)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn('cannot be used together', bad.stderr)

if __name__ == '__main__':
    unittest.main()
