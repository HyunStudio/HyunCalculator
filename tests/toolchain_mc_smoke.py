"""Optional real toolchain smoke tests for antithetic MC, not CI prerequisites.

The portable LCG stream is independently reproduced in test_codegen_mc.py.
Missing toolchains are SKIP, not PASS. Build/runtime results are separate from
source-generation coverage and Python unit tests.
"""
from __future__ import annotations

import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hyuncalculator.codegen import generate, GenerationOptions
from test_codegen_mc import reference_portable

CASES = [
    ('call', 4000, 42),
    ('put', 4000, 4567),
    ('call', 100, 17),
]


def run_one(language, option, paths, seed):
    code=generate('DERIV-003',GenerationOptions(language=language))
    with tempfile.TemporaryDirectory() as directory:
        p=Path(directory)
        if language=='C':
            file=p/'mc.c'
            file.write_text(code+f'''
#include <stdio.h>
int main(void){{HyunMCResult a=mc(100,100,1,.05,.2,0,"{option}",{paths},{seed});printf("%.17g %.17g %.17g %.17g",a.price,a.paired_se,a.ci_low,a.ci_high);}}
''')
            cmds=[['gcc','-std=c11','-Wall','-Wextra','-Werror',str(file),'-lm','-o',str(p/'mc')],[str(p/'mc')]]
        elif language=='C++':
            file=p/'mc.cpp'
            file.write_text(code+f'''
#include <iostream>
#include <iomanip>
int main(){{auto a=mc(100,100,1,.05,.2,0,"{option}",{paths},{seed});for(auto v:a)std::cout<<std::setprecision(17)<<v<<" ";}}
''')
            cmds=[['g++','-std=c++17','-Wall','-Wextra','-Werror',str(file),'-o',str(p/'mc')],[str(p/'mc')]]
        elif language=='JavaScript':
            file=p/'mc.mjs'
            file.write_text(code+f'\nconsole.log(mc(100,100,1,.05,.2,0,"{option}",{paths},{seed}).join(" "));\n')
            cmds=[['node',str(file)]]
        elif language=='TypeScript':
            file=p/'mc.ts'
            file.write_text(code+f'\nconsole.log(mc(100,100,1,.05,.2,0,"{option}",{paths},{seed}).join(" "));\n')
            cmds=[['tsc','--target','ES2020','--module','commonjs','--outDir',directory,str(file)],['node',str(p/'mc.js')]]
        elif language=='Java':
            file=p/'GeneratedCalculator.java'
            file.write_text(code+f'''
class Runner{{public static void main(String[]args){{for(double x:GeneratedCalculator.mc(100,100,1,.05,.2,0,"{option}",{paths},{seed}L))System.out.print(x+" ");}}}}
''')
            cmds=[['javac',str(file)],['java','-cp',directory,'Runner']]
        elif language=='Swift':
            file=p/'mc.swift'
            file.write_text(code+f'\nfor x in mc(100,100,1,0.05,0.2,0,"{option}",{paths},{seed}){{print(x,terminator:" ")}}\n')
            cmds=[['swiftc',str(file),'-o',str(p/'mc')],[str(p/'mc')]]
        elif language=='Kotlin':
            file=p/'mc.kt'
            file.write_text(code+f'\nfun main(){{for(x in mc(100.0,100.0,1.0,0.05,0.2,0.0,"{option}",{paths},{seed}L))print("$x ")}}\n')
            cmds=[['kotlinc',str(file),'-include-runtime','-d',str(p/'mc.jar')],['java','-jar',str(p/'mc.jar')]]
        elif language=='Go':
            file=p/'mc.go'
            file.write_text(code.replace('import "math"','import ("math";"fmt")')+f'\nfunc main(){{for _,v:=range mc(100,100,1,.05,.2,0,"{option}",{paths},{seed}){{fmt.Printf("%.17g ",v)}}}}\n')
            cmds=[['go','run',str(file)]]
        elif language=='Rust':
            file=p/'mc.rs'
            file.write_text(code+f'\nfn main(){{for v in mc(100.0,100.0,1.0,0.05,0.2,0.0,"{option}",{paths},{seed}){{print!("{{:.17}} ",v)}}}}\n')
            cmds=[['rustc','-D','warnings',str(file),'-o',str(p/'mc')],[str(p/'mc')]]
        else:raise ValueError(language)
        for command in cmds:
            result=subprocess.run(command,cwd=directory,capture_output=True,text=True,timeout=75)
            if result.returncode:raise RuntimeError(f'{command[0]}: {result.stderr[:3000]} {result.stdout[:500]}')
        values=[float(v) for v in result.stdout.split()]
        expected=reference_portable(option=option,paths=paths,seed=seed)
        assert len(values)==4, (language,values)
        for i,(actual,target) in enumerate(zip(values,expected)):
            if not math.isclose(actual,target,rel_tol=2e-11,abs_tol=2e-11):
                raise AssertionError(f'{language}/{option}/{paths}/{seed} index {i}: actual={actual}, expected={target}')
        return values


if __name__=='__main__':
    failures=[]
    for lang,tool in [('C','gcc'),('C++','g++'),('JavaScript','node'),('TypeScript','tsc'),('Java','javac'),('Swift','swiftc'),('Kotlin','kotlinc'),('Go','go'),('Rust','rustc')]:
        if not shutil.which(tool):print('SKIP',lang,'no toolchain',flush=True);continue
        for option,paths,seed in CASES:
            try:
                print('PASS',lang,option,paths,seed,run_one(lang,option,paths,seed)[0],flush=True)
            except Exception as exc:
                print('FAIL',lang,option,paths,seed,str(exc),flush=True)
                failures.append((lang,option,str(exc)))
    if failures:sys.exit(1)
