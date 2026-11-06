"""Complete C/C++ representative numerical coverage alongside the 27-case suite."""
from __future__ import annotations
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from toolchain_js_full_numeric import CASES
from toolchain_ci_smoke import selected_cases
from hyuncalculator.codegen import generate, GenerationOptions
from hyuncalculator.codegen.registry import catalog

C_CALLS = {
 'STAT-001': 'HyunNormalResult r=normal(100,100,20,.95);',
 'STAT-002': 'double rvalues[18]; if(!cov((double[]){.05,.10,.08,.10,.02,.07,-.05,.03,.01,.02,-.04,.06},4,3,rvalues,18))return 2;',
 'BOND-001': 'HyunResult r=bond(1000,.05,.04,5,2);',
 'RISK-003': 'HyunPerformance r=performance((double[]){.05,-.02,.01,-.03,.04,.015},6,.001,252);',
 'TS-001': 'HyunResult r=ewma((double[]){.02,-.01,.03,.015,-.04},5,.94);',
 'STRAT-002': 'double rvalues[38]; if(!backtest((double[]){.02,-.01,.03,.01,-.02,.04},(double[]){1,1,-1,0,.5,0},6,3,2,.0001,252,rvalues,38))return 2;',
}

def check(language, case):
    fid, _, call, expected, tolerance = case
    source = generate(fid, GenerationOptions(language=language))
    if language == 'C':
        values = 'rvalues' if fid in ('STAT-002','STRAT-002') else 'r.values'
        driver = C_CALLS[fid] + f'for(int i=0;i<{len(expected)};i++)printf("%.17g\\n",{values}[i]);'
        source += '\n#include <stdio.h>\nint main(void){' + driver + 'return 0;}\n'
        compiler, suffix, standard = 'gcc', '.c', '-std=c11'
    else:
        call = call.replace('[','{').replace(']','}')
        source += '\n#include <iostream>\n#include <iomanip>\nint main(){std::cout<<std::setprecision(17);auto r=' + call + ';for(auto x:r)std::cout<<x<<"\\n";}\n'
        compiler, suffix, standard = 'g++', '.cpp', '-std=c++17'
    with tempfile.TemporaryDirectory(prefix='hyun_full_native_') as tmp:
        path = Path(tmp)
        src, exe = path / ('driver'+suffix), path / 'driver.exe'
        src.write_text(source, encoding='utf-8')
        for command in ([compiler,standard,'-Wall','-Werror',str(src),'-lm','-o',str(exe)], [str(exe)]):
            result = subprocess.run(command, capture_output=True,text=True,timeout=60)
            if result.returncode:
                raise AssertionError(result.stderr[-3000:] or f'exit {result.returncode}')
        actual = [float(x) for x in result.stdout.split()]
    if len(actual) != len(expected):
        raise AssertionError(f'output length {len(actual)} != {len(expected)}')
    for index, (a,b) in enumerate(zip(actual,expected)):
        if not math.isfinite(a) or not math.isfinite(b) or not math.isclose(a,b,rel_tol=tolerance,abs_tol=tolerance):
            raise AssertionError(f'field {index}: {a} != {b}')

def main():
    ids = [fid for fid,_ in selected_cases()] + [case[0] for case in CASES]
    if len(ids)!=33 or len(set(ids))!=33 or set(ids)!={f.id for f in catalog()}:
        raise AssertionError('Incomplete or duplicated native numerical catalog')
    for tool in ('gcc','g++'):
        if not shutil.which(tool):
            raise RuntimeError(f'Required compiler missing: {tool}')
    passed=0
    for language in ('C','C++'):
        for case in CASES:
            check(language,case)
            passed+=1
            print(f'PASS {language} {case[0]} ({len(case[3])} fields)',flush=True)
    print(f'REMAINING NATIVE SUMMARY: {passed}/12 numerical cases passed')

if __name__=='__main__':
    main()
