"""Optional real toolchain smoke checks. Run: python tests/toolchain_smoke.py.

This is not part of mandatory CI because some compilers are not installed.
"""
import os,sys,tempfile,subprocess,shutil,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from hyuncalculator.codegen import generate,GenerationOptions
from hyuncalculator.codegen.emitter import EXTENSIONS

CASES=[('FIN-001','fv','1000, 0.05, 10',1628.894626777442),
       ('FIN-003','pmt','120000, 0.005, 24',5318.4733),
       ('FIN-004','npv','0.1, [-100,60,60]',4.132231404958667)]

def check(lang,id,fn,expected):
    arg={'FIN-001':{'C':'1000,.05,10','C++':'1000,.05,10','JavaScript':'1000,.05,10','TypeScript':'1000,.05,10','Java':'1000,.05,10','Swift':'1000,0.05,10','Kotlin':'1000.0,.05,10','Go':'1000,.05,10','Rust':'1000.0,.05,10'},
         'FIN-003':{'C':'120000,.005,24','C++':'120000,.005,24','JavaScript':'120000,.005,24','TypeScript':'120000,.005,24','Java':'120000,.005,24','Swift':'120000,0.005,24','Kotlin':'120000.0,.005,24','Go':'120000,.005,24','Rust':'120000.0,.005,24'},
         'FIN-004':{'C':'.1, (double[]){-100,60,60}, 3','C++':'.1,std::vector<double>{-100,60,60}','JavaScript':'.1,[-100,60,60]','TypeScript':'.1,[-100,60,60]','Java':'.1,new double[]{-100,60,60}','Swift':'0.1,[-100,60,60]','Kotlin':'.1,doubleArrayOf(-100.0,60.0,60.0)','Go':'.1,[]float64{-100,60,60}','Rust':'0.1,&[-100.0,60.0,60.0]'}}[id][lang]
    code=generate(id,GenerationOptions(language=lang))
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)
        cmds=[]
        if lang=='C':
            code+='#include <stdio.h>\nint main(void) { printf("%.12f\\n",'+fn+'('+arg+')); return 0; }\n'
            (p/'calc.c').write_text(code);cmds=[['gcc','-std=c11','-Wall','-Werror','-pedantic',str(p/'calc.c'),'-lm','-o',str(p/'calc')],[str(p/'calc')]]
        if lang=='C++':
            code+='#include <iostream>\nint main() { std::cout.precision(15); std::cout << '+fn+'('+arg+') << "\\n"; }\n'
            (p/'calc.cpp').write_text(code);cmds=[['g++','-std=c++17','-Wall','-Werror',str(p/'calc.cpp'),'-o',str(p/'calc')],[str(p/'calc')]]
        if lang=='JavaScript':
            code+='\nconsole.log('+fn+'('+arg+'));\n'
            (p/'calc.mjs').write_text(code);cmds=[['node',str(p/'calc.mjs')]]
        if lang=='TypeScript':
            code+='\nconsole.log('+fn+'('+arg+'));\n'
            (p/'calc.ts').write_text(code);cmds=[['tsc','--target','ES2020','--module','commonjs','--outDir',td,str(p/'calc.ts')],['node',str(p/'calc.js')]]
        if lang=='Java':
            code+='\nclass TestRunner { public static void main(String[] args) { System.out.println(GeneratedCalculator.'+fn+'('+arg+')); } }\n'
            (p/'GeneratedCalculator.java').write_text(code);cmds=[['javac',str(p/'GeneratedCalculator.java')],['java','-cp',td,'TestRunner']]
        if lang=='Swift':
            code+='\nprint('+fn+'('+arg+'))\n'
            (p/'calc.swift').write_text(code);cmds=[['swiftc',str(p/'calc.swift'),'-o',str(p/'calc')],[str(p/'calc')]]
        if lang=='Kotlin':
            code+='\nfun main() { println('+fn+'('+arg+')) }\n'
            (p/'calc.kt').write_text(code);cmds=[['kotlinc',str(p/'calc.kt'),'-include-runtime','-d',str(p/'calc.jar')],['java','-jar',str(p/'calc.jar')]]
        if lang=='Go':
            code=code.replace('import "math"','import "math"\nimport "fmt"')+'\nfunc main() { fmt.Println('+fn+'('+arg+')) }\n'
            (p/'calc.go').write_text(code);cmds=[['go','run',str(p/'calc.go')]]
        if lang=='Rust':
            code+='\nfn main() { println!("{}", '+fn+'('+arg+')); }\n'
            (p/'calc.rs').write_text(code);cmds=[['rustc',str(p/'calc.rs'),'-o',str(p/'calc')],[str(p/'calc')]]
        if not cmds:raise RuntimeError(lang)
        for cmd in cmds:
            q=subprocess.run(cmd,cwd=td,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=65)
            if q.returncode:raise RuntimeError(f'{lang} {id} {cmd[0]} failed: {q.stderr[:800]}')
        v=float(q.stdout.strip())
        if not math.isclose(v,expected,rel_tol=3e-6,abs_tol=1e-5):raise AssertionError(f'{lang} {id} expected {expected}, found {v}')
        return v

if __name__=='__main__':
    total=0
    failures=[]
    for lang,exe in [('C','gcc'),('C++','g++'),('JavaScript','node'),('TypeScript','tsc'),('Java','javac'),('Swift','swiftc'),('Kotlin','kotlinc'),('Go','go'),('Rust','rustc')]:
        if not shutil.which(exe):print('SKIP',lang);continue
        for id,fn,_,expected in CASES:
            try:
                v=check(lang,id,fn,expected);total+=1;print('PASS',lang,id,v,flush=True)
            except Exception as exc:
                failures.append((lang,id,str(exc)))
                print('FAIL',lang,id,exc,flush=True)
    print('checks passed:',total, 'failed:',len(failures))
    if failures:sys.exit(1)
