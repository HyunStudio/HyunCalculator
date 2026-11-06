"""Standalone Monte Carlo European option exporters for 13 non-Python targets.

Antithetic GBM terminal sampling with a shared Park-Miller 31-bit LCG and
Box-Muller transform. All emitted runtimes use the same deterministic stream.
Python's existing exporter retains NumPy PCG64, so same-seed bitwise parity with
Python is NOT promised; mathematical expectation and paired SE semantics agree.
"""
from __future__ import annotations

from .emitter import GenerationError

SUPPORTED = frozenset({'qf_mc'})
M = '2147483647'
NOTE = ("European antithetic Monte Carlo; Park-Miller 16807 + Box-Muller, "
        "pair-based SE and 95% CI. Portable seed must be 1..2147483646; "
        "RNG differs from Python/NumPy PCG64. Results: price, paired SE, CI low/high.")


def _check(formula, opt):
    if formula.function not in SUPPORTED or opt.language == 'Python':
        raise GenerationError('Portable Monte Carlo adapter accepts non-Python DERIV-003')
    if opt.structure != 'function' or opt.iteration != 'auto' or opt.variable_names or opt.variant != 'periodic':
        raise GenerationError('Portable Monte Carlo requires function/auto/canonical parameters')
    if opt.imports not in ('auto','standard'):
        raise GenerationError('Portable Monte Carlo requires standard math libraries')


