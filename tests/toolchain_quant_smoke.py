"""Optional compiler/runtime checks for 13-language portable structured formulas.
Run: python tests/toolchain_quant_smoke.py. Missing runtimes are SKIP, not PASS.
"""
from __future__ import annotations
import math, shutil, subprocess, tempfile, sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from hyuncalculator.codegen import generate, GenerationOptions
from hyuncalculator.quant import (garch_forecast,gbm_moments,ou_moments,transaction_cost)

CASES = [
    ('TS-002','garch',[.0004,-.01,.00001,.08,.9],list(garch_forecast(.0004,-.01,.00001,.08,.9).values())),
    ('STOCH-001','gbm',[100.,.07,.2,1.],list(gbm_moments(100.,.07,.2,1.).values())),
    ('STOCH-002','ou',[2.,1.,.8,.2,1.],list(ou_moments(2.,1.,.8,.2,1.).values())),
    ('STRAT-001','cost',[100000.,5.,3.,2.,2],list(transaction_cost(100000.,5.,3.,2.,2).values()))
]


def check(lang,formula,name,values,expected):
    snippet=generate(formula,GenerationOptions(language=lang))
    args=', '.join(str(int(v)) if (formula=='STRAT-001' and i==len(values)-1) else
                     (f'{v:.1f}' if lang=='Kotlin' and v==int(v) else f'{v:g}') for i,v in enumerate(values))
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        if lang=='C':
            text=snippet+'\n#include <stdio.h>\nint main(void) { HyunResult r='+name+'('+args+'); for(int i=0;i<'+str(len(expected))+';i++) printf("%.14g ",r.values[i]); }\n'
            (root/'code.c').write_text(text);cmds=[['gcc','-std=c11','-Wall','-Werror','-pedantic',str(root/'code.c'),'-lm','-o',str(root/'code')],[str(root/'code')]]
        elif lang=='C++':
            text=snippet+'\n#include <iostream>\nint main() { for (double x:'+name+'('+args+')) std::cout << x << " "; }\n'
            (root/'code.cpp').write_text(text);cmds=[['g++','-std=c++17','-Wall','-Werror',str(root/'code.cpp'),'-o',str(root/'code')],[str(root/'code')]]
        elif lang in ('JavaScript','TypeScript'):
            text=snippet+'\nconsole.log(Object.values('+name+'('+args+')).join(" "));\n'
            ext='ts' if lang=='TypeScript' else 'mjs'
            (root/('code.'+ext)).write_text(text)
            cmds=[['tsc','--target','ES2020','--module','commonjs','--outDir',td,str(root/'code.ts')],['node',str(root/'code.js')]] if lang=='TypeScript' else [['node',str(root/'code.mjs')]]
        elif lang=='Java':
            text=snippet+'\nclass Driver {public static void main(String[] args){for(double x:GeneratedCalculator.'+name+'('+args+')) System.out.print(x+" ");}}'
            (root/'GeneratedCalculator.java').write_text(text);cmds=[['javac',str(root/'GeneratedCalculator.java')],['java','-cp',td,'Driver']]
        elif lang=='Swift':
            text=snippet+'\nfor x in '+name+'('+args+') { print(x,terminator:" ") }\n'
            (root/'code.swift').write_text(text);cmds=[['swiftc',str(root/'code.swift'),'-o',str(root/'code')],[str(root/'code')]]
        elif lang=='Kotlin':
            text=snippet+'\nfun main(){ for (x in '+name+'('+args+')) print("$x ") }\n'
            (root/'code.kt').write_text(text);cmds=[['kotlinc',str(root/'code.kt'),'-include-runtime','-d',str(root/'code.jar')],['java','-jar',str(root/'code.jar')]]
        elif lang=='Go':
            text=snippet.replace('import "math"','import "math"\nimport "fmt"')+'\nfunc main(){ for _,x := range '+name+'('+args+') {fmt.Printf("%.14g ",x)} }\n'
            (root/'code.go').write_text(text);cmds=[['go','run',str(root/'code.go')]]
        elif lang=='Rust':
            text=snippet+'\nfn main(){for x in '+name+'('+args+') {print!("{} ",x)}}\n'
            (root/'code.rs').write_text(text);cmds=[['rustc',str(root/'code.rs'),'-o',str(root/'code')],[str(root/'code')]]
        else:raise AssertionError(lang)
        for cmd in cmds:
            proc=subprocess.run(cmd,cwd=td,capture_output=True,text=True,timeout=70)
            if proc.returncode: raise RuntimeError(f'{cmd[0]} returned {proc.returncode}: {proc.stderr[:600]}')
        result=[float(x) for x in proc.stdout.split()]
        if len(result)!=len(expected) or not all(math.isclose(x,y,rel_tol=3e-5,abs_tol=5e-6) for x,y in zip(result,expected)):
            raise AssertionError(f'{lang} {formula}: expected {expected}, got {result}')
        return result

if __name__=='__main__':
    fail=[];success=0; skipped=[]
    for lang,tool in [('C','gcc'),('C++','g++'),('JavaScript','node'),('TypeScript','tsc'),('Java','javac'),('Swift','swiftc'),('Kotlin','kotlinc'),('Go','go'),('Rust','rustc')]:
        if not shutil.which(tool): skipped.append(lang); print('SKIP',lang,flush=True);continue
        for fid,name,values,expected in CASES:
            try:
                check(lang,fid,name,values,expected)
                success+=1
                print('PASS',lang,fid,flush=True)
            except Exception as exc:
                fail.append((lang,fid,str(exc)))
                print('FAIL',lang,fid,str(exc),flush=True)
    print('PASSED',success,'FAILED',len(fail),'SKIPPED LANGUAGES',skipped,flush=True)
    if fail:sys.exit(1)
