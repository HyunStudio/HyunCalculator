"""Optional real compiler and reference comparison for Black–Scholes/Greeks.

Runs representative call and put examples and the zero-volatility edge case.
Missing toolchains are skipped (not counted as passes).
"""
from __future__ import annotations
import math,subprocess,shutil,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hyuncalculator.codegen import generate,GenerationOptions
from hyuncalculator.quant import black_scholes

CASES=[(100.,100.,1.,.05,.2,0.,'call'),(100.,110.,.5,.03,.45,.01,'put'),(120.,100.,1.,.01,0.,0.,'call')]


def check(lang, case):
    src=generate('DERIV-001',GenerationOptions(language=lang));fn='bs'
    *xs,opt=case; params=','.join(str(x) for x in xs)
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)
        if lang=='C':
            c='HyunResult r=bs('+params+',"'+opt+'");for(int i=0;i<6;i++)printf("%.17g ",r.values[i]);'
            (p/'a.c').write_text(src+'\n#include <stdio.h>\nint main(void){'+c+'}\n')
            cmds=[['gcc','-std=c11','-Wall','-Werror',str(p/'a.c'),'-lm','-o',str(p/'a')],[str(p/'a')]]
        elif lang=='C++':
            c='auto v=bs('+params+',"'+opt+'");for(double x:v)std::cout<<x<<" ";'
            (p/'a.cpp').write_text(src+'\n#include <iostream>\n#include <iomanip>\nint main(){std::cout<<std::setprecision(17);'+c+'}\n')
            cmds=[['g++','-std=c++17','-Wall','-Werror',str(p/'a.cpp'),'-o',str(p/'a')],[str(p/'a')]]
        elif lang in ('JavaScript','TypeScript'):
            c='console.log(bs('+params+',"'+opt+'").join(" "));'
            f='a.ts' if lang=='TypeScript' else 'a.mjs';(p/f).write_text(src+'\n'+c+'\n')
            cmds=([['tsc','--target','ES2020','--module','commonjs','--outDir',tmp,str(p/f)],['node',str(p/'a.js')]] if lang=='TypeScript' else [['node',str(p/f)]])
        elif lang=='Java':
            c='for(double x:GeneratedCalculator.bs('+params+',"'+opt+'"))System.out.print(x+" ");'
            (p/'GeneratedCalculator.java').write_text(src+'\nclass Driver{public static void main(String[]unused){'+c+'}}\n')
            cmds=[['javac',str(p/'GeneratedCalculator.java')],['java','-cp',tmp,'Driver']]
        elif lang=='Swift':
            c='for x in bs('+params+',"'+opt+'") {print(x,terminator:" ")}'
            (p/'a.swift').write_text(src+'\n'+c+'\n');cmds=[['swiftc',str(p/'a.swift'),'-o',str(p/'a')],[str(p/'a')]]
        elif lang=='Kotlin':
            c='for(x in bs('+params+',"'+opt+'"))print("$x ")'
            (p/'a.kt').write_text(src+'\nfun main(){'+c+'}\n');cmds=[['kotlinc',str(p/'a.kt'),'-include-runtime','-d',str(p/'a.jar')],['java','-jar',str(p/'a.jar')]]
        elif lang=='Go':
            c='for _,x:=range bs('+params+',"'+opt+'") {fmt.Printf("%.17g ",x)}'
            (p/'a.go').write_text(src.replace('import "math"','import "math"\nimport "fmt"')+'\nfunc main(){'+c+'}\n');cmds=[['go','run',str(p/'a.go')]]
        elif lang=='Rust':
            c='for x in bs('+params+',"'+opt+'") {print!("{x:.17} ")}'
            (p/'a.rs').write_text(src+'\nfn main(){'+c+'}\n');cmds=[['rustc','--edition','2021',str(p/'a.rs'),'-o',str(p/'a')],[str(p/'a')]]
        else:raise AssertionError(lang)
        output=''
        for cmd in cmds:
            r=subprocess.run(cmd,cwd=tmp,capture_output=True,text=True,timeout=80)
            if r.returncode:raise AssertionError(f'{lang} {cmd[0]}: {r.stderr[:1200]}')
            output=r.stdout
        got=[float(x) for x in output.split()]
        exp=list(black_scholes(*xs[:5],dividend=xs[5],option=opt).values())
        if len(got)!=6 or any(not (math.isnan(a) and math.isnan(b) or math.isclose(a,b,abs_tol=2e-9,rel_tol=2e-9)) for a,b in zip(got,exp)):
            raise AssertionError(f'{lang} {case}: {got} vs {exp}')
        return got

if __name__=='__main__':
    errors=[]
    for l,tool in [('C','gcc'),('C++','g++'),('JavaScript','node'),('TypeScript','tsc'),('Java','javac'),('Swift','swiftc'),('Kotlin','kotlinc'),('Go','go'),('Rust','rustc')]:
        if not shutil.which(tool):print('SKIP',l,flush=True);continue
        for case in CASES:
            try:print('PASS',l,case[-1],check(l,case)[:2],flush=True)
            except Exception as e:errors.append((l,str(e)));print('FAIL',l,str(e),flush=True)
    if errors:sys.exit(1)
