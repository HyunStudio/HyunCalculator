"""Deterministic, offline ZIP exports for formula-to-code outputs.

Only fixed internal paths are used. GenerationOptions is validated by generate().
Bundles contain source, sample input *data*, language dependencies and a
stdlib integrity test; they do not claim the generated algorithm was run.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from dataclasses import asdict

from .. import __version__
from .emitter import EXTENSIONS, GenerationError, GenerationOptions, generate
from .registry import get_formula

_SUPPORTED = frozenset(EXTENSIONS)
_DATE = (2024, 1, 1, 0, 0, 0)


def _file_name(formula, options: GenerationOptions) -> str:
    """Keep paths stable, independent of caller-controlled separators."""
    if options.language == 'Java':
        # Java public top-level class name must match source basename.
        basename = options.class_name if options.structure == 'class' else 'GeneratedCalculator'
    else:
        basename = (options.function_name or formula.function.removeprefix('fin_').removeprefix('qf_'))
        if formula.function == 'fin_irr' and options.function_name is None:
            basename = 'calculate_irr'
        if formula.function == 'qf_target' and options.function_name is None:
            basename = 'target_portfolio'
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,79}', basename):
        raise GenerationError('Invalid source filename')
    return f'{basename}.{EXTENSIONS[options.language]}'


def _extra_files(language: str, source: str) -> dict[str, str]:
    if language == 'Python':
        packages = []
        if re.search(r'(?m)^\s*(?:import|from)\s+numpy\b', source):
            packages.append('numpy>=1.24')
        if re.search(r'(?m)^\s*(?:import|from)\s+scipy\b', source):
            packages.append('scipy>=1.10')
        # Empty file is intentional for stdlib-only Python formulas.
        return {'requirements.txt': '\n'.join(packages) + ('\n' if packages else '')}
    if language == 'JavaScript':
        return {'package.json': json.dumps({'private': True, 'type': 'module'}, indent=2) + '\n'}
    if language == 'TypeScript':
        return {'tsconfig.json': json.dumps({'compilerOptions': {'target': 'ES2020', 'module': 'ES2020', 'strict': True, 'noEmit': True}, 'include': ['source/**/*.ts']}, indent=2) + '\n'}
    if language == 'Go':
        return {'go.mod': 'module hyuncalculator/generated\n\ngo 1.21\n'}
    if language == 'C#':
        return {'HyunCalculator.Generated.csproj': '<Project Sdk="Microsoft.NET.Sdk">\n  <PropertyGroup>\n    <TargetFramework>net8.0</TargetFramework>\n    <OutputType>Library</OutputType>\n    <Nullable>enable</Nullable>\n  </PropertyGroup>\n</Project>\n'}
    return {}


def _command(language: str, filename: str) -> str:
    path = f'source/{filename}'
    return {
        'Python': f'python -m pip install -r requirements.txt\npython -m py_compile {path}',
        'C': f'cc -std=c11 -Wall -Wextra -c {path} -o generated.o',
        'C++': f'c++ -std=c++17 -Wall -Wextra -c {path} -o generated.o',
        'JavaScript': f'node --check {path}',
        'TypeScript': 'tsc --project tsconfig.json',
        'Java': f'javac {path}',
        'C#': 'dotnet build HyunCalculator.Generated.csproj',
        'Swift': f'swiftc -parse {path}',
        'Kotlin': f'kotlinc {path} -d generated.jar',
        'Go': 'go test ./...',
        'Rust': f'rustc --edition 2021 --crate-type lib {path}',
        'R': f'Rscript -e \'source("{path}")\'',
        'MATLAB': f"matlab -batch \"addpath('source'); which('{filename[:-2]}')\"",
        'Julia': f'julia -e \'include("{path}")\'',
    }[language]


_TEST = '''"""Offline integrity check, NOT a numerical correctness certification."""
import ast
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class GeneratedBundleIntegrity(unittest.TestCase):
    def test_source_digest_and_metadata(self):
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        source = ROOT / manifest["source_file"]
        self.assertTrue(source.is_file())
        data = source.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), manifest["sha256"])
        self.assertFalse(manifest["runtime_verified"])

    def test_python_syntax_when_applicable(self):
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        if manifest["language"] == "Python":
            p = ROOT / manifest["source_file"]
            ast.parse(p.read_text(encoding="utf-8"), filename=p.name)

if __name__ == "__main__":
    unittest.main()
'''


def bundle_bytes(formula_id: str, options: GenerationOptions | None = None) -> bytes:
    """Create a repeatable ZIP in memory without running the generated source.

    Raises GenerationError for invalid formulas/language/options; does not write
    to disk, execute external tools, access the network or use arbitrary paths.
    """
    opt = options or GenerationOptions()
    formula = get_formula(formula_id)
    if formula is None or opt.language not in _SUPPORTED:
        raise GenerationError('Unknown formula or language')
    source = generate(formula_id, opt)  # full validation before filename use
    filename = _file_name(formula, opt)
    source_path = 'source/' + filename
    code = source.encode('utf-8')
    manifest = {
        'schema_version': 1,
        'generator_version': __version__,
        'formula_id': formula.id,
        'formula': formula.function,
        'language': opt.language,
        'source_file': source_path,
        'sha256': hashlib.sha256(code).hexdigest(),
        'options': asdict(opt),
        'runtime_verified': False,
        'verification_note': 'Source generated. Build, runtime and numerical parity are not certified by this archive.',
    }
    input_examples = {
        'formula_id': formula.id,
        'description': 'Original calculator example inputs; strings require type conversion for each generated language.',
        'fields': [{'name': key, 'example_text': example} for key, example in formula.fields],
    }
    readme = (
        f'# HyunCalculator generated project: {formula.id}\n\n'
        f'Formula: {formula.title_en}\n\n'
        f'Language: {opt.language}\n\n'
        f'Source file: `{source_path}`\n\n'
        '## Build or syntax check (requires a locally installed toolchain)\n\n'
        f'```sh\n{_command(opt.language, filename)}\n```\n\n'
        '## Files and test scope\n\n'
        '- `source/`: generated standalone implementation (may require libraries shown in requirements).\n'
        '- `examples/sample_inputs.json`: raw original calculator example fields, **not** executable test vectors.\n'
        '- `manifest.json`: generator metadata, options, SHA-256 digest, and verification status.\n'
        '- `tests/test_integrity.py`: source digest verification; Python also checks syntax.\n\n'
        'Run the offline integrity test with `python -m unittest discover -s tests -v`.\n\n'
        '**Important:** Passing this integrity test or a compiler check does not prove numerical correctness. '
        'Test output values and boundary conditions against an independent trusted reference before financial decisions.\n'
        'No network access, arbitrary downloaded code, or financial advice is provided by this export.\n'
    )
    files = {
        source_path: code,
        'README.md': readme.encode('utf-8'),
        'manifest.json': (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8'),
        'examples/sample_inputs.json': (json.dumps(input_examples, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8'),
        'tests/test_integrity.py': _TEST.encode('utf-8'),
    }
    for name, content in _extra_files(opt.language, source).items():
        files[name] = content.encode('utf-8')
    out = io.BytesIO()
    with zipfile.ZipFile(out, mode='w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in sorted(files.items()):
            # The archive never uses caller-supplied paths and is reproducible.
            info = zipfile.ZipInfo(name, _DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, content)
    return out.getvalue()
