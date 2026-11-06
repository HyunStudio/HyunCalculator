"""Optional executable verification of the 13-language YTM emitters.
Available C/C++/JS/TS/Java/Swift/Kotlin/Go; others are unverified.
"""
from __future__ import annotations
import math,sys,tempfile,subprocess,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from hyuncalculator.codegen import generate,GenerationOptions
from hyuncalculator.quant import yield_to_maturity

CASES=[(1044.912925031211,1000.,.05,5.,2),(850.,1000.,0.,2.,2)]

def check(lang,values):
    src=generate('BOND-002',GenerationOptions(language=lang))
    price,face,coupon,years,freq=values
    args=f'{price:.15f},{face:.1f},{coupon:.2f},{years:.1f},{freq}'
    with tempfile.TemporaryDirectory() as td:
        r=Path(td)
        if lang=='C':
            s=src+'\n#include <stdio.h>\nint main(void){printf("%.17g",ytm('+args+'));}\n'
            (r/'m.c').write_text(s);steps=[['gcc','-std=c11','-Wall','-Werror',str(r/'m.c'),'-lm','-o',str(r/'m')],[str(r/'m')]]
        elif lang=='C++':
            s=src+'\n#include <iostream>\nint main(){std::cout.precision(17);std::cout<<ytm('+args+');}\n'
            (r/'m.cpp').write_text(s);steps=[['g++','-std=c++17','-Wall','-Werror',str(r/'m.cpp'),'-o',str(r/'m')],[str(r/'m')]]
        elif lang in ('JavaScript','TypeScript'):
            s=src+'\nconsole.log(ytm('+args+'));\n';ext='ts' if lang=='TypeScript' else 'mjs'
            (r/('m.'+ext)).write_text(s);steps=[['tsc','--target','ES2020','--module','commonjs','--outDir',td,str(r/'m.ts')],['node',str(r/'m.js')]] if lang=='TypeScript' else [['node',str(r/'m.mjs')]]
        elif lang=='Java':
            s=src+'\nclass Driver{public static void main(String[]a){System.out.println(GeneratedCalculator.ytm('+args+'));}}'
            (r/'GeneratedCalculator.java').write_text(s);steps=[['javac',str(r/'GeneratedCalculator.java')],['java','-cp',td,'Driver']]
        elif lang=='Swift':
            s=src+'\nprint(ytm('+args+'))\n';(r/'m.swift').write_text(s);steps=[['swiftc',str(r/'m.swift'),'-o',str(r/'m')],[str(r/'m')]]
        elif lang=='Kotlin':
            s=src+'\nfun main(){println(ytm('+args+'))}\n';(r/'m.kt').write_text(s);steps=[['kotlinc',str(r/'m.kt'),'-include-runtime','-d',str(r/'m.jar')],['java','-jar',str(r/'m.jar')]]
        elif lang=='Go':
            s=src.replace('import "math"','import "math"\nimport "fmt"')+'\nfunc main(){fmt.Printf("%.17g",ytm('+args+'))}\n'
            (r/'m.go').write_text(s);steps=[['go','run',str(r/'m.go')]]
        else:raise AssertionError(lang)
        for cmd in steps:
            p=subprocess.run(cmd,cwd=td,capture_output=True,text=True,timeout=70)
            if p.returncode:raise RuntimeError(cmd[0]+': '+p.stderr[:750])
        out=float(p.stdout)
        expected=yield_to_maturity(*values)
        if not math.isclose(out,expected,abs_tol=1e-8,rel_tol=1e-8):raise AssertionError((lang,values,expected,out))
        return out
if __name__=='__main__':
    fails=[];ok=0
    for lang,tool in [('C','gcc'),('C++','g++'),('JavaScript','node'),('TypeScript','tsc'),('Java','javac'),('Swift','swiftc'),('Kotlin','kotlinc'),('Go','go')]:
        if not shutil.which(tool):print('SKIP',lang,flush=True);continue
        for values in CASES:
            try:
                result=check(lang,values);ok+=1;print('PASS',lang,values[2],result,flush=True)
            except Exception as exc:fails.append((lang,repr(exc)));print('FAIL',lang,str(exc),flush=True)
    print('SUMMARY',ok,'passed',len(fails),'failed',flush=True)
    if fails:sys.exit(1)
