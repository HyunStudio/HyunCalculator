"""Optional real toolchain validation for historical VaR and moving averages.

Missing toolchains are reported as skips, never PASS. CI unittest does not
require these compilers. Run manually: python tests/toolchain_series_smoke.py
"""
from __future__ import annotations
import math,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from hyuncalculator.codegen import generate,GenerationOptions
from hyuncalculator.quant import historical_var_es,moving_averages

RET=[-.02,.01,.005,-.04,.02,-.01,.03]
MOV=[100.,102.,101.,104.,106.,105.]


def test(lang, fid):
    src=generate(fid,GenerationOptions(language=lang))
    is_risk=fid=='RISK-001'
    name='hist_var' if is_risk else 'moving'
    rr='{-0.02,0.01,0.005,-0.04,0.02,-0.01,0.03}'
    mm='{100,102,101,104,106,105}'
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)
        if lang=='C':
            if is_risk: call='HyunResult x=hist_var((double[])'+rr+',7,0.95);printf("%.17g %.17g",x.values[0],x.values[1]);'
            else:call='double sma[4],ema[6];HyunMovingResult x=moving((double[])'+mm+',6,3,sma,ema);printf("%.17g %.17g ",x.last_sma,x.last_ema);for(int i=0;i<4;i++)printf("%.17g ",sma[i]);for(int i=0;i<6;i++)printf("%.17g ",ema[i]);'
            (p/'a.c').write_text(src+'\n#include <stdio.h>\nint main(void){'+call+'}\n')
            cmds=[['gcc','-std=c11','-Wall','-Werror',str(p/'a.c'),'-lm','-o',str(p/'a')],[str(p/'a')]]
        elif lang=='C++':
            if is_risk: call='auto r=hist_var(std::vector<double>'+rr+',0.95);for(auto x:r)std::cout<<x<<" ";'
            else:call='auto r=moving(std::vector<double>'+mm+',3);std::cout<<r.last_sma<<" "<<r.last_ema<<" ";for(auto x:r.sma)std::cout<<x<<" ";for(auto x:r.ema)std::cout<<x<<" ";'
            (p/'a.cpp').write_text(src+'\n#include <iostream>\n#include <iomanip>\nint main(){std::cout<<std::setprecision(17);'+call+'}\n')
            cmds=[['g++','-std=c++17','-Wall','-Werror',str(p/'a.cpp'),'-o',str(p/'a')],[str(p/'a')]]
        elif lang in ('JavaScript','TypeScript'):
            arr='[-0.02,0.01,0.005,-0.04,0.02,-0.01,0.03]' if is_risk else '[100,102,101,104,106,105]'
            call='console.log(hist_var('+arr+',0.95).join(" "));' if is_risk else 'const r=moving('+arr+',3);console.log([r.lastSMA,r.lastEMA,...r.sma,...r.ema].join(" "));'
            ext='ts' if lang=='TypeScript' else 'mjs';(p/('a.'+ext)).write_text(src+'\n'+call+'\n')
            cmds=([['tsc','--target','ES2020','--module','commonjs','--outDir',tmp,str(p/'a.ts')],['node',str(p/'a.js')]] if lang=='TypeScript' else [['node',str(p/'a.mjs')]])
        elif lang=='Java':
            arr='new double[]'+rr if is_risk else 'new double[]'+mm
            call='double[] r=GeneratedCalculator.hist_var('+arr+',0.95);for(double x:r)System.out.print(x+" ");' if is_risk else 'GeneratedCalculator.MovingResult r=GeneratedCalculator.moving('+arr+',3);System.out.print(r.lastSMA+" "+r.lastEMA+" ");for(double x:r.sma)System.out.print(x+" ");for(double x:r.ema)System.out.print(x+" ");'
            (p/'GeneratedCalculator.java').write_text(src+'\nclass Driver{public static void main(String[] args){'+call+'}}\n')
            cmds=[['javac',str(p/'GeneratedCalculator.java')],['java','-cp',tmp,'Driver']]
        elif lang=='Swift':
            arr='[-0.02,0.01,0.005,-0.04,0.02,-0.01,0.03]' if is_risk else '[100,102,101,104,106,105]'
            call='for x in hist_var('+arr+',0.95){print(x,terminator:" ")}' if is_risk else 'let r=moving('+arr+',3);for x in [r.lastSMA,r.lastEMA]+r.sma+r.ema{print(x,terminator:" ")}'
            (p/'a.swift').write_text(src+'\n'+call+'\n');cmds=[['swiftc',str(p/'a.swift'),'-o',str(p/'a')],[str(p/'a')]]
        elif lang=='Kotlin':
            arr='doubleArrayOf(-0.02,0.01,0.005,-0.04,0.02,-0.01,0.03)' if is_risk else 'doubleArrayOf(100.0,102.0,101.0,104.0,106.0,105.0)'
            call='for(x in hist_var('+arr+',0.95))print("$x ")' if is_risk else 'val r=moving('+arr+',3);for(x in doubleArrayOf(r.lastSMA,r.lastEMA)+r.sma+r.ema)print("$x ")'
            (p/'a.kt').write_text(src+'\nfun main(){'+call+'}\n');cmds=[['kotlinc',str(p/'a.kt'),'-include-runtime','-d',str(p/'a.jar')],['java','-jar',str(p/'a.jar')]]
        elif lang=='Go':
            arr='[]float64'+rr if is_risk else '[]float64'+mm
            call='for _,x:=range hist_var('+arr+',0.95){fmt.Printf("%.17g ",x)}' if is_risk else 'r:=moving('+arr+',3);fmt.Printf("%.17g %.17g ",r.LastSMA,r.LastEMA);for _,x:=range r.SMA{fmt.Printf("%.17g ",x)};for _,x:=range r.EMA{fmt.Printf("%.17g ",x)}'
            src=src.replace('import "math"','import "math"\nimport "fmt"').replace('import ("math";"sort")','import ("math";"sort";"fmt")')
            (p/'a.go').write_text(src+'\nfunc main(){'+call+'}\n');cmds=[['go','run',str(p/'a.go')]]
        else:raise AssertionError(lang)
        output=''
        for cmd in cmds:
            result=subprocess.run(cmd,cwd=tmp,capture_output=True,text=True,timeout=75)
            if result.returncode:raise AssertionError(f'{lang} {fid}: {result.stderr[:800]}')
            output=result.stdout
        got=[float(t) for t in output.split()]
        if is_risk:exp=list(historical_var_es(RET).values())
        else:
            v=moving_averages(MOV,3)
            exp=[v['Last SMA'],v['Last EMA'],*v['SMA (from first complete window)'],*v['EMA (first value seeded)']]
        if len(got)!=len(exp) or not all(math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-8) for a,b in zip(got,exp)):
            raise AssertionError(f'{lang} {fid} result mismatch: {got} vs {exp}')
        return got

if __name__=='__main__':
    errors=[]
    for lang,tool in [('C','gcc'),('C++','g++'),('JavaScript','node'),('TypeScript','tsc'),('Java','javac'),('Swift','swiftc'),('Kotlin','kotlinc'),('Go','go')]:
        if not shutil.which(tool):print('SKIP',lang,flush=True);continue
        for fid in ('RISK-001','TS-003'):
            try: print('PASS',lang,fid,test(lang,fid)[:3],flush=True)
            except Exception as e:errors.append((lang,fid,str(e)));print('FAIL',lang,fid,str(e),flush=True)
    if errors:sys.exit(1)
