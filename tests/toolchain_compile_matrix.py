"""Compile or syntax-check the complete 33-formula generation catalog.

This intentionally checks *source buildability*, NOT numerical correctness.
Each formula is compiled in isolation to avoid helper-name collisions.
A missing toolchain or a failed generation/build is counted as FAILURE.

Usage:
    python tests/toolchain_compile_matrix.py --language C
    python tests/toolchain_compile_matrix.py --language 'C++'
    python tests/toolchain_compile_matrix.py --language JavaScript
    python tests/toolchain_compile_matrix.py --language TypeScript
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hyuncalculator.codegen import GenerationOptions, generate
from hyuncalculator.codegen.registry import catalog

# Explicit, frozen compiler settings.  Syntax/build checks are not execution.
COMMANDS = {
    'C': ('gcc', 'generated.c', ('gcc', '-std=c11', '-pedantic-errors', '-fsyntax-only')),
    'C++': ('g++', 'generated.cpp', ('g++', '-std=c++17', '-pedantic-errors', '-fsyntax-only')),
    'JavaScript': ('node', 'generated.js', ('node', '--check')),
    'TypeScript': ('tsc', 'generated.ts', ('tsc', '--noEmit', '--target', 'ES2020',
                                           '--lib', 'ES2020,DOM', '--skipLibCheck')),
    'Java': ('javac', 'GeneratedCalculator.java', ('javac', '-encoding', 'UTF-8')),
    'Go': ('go', 'generated.go', ('go', 'test')),
    'Rust': ('rustc', 'generated.rs', ('rustc', '--edition=2021', '--crate-type=lib',
                                      '--emit=metadata', '-o', 'generated.rmeta')),
    'Swift': ('swiftc', 'generated.swift', ('swiftc', '-typecheck')),
    'Python': ('python', 'generated.py', ('python', '-m', 'py_compile')),
    'R': ('Rscript', 'generated.R', ('Rscript', '--vanilla', '-e', "parse(file='generated.R')")),
    'C#': ('dotnet', 'GeneratedCalculator.cs', ('dotnet', 'build', 'HyunGenerated.csproj',
                     '--configuration', 'Release', '--verbosity', 'quiet', '--nologo')),
    'Kotlin': ('kotlinc', 'generated.kt', ('kotlinc', '-d', 'generated.jar')),
    'Julia': ('julia', 'generated.jl', ('julia', '--startup-file=no', '--color=no',
                     '--compile=min', '-e', 'function validate(x); if x isa Expr; x.head in (:error, :incomplete) && error("Julia parse error: $x"); foreach(validate, x.args); end; end; validate(Meta.parseall(read("generated.jl", String)))')),
    # MATLAB output parsed in GNU Octave; this is NOT a MathWorks MATLAB compiler.
    'MATLAB': ('octave-cli', 'generated.m',
               ('octave-cli', '--quiet', '--no-gui', '--eval',
                "source('generated.m');")),
}


def check(formula_id: str, language: str) -> None:
    executable, filename, command = COMMANDS[language]
    # All 33 formulas must emit nontrivial standalone source.  No missing
    # language/formula profile is silently excluded from this matrix.
    source = generate(formula_id, GenerationOptions(language=language))
    if not source or not source.strip():
        raise AssertionError('generated source is empty')
    with tempfile.TemporaryDirectory(prefix='hyuncalc_compile_') as temp:
        root = Path(temp)
        source_file = root / filename
        source_file.write_text(source, encoding='utf-8')
        if language == 'C#':
            (root / 'HyunGenerated.csproj').write_text(
                '<Project Sdk="Microsoft.NET.Sdk">\n'
                '  <PropertyGroup>\n'
                '    <TargetFramework>net8.0</TargetFramework>\n'
                '    <OutputType>Library</OutputType>\n'
                '    <RestoreIgnoreFailedSources>true</RestoreIgnoreFailedSources>\n'
                '  </PropertyGroup>\n'
                '</Project>\n', encoding='utf-8',
            )
        # Octave's source() executes the function file, and therefore would
        # incorrectly call generated functions without input arguments.
        # Instead wrap generated definitions in an otherwise-empty function:
        # invoking only this wrapper forces the Octave parser to check all
        # nested function bodies without executing the financial functions.
        if language == 'MATLAB':
            (root / 'hyun_syntax_probe.m').write_text(
                'function hyun_syntax_probe()\n' + source + '\nend\n',
                encoding='utf-8',
            )
        # Rscript evaluates parse() only (no user-generated functions are called).
        # dotnet builds a distinct library to avoid public class name collisions.
        if language == 'MATLAB':
            cmd = [*command[:-1], 'hyun_syntax_probe();']
        elif language in ('R', 'C#', 'Julia'):
            cmd = list(command)
        else:
            cmd = [*command, filename]
        result = subprocess.run(
            cmd, cwd=root, capture_output=True,
            text=True, timeout=120 if language in ('C#', 'Kotlin') else 60, check=False,
        )
        if result.returncode:
            raise AssertionError(
                f'{executable} exited {result.returncode}: '
                f'{result.stderr[-4000:]} {result.stdout[-1000:]}'
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language', choices=tuple(COMMANDS), required=True)
    args = parser.parse_args()
    executable = COMMANDS[args.language][0]
    if shutil.which(executable) is None:
        parser.error(f'Missing required toolchain: {executable}. No silent skips.')

    formulas = catalog()
    if len(formulas) != 33 or len({f.id for f in formulas}) != 33:
        raise AssertionError('Formula registry changed: expected 33 unique IDs')
    checked = 0
    failed = []
    for formula in formulas:
        try:
            check(formula.id, args.language)
            checked += 1
            print(f'PASS compile {args.language} {formula.id}', flush=True)
        except Exception as exc:
            failed.append((formula.id, str(exc)))
            print(f'FAIL compile {args.language} {formula.id}: {exc}', flush=True)
    print(
        f'COMPILER MATRIX SUMMARY: {args.language} {checked} PASS; '
        f'{len(failed)} FAIL; {len(formulas)} planned formulas; '
        'source syntax/build only (NOT numerical execution)', flush=True,
    )
    if failed:
        raise SystemExit(1)
    return checked


if __name__ == '__main__':
    main()