def _c_family(fn, lang):
    math_names = {
        'C': ('exp','sqrt','log','cos','fmax','isfinite'),
        'C++': ('std::exp','std::sqrt','std::log','std::cos','std::max','std::isfinite'),
        'JavaScript': ('Math.exp','Math.sqrt','Math.log','Math.cos','Math.max','Number.isFinite'),
        'TypeScript': ('Math.exp','Math.sqrt','Math.log','Math.cos','Math.max','Number.isFinite'),
        'Java': ('Math.exp','Math.sqrt','Math.log','Math.cos','Math.max','Double.isFinite'),
        'C#': ('Math.Exp','Math.Sqrt','Math.Log','Math.Cos','Math.Max','double.IsFinite'),
    }
    exp, sqrt, log, cos, max_fn, finite = math_names[lang]
    is_js = lang in ('JavaScript','TypeScript')
    state_type = {'C':'long long','C++':'long long','JavaScript':'let','TypeScript':'let','Java':'long','C#':'long'}[lang]
    dec_type = {'C':'double','C++':'double','JavaScript':'const','TypeScript':'const','Java':'double','C#':'double'}[lang]
    mutable = {'C':'double','C++':'double','JavaScript':'let','TypeScript':'let','Java':'double','C#':'double'}[lang]
    index_type = {'C':'int','C++':'int','JavaScript':'let','TypeScript':'let','Java':'int','C#':'int'}[lang]
    assign_int = ('let' if is_js else 'int')
    declare_z = f'{dec_type} z'
    if lang == 'C':
        header = '#include <math.h>\n#include <string.h>\n#include <stdint.h>\n'
        result_type = 'HyunMCResult'
        signature = f'HyunMCResult {fn}(double s,double k,double t,double r,double sigma,double q,const char* option,int paths,long long seed)'
        check_option = '(option == NULL || (strcmp(option,"call")!=0 && strcmp(option,"put")!=0))'
        sign = '(strcmp(option,"call")==0 ? 1.0 : -1.0)'
        fail = 'return (HyunMCResult){NAN,NAN,NAN,NAN};'
        output = 'return (HyunMCResult){mean,se,mean-1.96*se,mean+1.96*se};'
        header += 'typedef struct {double price,paired_se,ci_low,ci_high;} HyunMCResult;\n'
    elif lang == 'C++':
        header = '#include <array>\n#include <algorithm>\n#include <cmath>\n#include <stdexcept>\n#include <string>\n'
        signature = f'std::array<double,4> {fn}(double s,double k,double t,double r,double sigma,double q,const std::string& option,int paths,long long seed)'
        check_option = '(option!="call" && option!="put")'
        sign = '(option=="call" ? 1.0 : -1.0)'
        fail = 'throw std::invalid_argument("Invalid Monte Carlo inputs");'
        output = 'return {mean,se,mean-1.96*se,mean+1.96*se};'
    elif is_js:
        header = ''
        signature = (f'export function {fn}(s: number,k: number,t: number,r: number,sigma: number,q: number,option: string,paths: number,seed: number): number[]'
                     if lang=='TypeScript' else f'export function {fn}(s,k,t,r,sigma,q,option,paths,seed)')
        check_option = '(option!=="call" && option!=="put")'
        sign = '(option==="call" ? 1.0 : -1.0)'
        fail = 'throw new RangeError("Invalid Monte Carlo inputs");'
        output = 'return [mean,se,mean-1.96*se,mean+1.96*se];'
    elif lang == 'Java':
        header = ''
        signature = f'public static double[] {fn}(double s,double k,double t,double r,double sigma,double q,String option,int paths,long seed)'
        check_option = '(option==null || (!option.equals("call") && !option.equals("put")))'
        sign = '(option.equals("call") ? 1.0 : -1.0)'
        fail = 'throw new IllegalArgumentException("Invalid Monte Carlo inputs");'
        output = 'return new double[]{mean,se,mean-1.96*se,mean+1.96*se};'
    else:  # C#
        header = 'using System;\n'
        signature = f'public static double[] {fn}(double s,double k,double t,double r,double sigma,double q,string option,int paths,long seed)'
        check_option = '(option!="call" && option!="put")'
        sign = '(option=="call" ? 1.0 : -1.0)'
        fail = 'throw new ArgumentException("Invalid Monte Carlo inputs");'
        output = 'return new double[]{mean,se,mean-1.96*se,mean+1.96*se};'
    validation = (f'!{finite}(s)||!{finite}(k)||!{finite}(t)||!{finite}(r)||'
                  f'!{finite}(sigma)||!{finite}(q)||s<=0||k<=0||t<=0||sigma<0||'
                  f'paths<100||paths>1000000||paths%2!=0||seed<1||seed>=2147483647||{check_option}')
    if is_js: validation += '||!Number.isSafeInteger(paths)||!Number.isSafeInteger(seed)'
    core = f'''// {NOTE}
{signature} {{
    if ({validation}) {{ {fail} }}
    {dec_type} sign = {sign};
    {dec_type} drift = (r-q-0.5*sigma*sigma)*t;
    {dec_type} volStep = sigma*{sqrt}(t);
    {dec_type} disc = {exp}(-r*t);
    {state_type} state = seed;
    {mutable} mean = 0.0;
    {mutable} m2 = 0.0;
    {assign_int} pairs = paths/2;
    for ({index_type} i=1;i<=pairs;++i) {{
        state = (state*16807) % 2147483647;
        {dec_type} u1 = (double)state/2147483647.0;
        state = (state*16807) % 2147483647;
        {dec_type} u2 = (double)state/2147483647.0;
        {declare_z} = {sqrt}(-2.0*{log}(u1))*{cos}(6.283185307179586*u2);
        {dec_type} st1 = s*{exp}(drift+volStep*z);
        {dec_type} st2 = s*{exp}(drift-volStep*z);
        {dec_type} pair = 0.5*disc*({max_fn}(0.0,sign*(st1-k))+{max_fn}(0.0,sign*(st2-k)));
        {dec_type} delta = pair-mean;
        mean += delta/i;
        m2 += delta*(pair-mean);
    }}
    {dec_type} se = {sqrt}((m2/(pairs-1))/pairs);
    {output}
}}
'''
    # JS/TS variables are IEEE doubles, not C casts. Others use exact 64-bit integer states.
    if is_js:
        core=core.replace('(double)state','state')
    elif lang in ('Java','C#'):
        core=core.replace('(double)state','(double)state')
    elif lang=='C++':
        core=core.replace('(double)state','static_cast<double>(state)')
    if lang=='Java':core='public class GeneratedCalculator {\n'+''.join('  '+x+'\n' for x in core.rstrip().splitlines())+'}\n'
    if lang=='C#':core='public static class GeneratedCalculator {\n'+''.join('  '+x+'\n' for x in core.rstrip().splitlines())+'}\n'
    return header+'\n'+core


