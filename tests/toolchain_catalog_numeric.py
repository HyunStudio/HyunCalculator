"""Full catalog numerical execution for R, Julia, Rust, C# and Octave.

Octave is a compatibility runtime, never evidence of licensed MATLAB execution.
All comparisons use registry sample inputs and original Python operations;
portable stochastic streams use independent Park-Miller references instead.
"""
from __future__ import annotations
import argparse
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from toolchain_ci_smoke import selected_cases
from hyuncalculator.codegen import generate, GenerationOptions, catalog
from hyuncalculator.operations import GROUPS
from test_codegen_python_full import _decode
from toolchain_js_full_numeric import flatten_result
from toolchain_stochastic_smoke import reference as path_reference
from test_codegen_mc import reference_portable
from toolchain_r_csharp_smoke import verify_output

SCALARS={'FIN-001','FIN-002','FIN-003','FIN-004','FIN-005','FIN-007','FIN-008','FIN-009','DERIV-002','BOND-002'}

def samples():
    operations={o.compute.__name__:o for group in ('Financial','Quant') for o in GROUPS[group]}
    for formula in catalog():
        args=[_decode(key,example) for key,example in formula.fields]
        args=[a.tolist() if hasattr(a,'tolist') else a for a in args]
        if formula.id=='FIN-001':args=args[:3]
        if formula.id=='ALLOC-003':args[-3]=[args[-3]];args[-2]=[args[-2]];args[-1]=[args[-1]]
        result=operations[formula.function].compute(dict(formula.fields))
        expected=flatten_result(result) if isinstance(result,dict) else [float(result)]
        if formula.id=='DERIV-003':
            args[-2]=4000;expected=list(reference_portable(*args))
        if formula.id.startswith('STOCH-') and formula.id[-1] in '345':
            index=1 if formula.id=='STOCH-003' else 4 if formula.id=='STOCH-004' else 5
            args[index]=4;args[index+1]=50;expected=path_reference(formula.id,args)
        fn={'qf_target':'target_portfolio','fin_irr':'calculate_irr'}.get(formula.function,formula.function.removeprefix('fin_').removeprefix('qf_'))
        yield formula.id,fn,args,expected

def literal(value,language,rectangular=False):
    if isinstance(value,str):return json.dumps(value)
    if not isinstance(value,list):return repr(value)
    matrix=bool(value and isinstance(value[0],list))
    if language in ('R','Julia','MATLAB') and matrix:
        if language=='R':
            flat=','.join(repr(x) for row in value for x in row)
            return f'matrix(c({flat}),nrow={len(value)},byrow=TRUE)'
        return '['+';'.join(' '.join(repr(x) for x in row) for row in value)+']'
    if language=='Rust':
        if matrix:return '&['+','.join('vec!['+','.join(repr(float(x)) for x in row)+']' for row in value)+']'
        return '&['+','.join(repr(float(x)) for x in value)+']'
    if language=='C#':
        if matrix and rectangular:return 'new double[,] {'+','.join('{'+','.join(repr(x) for x in row)+'}' for row in value)+'}'
        return ('new double[][]{' if matrix else 'new double[]{')+','.join(literal(x,language) for x in value)+'}'
    parts=','.join(literal(x,language) for x in value)
    if language=='R':return 'c('+parts+')'
    return '['+parts+']'

def check(language,record):
    fid,fn,args,expected=record
    target='MATLAB' if language in ('Octave','MATLAB') else language
    expr=fn+'('+','.join(literal(a,target,rectangular=fid!='STAT-002') for a in args)+')'
    source=generate(fid,GenerationOptions(language=target))
    with tempfile.TemporaryDirectory(prefix='hyun_catalog_') as tmp:
        p=Path(tmp)
        if language=='R':
            src=p/'driver.R';source+='\nv <- '+expr+'\ncat("HYUN_RESULT ",paste(sprintf("%.17g",as.numeric(unlist(v))),collapse=" "),"\\n",sep="")\n'
            commands=[['Rscript','--vanilla',str(src)]]
        elif language=='Julia':
            src=p/'driver.jl';source+='\nflatten(x::Number) = [Float64(x)]\nflatten(x::NamedTuple) = reduce(vcat, (flatten(v) for v in values(x)))\nflatten(x::AbstractArray) = reduce(vcat, (flatten(v) for v in x))\nprintln("HYUN_RESULT ",join(string.(flatten('+expr+')), " "))\n'
            commands=[['julia','--startup-file=no',str(src)]]
        elif language in ('Octave','MATLAB'):
            (p/(fn+'.m')).write_text(source,encoding='utf-8');src=p/'driver.m'
            source='v='+expr+';\nif isstruct(v), c=struct2cell(v); v=[c{:}]; end\nfprintf("HYUN_RESULT ");fprintf("%.17g ",v(:));fprintf("\\n");\n'
            commands=([['matlab','-batch',"run('driver.m')"]] if language=='MATLAB' else [[shutil.which('octave-cli') or 'octave','--quiet','--no-history',str(src)]])
        elif language=='Rust':
            src=p/'driver.rs';exe=p/'driver'
            if fid.startswith('ALLOC-'):expr+='.expect("valid allocation sample")'
            if fid=='TS-003':
                body='let v='+expr+';let mut out=vec![v.last_sma,v.last_ema];out.extend(v.sma);out.extend(v.ema);'
            elif fid in SCALARS:body='let out=vec!['+expr+'];'
            else:body='let out='+expr+';'
            source+='\nfn main(){'+body+'print!("HYUN_RESULT ");for x in out{print!("{:.17} ",x);}println!();}\n'
            commands=[['rustc','--edition=2021',str(src),'-o',str(exe)],[str(exe)]]
        elif language=='C#':
            src=p/'GeneratedCalculator.cs';(p/'Driver.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>')
            if fid=='TS-003':body='var v=GeneratedCalculator.'+expr+';var outValues=new System.Collections.Generic.List<double>{v.LastSMA,v.LastEMA};outValues.AddRange(v.SMA);outValues.AddRange(v.EMA);'
            else:body='var outValues='+('new double[]{GeneratedCalculator.'+expr+'}' if fid in SCALARS else 'GeneratedCalculator.'+expr)+';'
            (p/'Program.cs').write_text('class Driver{public static void Main(){'+body+'System.Console.Write("HYUN_RESULT ");foreach(var x in outValues)System.Console.Write(x.ToString("R",System.Globalization.CultureInfo.InvariantCulture)+" ");System.Console.WriteLine();}}',encoding='utf-8')
            commands=[['dotnet','build',str(p/'Driver.csproj'),'-o',str(p/'bin'),'--verbosity','quiet'],['dotnet',str(p/'bin'/'Driver.dll')]]
        src.write_text(source,encoding='utf-8')
        for command in commands:
            run=subprocess.run(command,cwd=tmp,capture_output=True,text=True,timeout=150)
            if run.returncode:raise AssertionError(run.stderr[-2500:]+' '+run.stdout[-500:])
        verify_output(run.stdout,expected,fid,language)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('language',choices=('R','Julia','Rust','C#','Octave','MATLAB'));language=parser.parse_args().language
    records=list(samples())
    if len(records)!=33 or len({r[0] for r in records})!=33:raise AssertionError('Catalog drift')
    failed=[]
    for record in records:
        try:check(language,record);print('PASS',language,record[0],flush=True)
        except Exception as exc:failed.append(record[0]);print('FAIL',language,record[0],str(exc),flush=True)
    print(f'{language} FULL CATALOG: {33-len(failed)}/33 PASS',flush=True)
    if failed:raise SystemExit(1)
if __name__=='__main__':main()
