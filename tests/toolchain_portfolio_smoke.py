"""Optional numerical smoke checks for PORT-001 in locally installed toolchains."""
from __future__ import annotations
import math,subprocess,shutil,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hyuncalculator.codegen import generate,GenerationOptions
from hyuncalculator.quant import portfolio_stats

expected=list(portfolio_stats([.6,.4],[.08,.12],[[.04,.01],[.01,.09]],.02).values())


def check(lang):
    src=generate('PORT-001',GenerationOptions(language=lang))
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)
        if lang=='C':
            c='HyunResult r=portfolio((double[]){.6,.4},(double[]){.08,.12},(double[]){.04,.01,.01,.09},2,.02);for(int i=0;i<3;i++)printf("%.17g ",r.values[i]);'
            (p/'p.c').write_text(src+'\n#include <stdio.h>\nint main(void){'+c+'}\n'); cmds=[['gcc','-std=c11','-Wall','-Werror',str(p/'p.c'),'-lm','-o',str(p/'p')],[str(p/'p')]]
        elif lang=='C++':
            c='auto v=portfolio({.6,.4},{.08,.12},{{.04,.01},{.01,.09}},.02);for(auto x:v)std::cout<<x<<" ";'
            (p/'p.cpp').write_text(src+'\n#include <iostream>\n#include <iomanip>\nint main(){std::cout<<std::setprecision(17);'+c+'}\n');cmds=[['g++','-std=c++17','-Wall','-Werror',str(p/'p.cpp'),'-o',str(p/'p')],[str(p/'p')]]
        elif lang in ('JavaScript','TypeScript'):
            c='console.log(portfolio([.6,.4],[.08,.12],[[.04,.01],[.01,.09]],.02).join(" "));'
            f='p.ts' if lang=='TypeScript' else 'p.mjs';(p/f).write_text(src+'\n'+c+'\n')
            cmds=[['tsc','--target','ES2020','--module','commonjs','--outDir',tmp,str(p/f)],['node',str(p/'p.js')]] if lang=='TypeScript' else [['node',str(p/f)]]
        elif lang=='Java':
            c='for(double x:GeneratedCalculator.portfolio(new double[]{.6,.4},new double[]{.08,.12},new double[][]{{.04,.01},{.01,.09}},.02))System.out.print(x+" ");'
            (p/'GeneratedCalculator.java').write_text(src+'\nclass Driver{public static void main(String[]args){'+c+'}}\n');cmds=[['javac',str(p/'GeneratedCalculator.java')],['java','-cp',tmp,'Driver']]
        elif lang=='Swift':
            c='for x in portfolio([0.6,0.4],[0.08,0.12],[[0.04,0.01],[0.01,0.09]],0.02){print(x,terminator:" ")}'
            (p/'p.swift').write_text(src+'\n'+c+'\n');cmds=[['swiftc',str(p/'p.swift'),'-o',str(p/'p')],[str(p/'p')]]
        elif lang=='Kotlin':
            c='for(x in portfolio(doubleArrayOf(0.6,0.4),doubleArrayOf(0.08,0.12),arrayOf(doubleArrayOf(0.04,0.01),doubleArrayOf(0.01,0.09)),0.02))print("$x ")'
            (p/'p.kt').write_text(src+'\nfun main(){'+c+'}\n');cmds=[['kotlinc',str(p/'p.kt'),'-include-runtime','-d',str(p/'p.jar')],['java','-jar',str(p/'p.jar')]]
        elif lang=='Go':
            c='for _,x:=range portfolio([]float64{.6,.4},[]float64{.08,.12},[][]float64{{.04,.01},{.01,.09}},.02){fmt.Printf("%.17g ",x)}'
            (p/'p.go').write_text(src.replace('import "math"','import "math"\nimport "fmt"')+'\nfunc main(){'+c+'}\n');cmds=[['go','run',str(p/'p.go')]]
        else:raise ValueError(lang)
        output=''
        for cmd in cmds:
            r=subprocess.run(cmd,cwd=tmp,capture_output=True,text=True,timeout=80)
            if r.returncode:raise AssertionError(f'{lang} {cmd[0]}: {r.stderr[:1500]}')
            output=r.stdout
        got=[float(x) for x in output.split()]
        if len(got)!=len(expected) or not all(math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-8) for a,b in zip(got,expected)):
            raise AssertionError(f'{lang}: {got} vs {expected}')
        return got

if __name__=='__main__':
    errors=[]
    for lang,tool in [('C','gcc'),('C++','g++'),('JavaScript','node'),('TypeScript','tsc'),('Java','javac'),('Swift','swiftc'),('Kotlin','kotlinc'),('Go','go')]:
        if not shutil.which(tool):print('SKIP',lang,flush=True);continue
        try:print('PASS',lang,check(lang),flush=True)
        except Exception as e:errors.append((lang,str(e)));print('FAIL',lang,str(e),flush=True)
    if errors:sys.exit(1)
