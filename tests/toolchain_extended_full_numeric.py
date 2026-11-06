"""Required full representative runtime checks for five additional targets."""
from __future__ import annotations
import argparse
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from toolchain_ci_smoke import selected_cases
from toolchain_js_full_numeric import CASES
from hyuncalculator.codegen import generate, GenerationOptions
from hyuncalculator.codegen.registry import catalog

TOOLS={'TypeScript':('tsc','node'),'Java':('javac','java'),'Swift':('swiftc',),'Kotlin':('kotlinc','java'),'Go':('go',)}
ARGS={
 'STAT-001':[100.,100.,20.,.95],
 'STAT-002':[[[.05,.10,.08],[.10,.02,.07],[-.05,.03,.01],[.02,-.04,.06]]],
 'BOND-001':[1000.,.05,.04,5.,2],
 'RISK-003':[[.05,-.02,.01,-.03,.04,.015],.001,252],
 'TS-001':[[.02,-.01,.03,.015,-.04],.94],
 'STRAT-002':[[.02,-.01,.03,.01,-.02,.04],[1.,1.,-1.,0.,.5,0.],3.,2.,.0001,252],
}

def literal(value,language):
    if not isinstance(value,list): return repr(value)
    nested=bool(value and isinstance(value[0],list))
    parts=','.join(literal(v,language) for v in value)
    if language=='Java': return ('new double[][]{' if nested else 'new double[]{')+parts+'}'
    if language=='Kotlin': return ('arrayOf(' if nested else 'doubleArrayOf(')+parts+')'
    if language=='Go': return ('[][]float64{' if nested else '[]float64{')+parts+'}'
    return '['+parts+']'

def check_remaining(language,case):
    fid,fn,_,expected,tol=case
    code=generate(fid,GenerationOptions(language=language))
    call=fn+'('+','.join(literal(v,language) for v in ARGS[fid])+')'
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp); exe=root/'program'
        if language=='TypeScript':
            src=root/'driver.ts';code+='\nconsole.log('+call+'.join(" "));\n'
            commands=[['tsc','--target','ES2020','--module','commonjs','--outDir',tmp,str(src)],['node',str(root/'driver.js')]]
        elif language=='Java':
            src=root/'GeneratedCalculator.java';code+='\nclass Driver{public static void main(String[] args){for(double x:GeneratedCalculator.'+call+')System.out.print(x+" ");}}\n'
            commands=[['javac',str(src)],['java','-cp',tmp,'Driver']]
        elif language=='Swift':
            src=root/'driver.swift';code+='\nfor x in '+call+' {print(x,terminator:" ")}\n'
            commands=[['swiftc',str(src),'-o',str(exe)],[str(exe)]]
        elif language=='Kotlin':
            src=root/'driver.kt';code+='\nfun main(){for(x in '+call+')print("$x ")}\n'
            commands=[['kotlinc',str(src),'-include-runtime','-d',str(root/'driver.jar')],['java','-jar',str(root/'driver.jar')]]
        else:
            src=root/'driver.go';code=code.replace('import "math"','import "math"\nimport "fmt"')+'\nfunc main(){for _,x:=range '+call+' {fmt.Printf("%.17g ",x)}}\n'
            commands=[['go','run',str(src)]]
        src.write_text(code,encoding='utf-8')
        for command in commands:
            result=subprocess.run(command,cwd=tmp,capture_output=True,text=True,timeout=120)
            if result.returncode: raise AssertionError(result.stderr[-3000:])
        actual=[float(x) for x in result.stdout.split()]
    if len(actual)!=len(expected): raise AssertionError(f'{len(actual)} fields != {len(expected)}')
    for i,(a,b) in enumerate(zip(actual,expected)):
        if not math.isfinite(a) or not math.isfinite(b) or not math.isclose(a,b,rel_tol=tol,abs_tol=tol):
            raise AssertionError(f'field {i}: {a} != {b}')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('language',choices=TOOLS);language=parser.parse_args().language
    for tool in TOOLS[language]:
        if not shutil.which(tool): raise RuntimeError('Required tool missing: '+tool)
    common=selected_cases();ids=[i for i,_ in common]+[c[0] for c in CASES]
    if len(ids)!=33 or len(set(ids))!=33 or set(ids)!={f.id for f in catalog()}: raise AssertionError('Stale catalog')
    failed=[];passed=0
    for fid,task in list(common)+[(c[0],lambda lang,c=c:check_remaining(lang,c)) for c in CASES]:
        try:
            value=task(language)
            if fid in ('FIN-005','FIN-006') and not value[0]: raise AssertionError(value[1])
            passed+=1;print('PASS',language,fid,flush=True)
        except Exception as exc:
            failed.append(fid);print('FAIL',language,fid,str(exc),flush=True)
    print(f'{language}: {passed}/33 PASS; {len(failed)} FAIL',flush=True)
    if failed: raise SystemExit(1)
if __name__=='__main__': main()
