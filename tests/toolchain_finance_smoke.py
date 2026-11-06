"""Optional standalone compiler smoke tests for FIN-005/006.

Run: python tests/toolchain_finance_smoke.py --langs C C++ JavaScript TypeScript Java Swift Kotlin Go
Toolchains must be installed. These test representative inputs, not every
formula-language edge case. This is not part of required CI.
"""
from __future__ import annotations
import math
import pathlib
import shutil
import subprocess
import tempfile

from hyuncalculator.codegen import GenerationOptions, generate

def source(formula, lang):
    fid = 'FIN-006' if formula == 'fin_loan' else 'FIN-005'
    return generate(fid, GenerationOptions(language=lang))


def test(lang,formula):
    c=source(formula,lang)
    name='loan' if formula=='fin_loan' else 'calculate_irr'
    args='120000,0.005,24,12' if formula=='fin_loan' else '[-100,60,60]'
    with tempfile.TemporaryDirectory() as dd:
        p=pathlib.Path(dd)
        if lang=='C':
            test=(f'\n#include <stdio.h>\nint main(void){{HyunLoanResult r={name}(120000,.005,24,12);for(int i=0;i<4;i++)printf("%.12f ",r.values[i]);return 0;}}' if formula=='fin_loan'
                  else f'\n#include <stdio.h>\nint main(void){{double a[]={{-100,60,60}};printf("%.12f",{name}(a,3));return 0;}}')
            (p/'g.c').write_text(c+test);cmd=['gcc','-std=c11','-Wall','-Wextra','-Werror',str(p/'g.c'),'-lm','-o',str(p/'a')];run=[str(p/'a')]
        elif lang=='C++':
            test=(f'\n#include <iostream>\nint main(){{auto r={name}(120000,.005,24,12);for(auto x:r)std::cout<<std::fixed<<x<<" ";}}' if formula=='fin_loan' else f'\n#include <iostream>\n#include <iomanip>\nint main(){{std::cout<<std::setprecision(15)<<{name}(std::vector<double>{{-100,60,60}});}}')
            (p/'g.cpp').write_text(c+test);cmd=['g++','-std=c++17','-Wall','-Wextra','-Werror',str(p/'g.cpp'),'-o',str(p/'a')];run=[str(p/'a')]
        elif lang=='JavaScript':
            (p/'g.mjs').write_text(c+f'\nconsole.log({name}({args if formula=="fin_loan" else "[-100,60,60]"}));');cmd=None;run=['node',str(p/'g.mjs')]
        elif lang=='TypeScript':
            (p/'g.ts').write_text(c+f'\nconsole.log({name}({args}));');cmd=['tsc','--strict','--target','es2020','--module','commonjs',str(p/'g.ts')];run=['node',str(p/'g.js')]
        elif lang=='Java':
            x=f'\nclass Test{{public static void main(String[] args){{ System.out.println(java.util.Arrays.toString(GeneratedCalculator.{name}(120000,.005,24,12)));}}}}' if formula=='fin_loan' else f'\nclass Test{{public static void main(String[] args){{System.out.println(GeneratedCalculator.{name}(new double[]{{-100,60,60}}));}}}}'
            (p/'GeneratedCalculator.java').write_text(c+x);cmd=['javac',str(p/'GeneratedCalculator.java')];run=['java','-cp',str(p),'Test']
        elif lang=='Swift':
            x=f'\nprint({name}(120000,0.005,24,12))' if formula=='fin_loan' else f'\nprint({name}([-100,60,60]))'
            (p/'g.swift').write_text(c+x);cmd=['swiftc',str(p/'g.swift'),'-o',str(p/'a')];run=[str(p/'a')]
        elif lang=='Kotlin':
            x=f'\nfun main(){{println({name}(120000.0,.005,24,12).joinToString(","))}}' if formula=='fin_loan' else f'\nfun main(){{println({name}(doubleArrayOf(-100.0,60.0,60.0)))}}'
            (p/'G.kt').write_text(c+x);cmd=['kotlinc',str(p/'G.kt'),'-include-runtime','-d',str(p/'g.jar')];run=['java','-jar',str(p/'g.jar')]
        elif lang=='Go':
            c=c.replace('import "math"','import ("math";"fmt")');x=f'\nfunc main(){{fmt.Println({name}(120000,.005,24,12))}}' if formula=='fin_loan' else f'\nfunc main(){{fmt.Println({name}([]float64{{-100,60,60}}))}}'
            (p/'g.go').write_text(c+x);cmd=None;run=['go','run',str(p/'g.go')]
        else:return False,'no toolchain'
        if cmd:
            res=subprocess.run(cmd,cwd=p,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30)
            if res.returncode:return False,'COMPILE: '+res.stderr[:2000]
        res=subprocess.run(run,cwd=p,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30)
        if res.returncode:return False,'RUN: '+res.stderr[:1000]
        import re
        values=[float(x) for x in re.findall(r'(?<![a-zA-Z])[+-]?(?:\d*\.\d+|\d+)(?:[eE][+-]?\d+)?',res.stdout)]
        if formula=='fin_loan':
            if len(values)!=4:return False,'unexpected result '+res.stdout
            pr,rate,n,period=120000,.005,24,12
            payment=pr*rate/(1-(1+rate)**-n)
            factor=(1+rate)**(period-1)
            prev=pr*factor-payment*(factor-1)/rate
            reference=[payment,prev*rate,payment-prev*rate,max(0,prev-(payment-prev*rate))]
            if any(not math.isclose(x,y,rel_tol=1e-8,abs_tol=1e-7) for x,y in zip(values,reference)):
                return False,f'NUMERIC actual={values} ref={reference}'
        else:
            ref=(-60-math.sqrt(60**2+4*100*60))/(2*-100) if False else 0.1306623862918075
            if len(values)!=1 or not math.isclose(values[0],ref,abs_tol=1e-7,rel_tol=1e-7):return False,f'NUMERIC {values} vs {ref}'
        return True,res.stdout.strip()

if __name__ == '__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--langs',nargs='*',default=['C','C++','JavaScript','TypeScript','Java','Swift','Kotlin','Go']);ap.add_argument('--formulas',nargs='*',default=['fin_loan','fin_irr']);args=ap.parse_args()
    needed = {'C':'gcc','C++':'g++','JavaScript':'node','TypeScript':'tsc','Java':'javac','Swift':'swiftc','Kotlin':'kotlinc','Go':'go'}
    failed = False
    for form in args.formulas:
        for lang in args.langs:
            if not shutil.which(needed.get(lang, 'not-installed')):
                print(f'{form} {lang}: SKIP (toolchain not installed)', flush=True)
                continue
            try:
                ok,msg=test(lang,form)
            except Exception as exc:ok=False;msg=repr(exc)
            print(f'{form:>8} {lang:>11}: {"PASS" if ok else "FAIL"} {msg}',flush=True)
            failed |= not ok
    if failed:
        raise SystemExit(1)
