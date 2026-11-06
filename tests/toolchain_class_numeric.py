"""Execute exported NPV classes with explicit loops and import policies."""
import argparse
import math
import subprocess
import tempfile
from pathlib import Path
from toolchain_ci_smoke import selected_cases  # establishes project import path
from hyuncalculator.codegen import generate, GenerationOptions


def check(language, loop, imports):
    code=generate('FIN-004',GenerationOptions(language=language,structure='class',iteration=loop,imports=imports,class_name='Cashflows',function_name='discount',variable_names=(('rate','discount_rate'),('flows','cashflows'))))
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp);exe=p/'driver'
        if language=='C++':
            src=p/'driver.cpp';code+='\n#include <iostream>\n#include <iomanip>\nint main(){std::cout<<std::setprecision(17)<<Cashflows::discount(.1,{-100,60,60});}'
            commands=[['g++','-std=c++17','-Wall','-Werror',str(src),'-o',str(exe)],[str(exe)]]
        elif language=='TypeScript':
            src=p/'driver.ts';code+='\nconsole.log(Cashflows.discount(.1,[-100,60,60]));'
            commands=[['tsc','--target','ES2020','--module','commonjs','--outDir',tmp,str(src)],['node',str(p/'driver.js')]]
        elif language=='Java':
            src=p/'Cashflows.java';code+='\nclass Driver{public static void main(String[] args){System.out.print(Cashflows.discount(.1,new double[]{-100,60,60}));}}'
            commands=[['javac',str(src)],['java','-cp',tmp,'Driver']]
        elif language=='C#':
            src=p/'Cashflows.cs';(p/'Driver.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>')
            code+='\nclass Driver{public static void Main(){System.Console.Write(Cashflows.discount(.1,new double[]{-100,60,60}).ToString("R",System.Globalization.CultureInfo.InvariantCulture));}}'
            commands=[['dotnet','build',str(p/'Driver.csproj'),'-o',str(p/'bin'),'--verbosity','quiet'],['dotnet',str(p/'bin'/'Driver.dll')]]
        elif language=='Swift':
            src=p/'driver.swift';code+='\nprint(Cashflows.discount(0.1,[-100,60,60]))'
            commands=[['swiftc',str(src),'-o',str(exe)],[str(exe)]]
        elif language=='Kotlin':
            src=p/'driver.kt';code+='\nfun main(){print(Cashflows.discount(0.1,doubleArrayOf(-100.0,60.0,60.0)))}'
            commands=[['kotlinc',str(src),'-include-runtime','-d',str(p/'driver.jar')],['java','-jar',str(p/'driver.jar')]]
        else: raise ValueError(language)
        src.write_text(code,encoding='utf-8')
        for command in commands:
            result=subprocess.run(command,cwd=tmp,text=True,capture_output=True,timeout=120)
            if result.returncode:raise AssertionError(result.stderr[-3000:])
        value=float(result.stdout.strip())
        if not math.isclose(value,4.132231404958667,abs_tol=1e-10):raise AssertionError(value)

def main():
    p=argparse.ArgumentParser();p.add_argument('language');language=p.parse_args().language
    for loop in ('for','while'):
        for imports in ('auto','standard'):
            check(language,loop,imports);print('PASS NPV class',language,loop,imports,flush=True)
if __name__=='__main__':main()