def _other(fn, lang):
    if lang=='R':
        return f'''# {NOTE}
{fn} <- function(s,k,t,r,sigma,q,option,paths,seed) {{
  if(any(!is.finite(c(s,k,t,r,sigma,q,paths,seed))) || s<=0 || k<=0 || t<=0 || sigma<0 || paths<100 || paths>1000000 || paths%%2!=0 || paths!=floor(paths) || seed<1 || seed>=2147483647 || seed!=floor(seed) || !(option %in% c("call","put")))stop("Invalid Monte Carlo inputs")
  sign <- if (option=="call") 1.0 else -1.0
  drift <- (r-q-0.5*sigma*sigma)*t; volStep <- sigma*sqrt(t); disc <- exp(-r*t)
  state <- as.numeric(seed); mean <- 0.0; m2 <- 0.0; pairs <- paths/2
  for (i in seq_len(pairs)) {{
    state <- (state*16807) %% 2147483647; u1 <- state/2147483647
    state <- (state*16807) %% 2147483647; u2 <- state/2147483647
    z <- sqrt(-2*log(u1))*cos(6.283185307179586*u2)
    st1 <- s*exp(drift+volStep*z); st2 <- s*exp(drift-volStep*z)
    pair <- 0.5*disc*(max(0,sign*(st1-k))+max(0,sign*(st2-k)))
    delta <- pair-mean; mean <- mean+delta/i; m2 <- m2+delta*(pair-mean)
  }}
  se <- sqrt((m2/(pairs-1))/pairs)
  c(price=mean,paired_se=se,ci_low=mean-1.96*se,ci_high=mean+1.96*se)
}}
'''
    if lang=='MATLAB':
        return f'''% {NOTE}
function result = {fn}(s,k,t,r,sigma,q,option,paths,seed)
  if any(~isfinite([s,k,t,r,sigma,q,paths,seed])) || s<=0 || k<=0 || t<=0 || sigma<0 || paths<100 || paths>1000000 || mod(paths,2)~=0 || paths~=floor(paths) || seed<1 || seed>=2147483647 || seed~=floor(seed) || ~(strcmp(option,'call') || strcmp(option,'put'))
    error('Invalid Monte Carlo inputs');
  end
  sign = 1; if strcmp(option,'put'); sign=-1; end
  drift=(r-q-0.5*sigma*sigma)*t; volStep=sigma*sqrt(t); disc=exp(-r*t);
  state=double(seed); pairCount=paths/2; avg=0; m2=0;
  for i=1:pairCount
    state=mod(state*16807,2147483647); u1=state/2147483647;
    state=mod(state*16807,2147483647); u2=state/2147483647;
    z=sqrt(-2*log(u1))*cos(6.283185307179586*u2);
    st1=s*exp(drift+volStep*z); st2=s*exp(drift-volStep*z);
    sample=0.5*disc*(max(0,sign*(st1-k))+max(0,sign*(st2-k)));
    delta=sample-avg; avg=avg+delta/i; m2=m2+delta*(sample-avg);
  end
  se=sqrt((m2/(pairCount-1))/pairCount);
  result=[avg,se,avg-1.96*se,avg+1.96*se];
end
'''
    if lang=='Julia':
        return f'''# {NOTE}
function {fn}(s,k,t,r,sigma,q,option,paths,seed)
  if !all(isfinite,(s,k,t,r,sigma,q,paths,seed)) || s<=0 || k<=0 || t<=0 || sigma<0 || paths<100 || paths>1000000 || !iseven(paths) || seed<1 || seed>=2147483647 || !(option in ("call","put"))
    throw(ArgumentError("Invalid Monte Carlo inputs"))
  end
  sign=option=="call" ? 1.0 : -1.0
  drift=(r-q-0.5*sigma*sigma)*t; volStep=sigma*sqrt(t); disc=exp(-r*t)
  state=Int64(seed); count=paths÷2; avg=0.0; m2=0.0
  for i in 1:count
    state=(state*16807)%2147483647; u1=state/2147483647.0
    state=(state*16807)%2147483647; u2=state/2147483647.0
    z=sqrt(-2*log(u1))*cos(6.283185307179586*u2)
    st1=s*exp(drift+volStep*z); st2=s*exp(drift-volStep*z)
    sample=0.5*disc*(max(0.0,sign*(st1-k))+max(0.0,sign*(st2-k)))
    delta=sample-avg; avg+=delta/i; m2+=delta*(sample-avg)
  end
  se=sqrt((m2/(count-1))/count)
  return [avg,se,avg-1.96*se,avg+1.96*se]
end
'''
    if lang=='Swift':
        return f'''// {NOTE}
import Foundation
func {fn}(_ s:Double,_ k:Double,_ t:Double,_ r:Double,_ sigma:Double,_ q:Double,_ option:String,_ paths:Int,_ seed:Int64)->[Double] {{
  guard [s,k,t,r,sigma,q].allSatisfy({{$0.isFinite}}), s>0,k>0,t>0,sigma>=0,paths>=100,paths<=1000000,paths%2==0,seed>=1,seed<2147483647,(option=="call" || option=="put") else {{ return [Double.nan,Double.nan,Double.nan,Double.nan] }}
  let sign:Double=option=="call" ? 1.0 : -1.0
  let drift=(r-q-0.5*sigma*sigma)*t,volStep=sigma*sqrt(t),disc=exp(-r*t)
  var state=seed,avg=0.0,m2=0.0
  let count=paths/2
  for i in 1...count {{
    state=(state*16807)%2147483647;let u1=Double(state)/2147483647.0
    state=(state*16807)%2147483647;let u2=Double(state)/2147483647.0
    let z=sqrt(-2.0*log(u1))*cos(6.283185307179586*u2)
    let st1=s*exp(drift+volStep*z),st2=s*exp(drift-volStep*z)
    let sample=0.5*disc*(max(0.0,sign*(st1-k))+max(0.0,sign*(st2-k)))
    let delta=sample-avg;avg+=delta/Double(i);m2+=delta*(sample-avg)
  }}
  let se=sqrt((m2/Double(count-1))/Double(count))
  return [avg,se,avg-1.96*se,avg+1.96*se]
}}
'''
    if lang=='Kotlin':
        return f'''// {NOTE}
import kotlin.math.*
fun {fn}(s:Double,k:Double,t:Double,r:Double,sigma:Double,q:Double,option:String,paths:Int,seed:Long):DoubleArray {{
  require(listOf(s,k,t,r,sigma,q).all{{it.isFinite()}} && s>0 && k>0 && t>0 && sigma>=0 && paths in 100..1000000 && paths%2==0 && seed in 1..2147483646 && (option=="call" || option=="put")) {{ "Invalid Monte Carlo inputs" }}
  val sign=if(option=="call")1.0 else -1.0
  val drift=(r-q-0.5*sigma*sigma)*t;val volStep=sigma*sqrt(t);val disc=exp(-r*t)
  var state=seed;var avg=0.0;var m2=0.0;val count=paths/2
  for(i in 1..count) {{
    state=(state*16807L)%2147483647L;val u1=state.toDouble()/2147483647.0
    state=(state*16807L)%2147483647L;val u2=state.toDouble()/2147483647.0
    val z=sqrt(-2.0*ln(u1))*cos(6.283185307179586*u2)
    val st1=s*exp(drift+volStep*z);val st2=s*exp(drift-volStep*z)
    val sample=0.5*disc*(max(0.0,sign*(st1-k))+max(0.0,sign*(st2-k)))
    val delta=sample-avg;avg+=delta/i;m2+=delta*(sample-avg)
  }}
  val se=sqrt((m2/(count-1))/count)
  return doubleArrayOf(avg,se,avg-1.96*se,avg+1.96*se)
}}
'''
    if lang=='Go':
        return f'''// {NOTE}
package main
import "math"
func {fn}(s,k,t,r,sigma,q float64,option string,paths int,seed int64)[4]float64 {{
  if math.IsNaN(s)||math.IsNaN(k)||math.IsNaN(t)||math.IsNaN(r)||math.IsNaN(sigma)||math.IsNaN(q)||math.IsInf(s,0)||math.IsInf(k,0)||math.IsInf(t,0)||math.IsInf(r,0)||math.IsInf(sigma,0)||math.IsInf(q,0)||s<=0||k<=0||t<=0||sigma<0||paths<100||paths>1000000||paths%2!=0||seed<1||seed>=2147483647||(option!="call"&&option!="put") {{ bad:=math.NaN();return [4]float64{{bad,bad,bad,bad}} }}
  sign:=1.0;if option=="put"{{sign=-1.0}}
  drift:=(r-q-0.5*sigma*sigma)*t;volStep:=sigma*math.Sqrt(t);disc:=math.Exp(-r*t)
  state:=seed;avg:=0.0;m2:=0.0;count:=paths/2
  for i:=1;i<=count;i++{{
    state=(state*16807)%2147483647;u1:=float64(state)/2147483647.0
    state=(state*16807)%2147483647;u2:=float64(state)/2147483647.0
    z:=math.Sqrt(-2.0*math.Log(u1))*math.Cos(6.283185307179586*u2)
    st1:=s*math.Exp(drift+volStep*z);st2:=s*math.Exp(drift-volStep*z)
    sample:=0.5*disc*(math.Max(0,sign*(st1-k))+math.Max(0,sign*(st2-k)))
    delta:=sample-avg;avg+=delta/float64(i);m2+=delta*(sample-avg)
  }}
  se:=math.Sqrt((m2/float64(count-1))/float64(count))
  return [4]float64{{avg,se,avg-1.96*se,avg+1.96*se}}
}}
'''
    if lang=='Rust':
        return f'''// {NOTE}
pub fn {fn}(s:f64,k:f64,t:f64,r:f64,sigma:f64,q:f64,option:&str,paths:usize,seed:i64)->[f64;4]{{
  if ![s,k,t,r,sigma,q].iter().all(|v|v.is_finite())||s<=0.0||k<=0.0||t<=0.0||sigma<0.0||paths<100||paths>1000000||paths%2!=0||seed<1||seed>=2147483647||(option!="call"&&option!="put"){{return [f64::NAN;4]}}
  let sign:f64=if option=="call"{{1.0}}else{{-1.0}};
  let drift=(r-q-0.5*sigma*sigma)*t;let vol_step=sigma*t.sqrt();let disc=(-r*t).exp();
  let mut state=seed;let mut avg=0.0;let mut m2=0.0;let count=paths/2;
  for i in 1..=count {{
    state=(state*16807)%2147483647;let u1=state as f64/2147483647.0;
    state=(state*16807)%2147483647;let u2=state as f64/2147483647.0;
    let z=(-2.0*u1.ln()).sqrt()*(6.283185307179586_f64*u2).cos();
    let st1=s*(drift+vol_step*z).exp();let st2=s*(drift-vol_step*z).exp();
    let sample=0.5*disc*(0.0_f64.max(sign*(st1-k))+0.0_f64.max(sign*(st2-k)));
    let delta=sample-avg;avg+=delta/i as f64;m2+=delta*(sample-avg);
  }}
  let se=(m2/(count-1) as f64/count as f64).sqrt();
  [avg,se,avg-1.96*se,avg+1.96*se]
}}
'''
    raise GenerationError(f'Monte Carlo emitter not implemented for {lang}')


def generate_mc(fn, formula, opt):
    _check(formula,opt)
    if opt.language in ('C','C++','JavaScript','TypeScript','Java','C#'):
        return _c_family(fn,opt.language)
    return _other(fn,opt.language)
