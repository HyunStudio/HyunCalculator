"""Compile/run generated fixed-income and EWMA programs where toolchains exist.
No dependency on CI-installed toolchains: unavailable compilers are explicit SKIP.
"""
from __future__ import annotations
import math, subprocess, shutil, tempfile, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from hyuncalculator.codegen import generate, GenerationOptions
from hyuncalculator.quant import bond_metrics, ewma_volatility

CASES=[('BOND-001','bond',[1000.,0.05,0.04,5.,2],list(bond_metrics(1000.,0.05,0.04,5.,2).values())),
       ('TS-001','ewma',[[.01,-.02,.015,.005],.94],list(ewma_volatility([.01,-.02,.015,.005],.94).values()))]


def check(lang,formula,fn,vals,expected):
    src=generate(formula,GenerationOptions(language=lang))
    bond=formula=='BOND-001'
    scalar_args='1000.0,0.05,0.04,5.0,2' if bond else None
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        if lang=='C':
            call=f'{fn}({scalar_args})' if bond else f'{fn}((double[]){{.01,-.02,.015,.005}},4,.94)'
            code=src+'\n#include <stdio.h>\nint main(void){HyunResult r='+call+'; for(int i=0;i<'+str(len(expected))+';i++) printf("%.16g ",r.values[i]);}\n'
            (root/'a.c').write_text(code);cmds=[['gcc','-std=c11','-Wall','-Werror',str(root/'a.c'),'-lm','-o',str(root/'a')],[str(root/'a')]]
        elif lang=='C++':
            call=f'{fn}({scalar_args})' if bond else f'{fn}(std::vector<double>{{.01,-.02,.015,.005}},.94)'
            code=src+'\n#include <iostream>\nint main(){for(double x:'+call+')std::cout.precision(17),std::cout<<x<<" ";}\n'
            (root/'a.cpp').write_text(code);cmds=[['g++','-std=c++17','-Wall','-Werror',str(root/'a.cpp'),'-o',str(root/'a')],[str(root/'a')]]
        elif lang in ('JavaScript','TypeScript'):
            call=f'{fn}({scalar_args})' if bond else f'{fn}([.01,-.02,.015,.005],.94)'
            code=src+'\nconsole.log('+call+'.join(" "));\n'
            ext='ts' if lang=='TypeScript' else 'mjs'
            (root/('a.'+ext)).write_text(code)
            cmds=[['tsc','--target','ES2020','--module','commonjs','--outDir',td,str(root/'a.ts')],['node',str(root/'a.js')]] if lang=='TypeScript' else [['node',str(root/'a.mjs')]]
        elif lang=='Java':
            call=f'GeneratedCalculator.{fn}({scalar_args})' if bond else f'GeneratedCalculator.{fn}(new double[]{{.01,-.02,.015,.005}},.94)'
            code=src+'\nclass Driver{public static void main(String[]unused){for(double x:'+call+')System.out.print(x+" ");}}\n'
            (root/'GeneratedCalculator.java').write_text(code)
            cmds=[['javac',str(root/'GeneratedCalculator.java')],['java','-cp',td,'Driver']]
        elif lang=='Swift':
            call=f'{fn}({scalar_args})' if bond else f'{fn}([0.01,-0.02,0.015,0.005],0.94)'
            code=src+'\nfor x in '+call+' {print(x,terminator:" ")}\n'
            (root/'a.swift').write_text(code);cmds=[['swiftc',str(root/'a.swift'),'-o',str(root/'a')],[str(root/'a')]]
        elif lang=='Kotlin':
            call=f'{fn}({scalar_args})' if bond else f'{fn}(doubleArrayOf(0.01,-0.02,0.015,0.005),0.94)'
            code=src+'\nfun main(){for(x in '+call+') print("$x ")}\n'
            (root/'a.kt').write_text(code);cmds=[['kotlinc',str(root/'a.kt'),'-include-runtime','-d',str(root/'a.jar')],['java','-jar',str(root/'a.jar')]]
        elif lang=='Go':
            call=f'{fn}({scalar_args})' if bond else f'{fn}([]float64{{.01,-.02,.015,.005}},.94)'
            code=src.replace('import "math"','import "math"\nimport "fmt"')+'\nfunc main(){for _,x:=range '+call+' {fmt.Printf("%.17g ",x)}}\n'
            (root/'a.go').write_text(code);cmds=[['go','run',str(root/'a.go')]]
        else:raise AssertionError(lang)
        result=None
        for cmd in cmds:
            proc=subprocess.run(cmd,cwd=td,capture_output=True,text=True,timeout=80)
            if proc.returncode:raise RuntimeError(str(cmd[0])+': '+proc.stderr[:700])
            result=proc.stdout
        got=[float(x) for x in result.split()]
        if len(got)!=len(expected) or not all(math.isclose(x,y,abs_tol=1e-8,rel_tol=1e-8) for x,y in zip(got,expected)):
            raise AssertionError(f'{lang} {formula}: got {got}; expected {expected}')
        return got

if __name__=='__main__':
    failures=[];n=0
    for lang,tool in [('C','gcc'),('C++','g++'),('JavaScript','node'),('TypeScript','tsc'),('Java','javac'),('Swift','swiftc'),('Kotlin','kotlinc'),('Go','go')]:
        if not shutil.which(tool):print('SKIP',lang,flush=True);continue
        for case in CASES:
            try:
                got=check(lang,*case);n+=1;print('PASS',lang,case[0],got,flush=True)
            except Exception as exc:
                failures.append((lang,case[0],str(exc)));print('FAIL',lang,case[0],str(exc),flush=True)
    print('RESULT:',n,'passes,',len(failures),'failures',flush=True)
    if failures:sys.exit(1)
