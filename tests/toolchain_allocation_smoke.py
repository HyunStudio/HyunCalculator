"""Manual compiler smoke: verify both Markowitz adapters in available toolchains.

Runs 2/3 asset numerical samples and invalid covariances. This script is optional
because not every CI runner has Swift/Kotlin/Go/R/MATLAB licenses installed.
"""
from __future__ import annotations
import math,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hyuncalculator.codegen import generate,GenerationOptions
from hyuncalculator.quant import global_minimum_variance,minimum_variance_target

cov=[[.04,.01],[.01,.09]]
mu=[.08,.12]
expected_gmv=list(global_minimum_variance(cov))
expected_gmv.append(sum(expected_gmv[i]*cov[i][j]*expected_gmv[j] for i in range(2) for j in range(2)))
expected_target=list(minimum_variance_target(mu,cov,.1))
expected_target.append(sum(expected_target[i]*mu[i] for i in range(2)))

def smoke(fid,lang):
    src=generate(fid,GenerationOptions(language=lang))
    target=fid=='ALLOC-002'
    fn='target_portfolio' if target else 'gmv'
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)
        if lang=='C':
            args='(double[]){.08,.12},' if target else ''
            args+='(double[]){.04,.01,.01,.09},2,'
            if target:args+='.1,'
            args+='out'
            (p/'m.c').write_text(src+f'\n#include <stdio.h>\nint main(void){{double out[3];if({fn}({args})!=0)return 4;printf("%.17g %.17g %.17g",out[0],out[1],out[2]);}}')
            cmds=[['gcc','-std=c11','-Wall','-Werror',str(p/'m.c'),'-lm','-o',str(p/'m')],[str(p/'m')]]
        elif lang=='C++':
            args='std::vector<double>{.08,.12},' if target else ''
            args+='std::vector<std::vector<double>>{{.04,.01},{.01,.09}}'
            if target:args+=',.1'
            (p/'m.cpp').write_text(src+f'\n#include <iostream>\n#include <iomanip>\nint main(){{auto v={fn}({args});std::cout<<std::setprecision(17)<<v[0]<<" "<<v[1]<<" "<<v[2];}}')
            cmds=[['g++','-std=c++17','-Wall','-Werror',str(p/'m.cpp'),'-o',str(p/'m')],[str(p/'m')]]
        elif lang in ('JavaScript','TypeScript'):
            args='[.08,.12],' if target else ''
            args+='[[.04,.01],[.01,.09]]'
            if target:args+=',.1'
            f='m.ts' if lang=='TypeScript' else 'm.mjs'
            (p/f).write_text(src+f'\nconsole.log({fn}({args}).join(" "));')
            cmds=[['tsc','--target','ES2020','--module','commonjs','--outDir',tmp,str(p/f)],['node',str(p/'m.js')]] if lang=='TypeScript' else [['node',str(p/f)]]
        elif lang=='Java':
            args='new double[]{.08,.12},' if target else ''
            args+='new double[][]{{.04,.01},{.01,.09}}'
            if target:args+=',.1'
            (p/'GeneratedCalculator.java').write_text(src+f'\nclass Runner{{public static void main(String[]a){{for(double x:GeneratedCalculator.{fn}({args}))System.out.print(x+" ");}}}}')
            cmds=[['javac',str(p/'GeneratedCalculator.java')],['java','-cp',tmp,'Runner']]
        elif lang=='Swift':
            args='[0.08,0.12],' if target else ''
            args+='[[0.04,0.01],[0.01,0.09]]'
            if target:args+=',0.1'
            (p/'m.swift').write_text(src+f'\nlet values=try! {fn}({args})\nfor x in values{{print(x,terminator:" ")}}')
            cmds=[['swiftc',str(p/'m.swift'),'-o',str(p/'m')],[str(p/'m')]]
        elif lang=='Kotlin':
            args='doubleArrayOf(0.08,0.12),' if target else ''
            args+='arrayOf(doubleArrayOf(0.04,0.01),doubleArrayOf(0.01,0.09))'
            if target:args+=',0.1'
            (p/'m.kt').write_text(src+f'\nfun main(){{for(x in {fn}({args}))print("$x ")}}')
            cmds=[['kotlinc',str(p/'m.kt'),'-include-runtime','-d',str(p/'m.jar')],['java','-jar',str(p/'m.jar')]]
        elif lang=='Go':
            args='[]float64{.08,.12},' if target else ''
            args+='[][]float64{{.04,.01},{.01,.09}}'
            if target:args+=',.1'
            (p/'m.go').write_text(src.replace('import "math"','import ("math";"fmt")')+f'\nfunc main(){{for _,x:=range {fn}({args}){{fmt.Printf("%.17g ",x)}}}}')
            cmds=[['go','run',str(p/'m.go')]]
        else:raise ValueError(lang)
        result=''
        for cmd in cmds:
            r=subprocess.run(cmd,cwd=tmp,capture_output=True,text=True,timeout=90)
            if r.returncode:raise AssertionError(f'{lang}/{fid} {cmd[0]}: {r.stderr[:1500]}')
            result=r.stdout
        vals=[float(x) for x in result.split()]
        expected=expected_target if target else expected_gmv
        if len(vals)!=3 or not all(math.isclose(x,y,abs_tol=1e-8,rel_tol=1e-8) for x,y in zip(vals,expected)):
            raise AssertionError(f'{lang}/{fid}: {vals} != {expected}')
        return vals

if __name__=='__main__':
    failures=[]
    for fid in ('ALLOC-001','ALLOC-002'):
        for lang,tool in [('C','gcc'),('C++','g++'),('JavaScript','node'),('TypeScript','tsc'),('Java','javac'),('Swift','swiftc'),('Kotlin','kotlinc'),('Go','go')]:
            if not shutil.which(tool):print('SKIP',fid,lang,flush=True);continue
            try:print('PASS',fid,lang,smoke(fid,lang),flush=True)
            except Exception as e:failures.append((fid,lang,str(e)));print('FAIL',fid,lang,str(e),flush=True)
    if failures:sys.exit(1)
