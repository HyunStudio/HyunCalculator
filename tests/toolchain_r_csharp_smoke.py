"""Required native R and C# smoke tests for independent generated programs.

Runs selected formula-language pairs against the established Python quantitative
reference. Missing runtimes, compilation problems, invalid output and numeric
mismatches are all failures. This is NOT complete 462-pair certification.

Usage: python tests/toolchain_r_csharp_smoke.py --language R
       python tests/toolchain_r_csharp_smoke.py --language C#
"""
from __future__ import annotations

import argparse
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hyuncalculator.codegen import GenerationOptions, generate
from hyuncalculator.finance import future_value, amortization
from hyuncalculator.quant import (normal_probabilities, normal_var_es,
                                  risk_metrics, yield_to_maturity)


RETURNS = [.01, -.02, .03, .015, -.005]


def cases():
    from toolchain_smoke import CASES as scalar_cases
    extra = []
    for fid, fn, args, expected in scalar_cases:
        if fid == 'FIN-001':
            continue
        rargs = args.replace('[-100,60,60]', 'c(-100,60,60)')
        csargs = args.replace('[-100,60,60]', 'new double[]{-100,60,60}')
        extra.append((fid, fn, rargs, csargs, [expected]))
    return extra + [
        ('FIN-001', 'fv', '1000,0.05,10', '1000,0.05,10',
         [float(future_value(1000, .05, 10))]),
        ('FIN-006', 'loan', '120000,0.005,24,12', '120000,0.005,24,12',
         list(amortization(120000, .005, 24, 12).values())),
        ('RISK-002', 'normal_var', '0.001,0.02,0.95', '0.001,0.02,0.95',
         list(normal_var_es(.001, .02, .95).values())),
        ('STAT-001', 'normal', '1.5,0.2,1.1,0.95', '1.5,0.2,1.1,0.95',
         list(normal_probabilities(1.5, .2, 1.1, .95).values())),
        ('RISK-003', 'performance', 'c(0.01,-0.02,0.03,0.015,-0.005),0.0001,252',
         'new double[]{0.01,-0.02,0.03,0.015,-0.005},0.0001,252',
         list(risk_metrics(RETURNS, .0001, 252).values())),
        ('BOND-002', 'ytm', '1044.912925031211,1000,0.05,5,2',
         '1044.912925031211,1000,0.05,5,2',
         [float(yield_to_maturity(1044.912925031211, 1000, .05, 5, 2))]),
    ]


def run_checked(cmd, cwd, timeout=90):
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True,
                            timeout=timeout, check=False)
    if result.returncode:
        raise AssertionError(f'{" ".join(map(str,cmd))} exit={result.returncode}: '
                             f'{result.stderr[-3000:]} {result.stdout[-1200:]}')
    return result.stdout


def verify_output(output, expected, formula, language):
    # Compile/build output may contain restore messages; only parse the tagged line.
    matches = [line.split('HYUN_RESULT ', 1)[1].strip()
               for line in output.splitlines() if line.startswith('HYUN_RESULT ')]
    if len(matches) != 1:
        raise AssertionError(f'{language} {formula}: missing/extra result marker in {output[-1200:]}')
    got = [float(item) for item in matches[0].split()]
    if len(got) != len(expected):
        raise AssertionError(f'{formula}: expected {len(expected)} values, got {got}')
    for i, (actual, reference) in enumerate(zip(got, expected)):
        if math.isnan(reference):
            if not math.isnan(actual):
                raise AssertionError(f'{formula}[{i}] expected NaN, got {actual}')
        elif not math.isclose(actual, reference, rel_tol=3e-7, abs_tol=3e-7):
            raise AssertionError(f'{language} {formula}[{i}]: {actual} != {reference}')
    return got


def check_r(formula, function, r_args, expected):
    with TemporaryDirectory(prefix='hyuncalc_R_') as temp:
        root = Path(temp)
        source = generate(formula, GenerationOptions(language='R'))
        (root / 'generated.R').write_text(source, encoding='utf-8')
        code = ("source('generated.R')\n"
                f"v <- {function}({r_args})\n"
                "cat('HYUN_RESULT ', paste(sprintf('%.17g', as.numeric(v)), collapse=' '), '\\n', sep='')\n")
        (root / 'test.R').write_text(code, encoding='utf-8')
        output = run_checked(['Rscript', '--vanilla', 'test.R'], root)
        return verify_output(output, expected, formula, 'R')


def check_csharp(formula, function, cs_args, expected):
    with TemporaryDirectory(prefix='hyuncalc_CSharp_') as temp:
        root = Path(temp)
        source = generate(formula, GenerationOptions(language='C#'))
        (root / 'GeneratedCalculator.cs').write_text(source, encoding='utf-8')
        project = '''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <RestoreIgnoreFailedSources>true</RestoreIgnoreFailedSources>
  </PropertyGroup>
</Project>
'''
        (root / 'HyunSmoke.csproj').write_text(project, encoding='utf-8')
        call = f'GeneratedCalculator.{function}({cs_args})'
        # Scalar output and vector output must both be converted into invariant
        # round-trip representations before comparisons.
        if formula.startswith('FIN-') and formula != 'FIN-006' or formula == 'BOND-002':
            call = f'new double[]{{{call}}}'
        program = '''using System;
using System.Globalization;
using System.Linq;
var values = CALL;
Console.WriteLine("HYUN_RESULT " + string.Join(" ", values.Select(x => x.ToString("R", CultureInfo.InvariantCulture))));
'''.replace('CALL', call)
        (root / 'Program.cs').write_text(program, encoding='utf-8')
        output = run_checked(['dotnet', 'run', '--project', str(root / 'HyunSmoke.csproj'),
                              '--configuration', 'Release', '--no-launch-profile',
                              '--verbosity', 'quiet'], root, timeout=150)
        return verify_output(output, expected, formula, 'C#')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', choices=('R', 'C#'), required=True)
    args = parser.parse_args()
    exe = 'Rscript' if args.language == 'R' else 'dotnet'
    if shutil.which(exe) is None:
        raise SystemExit(f'FAIL: required {exe} executable is missing; never report an absent runtime as success')
    failures = []
    passed = 0
    for formula, fn, r_args, cs_args, reference in cases():
        try:
            if args.language == 'R':
                actual = check_r(formula, fn, r_args, reference)
            else:
                actual = check_csharp(formula, fn, cs_args, reference)
            print(f'PASS {args.language} {formula} {actual[:3]}', flush=True)
            passed += 1
        except Exception as exc:
            failures.append((formula, str(exc)))
            print(f'FAIL {args.language} {formula} {str(exc)[:2000]}', flush=True)
    print(f'{args.language} NATIVE NUMERIC SUMMARY: {passed} PASS; {len(failures)} FAIL; '
          f'{len(cases())} planned cases', flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()