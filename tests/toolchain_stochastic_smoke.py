"""Optional toolchain tests for stochastic-path formula emission.

Run from project root: python tests/toolchain_stochastic_smoke.py
"""
from __future__ import annotations
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from hyuncalculator.codegen import generate, GenerationOptions

CASES = {
    'STOCH-003': ('brownian', '1,4,50,42,0.5,0.07,0.2', (1.,4,50,42,.5,.07,.2)),
    'STOCH-004': ('gbm_paths', '100,0.07,0.2,1,4,50,42', (100.,.07,.2,1,4,50,42)),
    'STOCH-005': ('ou_paths', '2,1,0.8,0.2,1,4,50,42', (2.,1.,.8,.2,1,4,50,42)),
}


def reference(formula_id, args):
    if formula_id=='STOCH-003':years,steps,paths,seed,initial,mu,sigma=args
    elif formula_id=='STOCH-004':initial,mu,sigma,years,steps,paths,seed=args
    else:initial,level,kappa,sigma,years,steps,paths,seed=args
    steps,paths,seed=int(steps),int(paths),int(seed)
    dt=years/steps
    if formula_id=='STOCH-003':
        tm=initial+mu*years;ts=sigma*math.sqrt(years)
        d=mu*dt;n=sigma*math.sqrt(dt)
    elif formula_id=='STOCH-004':
        tm=initial*math.exp(mu*years);ts=tm*math.sqrt(math.exp(sigma*sigma*years)-1)
        d=(mu-.5*sigma*sigma)*dt;n=sigma*math.sqrt(dt)
    else:
        tm=level+(initial-level)*math.exp(-kappa*years)
        ts=sigma*math.sqrt((1-math.exp(-2*kappa*years))/(2*kappa))
        d=math.exp(-kappa*dt);n=sigma*math.sqrt((1-math.exp(-2*kappa*dt))/(2*kappa))
    rng=seed;mean=m2=0.;samples=[]
    for p in range(paths):
        val=initial
        if p==0:samples.append(val)
        for j in range(steps):
            rng=(rng*16807)%2147483647;u1=rng/2147483647
            rng=(rng*16807)%2147483647;u2=rng/2147483647
            z=math.sqrt(-2*math.log(u1))*math.cos(2*math.pi*u2)
            if formula_id=='STOCH-003':val=val+d+n*z
            elif formula_id=='STOCH-004':val=val*math.exp(d+n*z)
            else:val=level+(val-level)*d+n*z
            if p==0:samples.append(val)
        delta=val-mean;mean+=delta/(p+1);m2+=delta*(val-mean)
    return [tm,ts,mean,math.sqrt(m2/(paths-1)),*samples]


def check_toolchain(lang, fid, extra_args=None):
    fn,args,values=CASES[fid]
    args=extra_args or args
    code=generate(fid,GenerationOptions(language=lang))
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)
        if lang=='C':
            src=p/'m.c';src.write_text(code+f'\n#include <stdio.h>\nint main(void){{HyunPathResult a={fn}({args});for(int i=0;i<a.length;i++)printf("%.17g ",a.values[i]);}}\n')
            commands=[['gcc','-std=c11','-Wall','-Wextra','-Werror',str(src),'-lm','-o',str(p/'run')],[str(p/'run')]]
        elif lang=='C++':
            src=p/'m.cpp';src.write_text(code+f'\n#include <iostream>\n#include <iomanip>\nint main(){{auto a={fn}({args});for(auto v:a)std::cout<<std::setprecision(17)<<v<<" ";}}\n')
            commands=[['g++','-std=c++17','-Wall','-Wextra','-Werror',str(src),'-o',str(p/'run')],[str(p/'run')]]
        elif lang=='JavaScript':
            src=p/'m.mjs';src.write_text(code+f'\nconsole.log({fn}({args}).join(" "));\n');commands=[['node',str(src)]]
        elif lang=='TypeScript':
            src=p/'m.ts';src.write_text(code+f'\nconsole.log({fn}({args}).join(" "));\n')
            commands=[['tsc','--target','ES2020','--module','commonjs','--outDir',str(p),str(src)],['node',str(p/'m.js')]]
        elif lang=='Java':
            src=p/'GeneratedCalculator.java';src.write_text(code+f'\nclass Runner{{public static void main(String[]x){{for(double v:GeneratedCalculator.{fn}({args}))System.out.print(v+" ");}}}}\n')
            commands=[['javac',str(src)],['java','-cp',str(p),'Runner']]
        elif lang=='Swift':
            src=p/'m.swift';src.write_text(code+f'\nfor v in {fn}({args}){{print(v,terminator:" ")}}\n')
            commands=[['swiftc',str(src),'-o',str(p/'run')],[str(p/'run')]]
        elif lang=='Kotlin':
            src=p/'m.kt';vs=args.rsplit(',',1)[0].split(',');seed=args.rsplit(',',1)[-1]
            # language-specific Double and Long suffixes; paths/steps are Int.
            if fid=='STOCH-003':kargs='1.0,4,50,42L,0.5,0.07,0.2'
            elif fid=='STOCH-004':kargs='100.0,0.07,0.2,1.0,4,50,42L'
            else:kargs='2.0,1.0,0.8,0.2,1.0,4,50,42L'
            src.write_text(code+f'\nfun main(){{for(v in {fn}({kargs}))print("$v ")}}\n')
            commands=[['kotlinc',str(src),'-include-runtime','-d',str(p/'run.jar')],['java','-jar',str(p/'run.jar')]]
        elif lang=='Go':
            src=p/'m.go';src.write_text(code.replace('import "math"','import ("math";"fmt")')+f'\nfunc main(){{for _,v:=range {fn}({args}){{fmt.Printf("%.17g ",v)}}}}\n')
            commands=[['go','run',str(src)]]
        else:raise ValueError(lang)
        for cmd in commands:
            result=subprocess.run(cmd,cwd=str(p),capture_output=True,text=True,timeout=85)
            if result.returncode:raise AssertionError(f'{lang}/{fid}: {cmd[0]}\n{result.stderr[:3000]}')
        actual=[float(v) for v in result.stdout.split()]
        expected=reference(fid,values)
        if len(actual)!=len(expected):raise AssertionError((lang,fid,len(actual),len(expected),result.stdout[:1000]))
        for i,(a,b) in enumerate(zip(actual,expected)):
            if not math.isclose(a,b,abs_tol=3e-9,rel_tol=3e-9):
                raise AssertionError((lang,fid,i,a,b))
        return actual

if __name__=='__main__':
    import sys
    langs=sys.argv[1:] or ['C','C++','JavaScript','TypeScript','Java','Swift','Kotlin','Go']
    failures=[]
    for lang in langs:
        exe={'C':'gcc','C++':'g++','JavaScript':'node','TypeScript':'tsc','Java':'javac','Swift':'swiftc','Kotlin':'kotlinc','Go':'go'}[lang]
        if not shutil.which(exe):print('SKIP',lang,'not installed',flush=True);continue
        for fid in CASES:
            try:
                actual=check_toolchain(lang,fid)
                print('PASS',lang,fid,len(actual),actual[:4],flush=True)
            except Exception as exc:
                print('FAIL',lang,fid,str(exc)[:2000],flush=True);failures.append((lang,fid,str(exc)))
    if failures:sys.exit(1)
