"""Opt-in real toolchain smoke tests of generated Black-Litterman math.

Requires individual compilers; does not claim coverage for missing toolchains.
Checks equilibrium, posterior and full predictive covariance against NumPy.
"""
from __future__ import annotations
import math,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hyuncalculator.codegen import generate,GenerationOptions
from hyuncalculator.quant import black_litterman

cov=[[.04,.01],[.01,.09]];market=[.6,.4];p=[[1.,-1.]];q=[.02];omega=[.001];delta=2.5;tau=.05
ref=black_litterman(cov,market,delta,tau,p,q,omega)
expected=list(ref['Equilibrium returns'])+list(ref['Posterior expected returns'])+list(ref['Posterior predictive covariance'].flatten())

def smoke(lang):
    src=generate('ALLOC-003',GenerationOptions(language=lang))
    fn='bl'
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)
        if lang=='C':
            (path/'m.c').write_text(src+f'''
#include <stdio.h>
int main(void){{double out[8];int rc={fn}((double[]){{.04,.01,.01,.09}},(double[]){{.6,.4}},2,2.5,.05,(double[]){{1,-1}},1,(double[]){{.02}},(double[]){{.001}},out);if(rc)return 4;for(int i=0;i<8;i++)printf("%.17g ",out[i]);return 0;}}
''')
            cmds=[['gcc','-std=c11','-Wall','-Werror',str(path/'m.c'),'-lm','-o',str(path/'m')],[str(path/'m')]]
        elif lang=='C++':
            (path/'m.cpp').write_text(src+f'''
#include <iostream>
#include <iomanip>
int main(){{auto a={fn}({{{{.04,.01}},{{.01,.09}}}},{{.6,.4}},2.5,.05,{{{{1,-1}}}},{{.02}},{{.001}});for(double v:a)std::cout<<std::setprecision(17)<<v<<" ";}}
''')
            cmds=[['g++','-std=c++17','-Wall','-Werror',str(path/'m.cpp'),'-o',str(path/'m')],[str(path/'m')]]
        elif lang in ('JavaScript','TypeScript'):
            ext='ts' if lang=='TypeScript' else 'mjs'
            (path/f'm.{ext}').write_text(src+f'\nconsole.log({fn}([[.04,.01],[.01,.09]],[.6,.4],2.5,.05,[[1,-1]],[.02],[.001]).join(" "));')
            cmds=[['tsc','--target','ES2020','--module','commonjs','--outDir',tmp,str(path/'m.ts')],['node',str(path/'m.js')]] if lang=='TypeScript' else [['node',str(path/'m.mjs')]]
        elif lang=='Java':
            (path/'GeneratedCalculator.java').write_text(src+f'\nclass Runner {{public static void main(String[]args){{for(double v:GeneratedCalculator.{fn}(new double[][]{{{{.04,.01}},{{.01,.09}}}},new double[]{{.6,.4}},2.5,.05,new double[][]{{{{1,-1}}}},new double[]{{.02}},new double[]{{.001}}))System.out.print(v+" ");}}}}')
            cmds=[['javac',str(path/'GeneratedCalculator.java')],['java','-cp',tmp,'Runner']]
        elif lang=='Swift':
            (path/'m.swift').write_text(src+f'\nfor v in try! {fn}([[0.04,0.01],[0.01,0.09]],[0.6,0.4],2.5,0.05,[[1.0,-1.0]],[0.02],[0.001]) {{print(v,terminator:" ")}}')
            cmds=[['swiftc',str(path/'m.swift'),'-o',str(path/'m')],[str(path/'m')]]
        elif lang=='Kotlin':
            (path/'m.kt').write_text(src+f'\nfun main(){{for(v in {fn}(arrayOf(doubleArrayOf(.04,.01),doubleArrayOf(.01,.09)),doubleArrayOf(.6,.4),2.5,.05,arrayOf(doubleArrayOf(1.0,-1.0)),doubleArrayOf(.02),doubleArrayOf(.001)))print("$v ")}}')
            cmds=[['kotlinc',str(path/'m.kt'),'-include-runtime','-d',str(path/'m.jar')],['java','-jar',str(path/'m.jar')]]
        elif lang=='Go':
            (path/'m.go').write_text(src.replace('import "math"','import ("math";"fmt")')+f'\nfunc main(){{for _,v:=range {fn}([][]float64{{{{.04,.01}},{{.01,.09}}}},[]float64{{.6,.4}},2.5,.05,[][]float64{{{{1,-1}}}},[]float64{{.02}},[]float64{{.001}}){{fmt.Printf("%.17g ",v)}}}}')
            cmds=[['go','run',str(path/'m.go')]]
        elif lang=='Rust':
            (path/'m.rs').write_text(src+f'\nfn main(){{let a={fn}(&vec![vec![0.04,0.01],vec![0.01,0.09]],&[0.6,0.4],2.5,0.05,&vec![vec![1.0,-1.0]],&[0.02],&[0.001]).unwrap();for v in a{{print!("{{:.17}} ",v);}}}}')
            cmds=[['rustc','-D','warnings',str(path/'m.rs'),'-o',str(path/'m')],[str(path/'m')]]
        else:raise ValueError(lang)
        out=''
        for cmd in cmds:
            res=subprocess.run(cmd,cwd=tmp,capture_output=True,text=True,timeout=120)
            if res.returncode:raise RuntimeError(f'{lang} failed: {cmd[0]}: {res.stderr[:2000]}')
            out=res.stdout
        actual=list(map(float,out.split()))
        if len(actual)!=len(expected):raise AssertionError(f'{lang}: wrong output length {len(actual)} vs {len(expected)}: {out[:200]}')
        for i,(x,y) in enumerate(zip(actual,expected)):
            if not math.isclose(x,y,rel_tol=1e-8,abs_tol=1e-9):
                raise AssertionError(f'{lang} index {i}: {x} != {y}')
        return actual

if __name__=='__main__':
    failures=[]
    for language,tool in [('C','gcc'),('C++','g++'),('JavaScript','node'),('TypeScript','tsc'),('Java','javac'),('Swift','swiftc'),('Kotlin','kotlinc'),('Go','go'),('Rust','rustc')]:
        if not shutil.which(tool): print('SKIP',language,flush=True);continue
        try:print('PASS',language,smoke(language),flush=True)
        except Exception as e:print('FAIL',language,str(e),flush=True);failures.append((language,str(e)))
    if failures:sys.exit(1)
