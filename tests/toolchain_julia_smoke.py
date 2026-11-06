"""Required Julia numeric smoke checks for generated source.

Six representative standalone formula-language examples; not 462-way coverage.
The Julia interpreter is mandatory: an absent runtime fails the job.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from toolchain_r_csharp_smoke import cases, verify_output
from hyuncalculator.codegen import generate, GenerationOptions


JULIA_ARGS = {
    'FIN-001': '1000,0.05,10',
    'FIN-006': '120000,0.005,24,12',
    'RISK-002': '0.001,0.02,0.95',
    'STAT-001': '1.5,0.2,1.1,0.95',
    'RISK-003': '[0.01,-0.02,0.03,0.015,-0.005],0.0001,252',
    'BOND-002': '1044.912925031211,1000,0.05,5,2',
}


from toolchain_smoke import CASES as SCALAR_CASES
JULIA_ARGS.update({fid: args for fid, fn, args, expected in SCALAR_CASES if fid != 'FIN-001'})


def check(formula, function, expected):
    with TemporaryDirectory(prefix='hyuncalc_julia_') as td:
        root = Path(td)
        (root / 'generated.jl').write_text(
            generate(formula, GenerationOptions(language='Julia')), encoding='utf-8')
        body = f'''include("generated.jl")
let result = {function}({JULIA_ARGS[formula]})
    vals = result isa Number ? [result] : result isa NamedTuple ? collect(values(result)) : collect(result)
    println("HYUN_RESULT ", join(string.(Float64.(vals)), " "))
end
'''
        (root / 'check.jl').write_text(body, encoding='utf-8')
        process = subprocess.run(
            ['julia', '--startup-file=no', '--color=no', str(root / 'check.jl')],
            cwd=root, capture_output=True, text=True, timeout=150, check=False)
        if process.returncode:
            raise AssertionError(f'Julia error: {process.stderr[-3000:]} {process.stdout[-700:]}')
        return verify_output(process.stdout, expected, formula, 'Julia')


def main():
    if shutil.which('julia') is None:
        raise SystemExit('FAIL: julia interpreter is required for the Julia CI job')
    passed = 0
    failed = []
    for formula, function, _rargs, _csargs, expected in cases():
        try:
            got = check(formula, function, expected)
            passed += 1
            print('PASS Julia', formula, got[:3], flush=True)
        except Exception as exc:
            failed.append((formula, str(exc)))
            print('FAIL Julia', formula, str(exc)[:2000], flush=True)
    print(f'JULIA NATIVE NUMERIC SUMMARY: {passed} PASS; {len(failed)} FAIL; {len(cases())} planned cases', flush=True)
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
