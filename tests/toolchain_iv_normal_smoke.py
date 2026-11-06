"""Optional real-runtime checks for IV and Gaussian VaR/ES exporters.

Executes selected available toolchains, skipping missing interpreters explicitly.
Does not certify runtimes outside the installed local environment.
"""
from __future__ import annotations
import math,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hyuncalculator.codegen import generate,GenerationOptions
from hyuncalculator.quant import black_scholes,normal_var_es

CASES=[('DERIV-002',(10.450583572185565,100.,100.,1.,.05,0.,'call'),.2),
       ('DERIV-002',(15.912352,100.,110.,.5,.03,.01,'put'),None),
       ('RISK-002',(.001,.02,.95),None),
       ('RISK-002',(-.002,.15,.01),None),
       ('RISK-002',(.001,.02,.999),None)]
TOOLS=[('C','gcc'),('C++','g++'),('JavaScript','node'),('TypeScript','tsc'),('Java','javac'),('Swift','swiftc'),('Kotlin','kotlinc'),('Go','go'),('Rust','rustc')]


def run_one(lang, ident, params):
    src=generate(ident,GenerationOptions(language=lang))
    fname='iv' if ident=='DERIV-002' else 'normal_var'
    # The reference constant for the second IV case is calculated here to avoid a magic price.
    if ident=='DERIV-002':
        p,s,k,t,r,q,typ=params
        arguments=f'{p},{s},{k},{t},{r},{q},"{typ}"'
    else:
        mean,vol,c=params
        arguments=f'{mean},{vol},{c}'
    expr=f'{fname}({arguments})'
    if lang=='Java':expr=f'GeneratedCalculator.{expr}'
    with tempfile.TemporaryDirectory() as d:
        root=Path(d)
        if lang=='C':
            exe=root/'test';out='printf("%.17g",'+expr+');' if ident=='DERIV-002' else f'HyunResult x={expr};printf("%.17g %.17g",x.values[0],x.values[1]);'
            (root/'test.c').write_text(src+'\n#include <stdio.h>\nint main(void){'+out+'}\n')
            commands=[['gcc','-std=c11','-Wall','-Wextra','-Werror',str(root/'test.c'),'-lm','-o',str(exe)],[str(exe)]]
        elif lang=='C++':
            exe=root/'test';out=f'std::cout<<std::setprecision(17)<<{expr};' if ident=='DERIV-002' else f'auto x={expr};std::cout<<std::setprecision(17)<<x[0]<<" "<<x[1];'
            (root/'test.cpp').write_text(src+'\n#include <iostream>\n#include <iomanip>\nint main(){'+out+'}\n')
            commands=[['g++','-std=c++17','-Wall','-Wextra','-Werror',str(root/'test.cpp'),'-o',str(exe)],[str(exe)]]
        elif lang in ('JavaScript','TypeScript'):
            ext='ts' if lang=='TypeScript' else 'mjs';out=f'console.log({expr});' if ident=='DERIV-002' else f'console.log({expr}.join(" "));'
            (root/f'test.{ext}').write_text(src+'\n'+out+'\n')
            commands=([['tsc','--target','ES2020','--module','commonjs','--outDir',str(root),str(root/'test.ts')],['node',str(root/'test.js')]] if lang=='TypeScript' else [['node',str(root/'test.mjs')]])
        elif lang=='Java':
            out=f'System.out.println({expr});' if ident=='DERIV-002' else f'for(double x:{expr})System.out.print(x+" ");'
            (root/'GeneratedCalculator.java').write_text(src+'\nclass Driver {public static void main(String[] args) {'+out+'}}\n')
            commands=[['javac',str(root/'GeneratedCalculator.java')],['java','-cp',str(root),'Driver']]
        elif lang=='Swift':
            out=f'print({expr})' if ident=='DERIV-002' else f'print({expr}.map{{String($0)}}.joined(separator:" "))'
            (root/'test.swift').write_text(src+'\n'+out+'\n')
            commands=[['swiftc',str(root/'test.swift'),'-o',str(root/'test')],[str(root/'test')]]
        elif lang=='Kotlin':
            out=f'println({expr})' if ident=='DERIV-002' else f'println({expr}.joinToString(" "))'
            (root/'test.kt').write_text(src+'\nfun main(){'+out+'}\n')
            commands=[['kotlinc',str(root/'test.kt'),'-include-runtime','-d',str(root/'test.jar')],['java','-jar',str(root/'test.jar')]]
        elif lang=='Go':
            out=f'fmt.Println({expr})' if ident=='DERIV-002' else f'x:={expr};fmt.Println(x[0],x[1])'
            (root/'test.go').write_text(src.replace('import "math"','import "math"\nimport "fmt"')+'\nfunc main(){'+out+'}\n')
            commands=[['go','run',str(root/'test.go')]]
        elif lang=='Rust':
            out=f'println!("{{}}",{expr});' if ident=='DERIV-002' else f'let x={expr};println!("{{}} {{}}",x[0],x[1]);'
            (root/'test.rs').write_text(src+'\nfn main(){'+out+'}\n')
            commands=[['rustc','--edition','2021',str(root/'test.rs'),'-o',str(root/'test')],[str(root/'test')]]
        else:raise AssertionError(lang)
        output=''
        for cmd in commands:
            proc=subprocess.run(cmd,cwd=d,capture_output=True,text=True,timeout=90)
            if proc.returncode:
                raise RuntimeError(f'{lang} {cmd[0]} failed: {proc.stderr[:1800]}')
            output=proc.stdout
    actual=[float(x) for x in output.split()]
    if ident=='DERIV-002':
        if len(actual)!=1 or not math.isfinite(actual[0]):raise AssertionError(f'{lang} IV output invalid: {actual}')
        price,spot,strike,t,rate,div,typ=params
        target=__import__('hyuncalculator.quant',fromlist=['implied_volatility']).implied_volatility(price,spot,strike,t,rate,div,typ)
        if not math.isclose(actual[0],target,rel_tol=1e-7,abs_tol=1e-8):raise AssertionError(f'{lang} IV {actual} vs {target}')
    else:
        ref=normal_var_es(*params);target=list(ref.values())
        if len(actual)!=2 or not all(math.isclose(a,b,rel_tol=1e-7,abs_tol=1e-9) for a,b in zip(actual,target)):
            raise AssertionError(f'{lang} normal VaR {actual} vs {target}')
    return actual

if __name__=='__main__':
    errors=[]
    for lang,cmd in TOOLS:
        if not shutil.which(cmd):
            print('SKIP',lang,'missing toolchain',flush=True);continue
        for ident,params,_ in CASES:
            try: print('PASS',lang,ident,run_one(lang,ident,params),flush=True)
            except Exception as e: errors.append((lang,ident,str(e)));print('FAIL',lang,ident,str(e),flush=True)
    if errors:sys.exit(1)
