"""SMA and EMA source generator for 13 languages (Python handled separately).

SMA uses cumulative sums as the v1.1.0 NumPy implementation does. EMA uses
alpha=2/(window+1), seeded at the first element. Result includes entire series.
C caller provides output arrays sized n-window+1 and n respectively.
"""
from __future__ import annotations
from .emitter import GenerationError

SUPPORTED = frozenset({'qf_moving'})


def generate_moving(fn, formula, options):
    if options.language == 'Python': raise GenerationError('Python uses reference emitter')
    if options.structure != 'function' or options.iteration != 'auto' or options.variable_names or options.variant != 'periodic':
        raise GenerationError('Moving-average adapter supports function/auto, standard parameters only')
    l = options.language
    note = 'HyunCalculator TS-003: SMA complete windows, EMA seeded by first sample; [lastSMA,lastEMA,SMA series,EMA series]'
    if l == 'R':
        return f'''# {note}
{fn} <- function(values, window) {{
  if (length(values)<1 || any(!is.finite(values)) || length(window)!=1 || !is.finite(window) || window!=trunc(window) || window<1 || window>length(values)) stop("Invalid moving-average inputs")
  n<-length(values);sma<-numeric(n-window+1);ema<-numeric(n);ema[1]<-values[1]
  acc<-sum(values[1:window]);sma[1]<-acc/window
  if(window<n) for(i in (window+1):n) {{acc<-acc+values[i]-values[i-window];sma[i-window+1]<-acc/window}}
  alpha<-2/(window+1)
  if(n>1) for(i in 2:n) ema[i]<-alpha*values[i]+(1-alpha)*ema[i-1]
  return(list(last_sma=tail(sma,1),last_ema=tail(ema,1),sma=sma,ema=ema))
}}
'''
    if l == 'MATLAB':
        return f'''% {note}
function result = {fn}(values,window)
  if isempty(values) || any(~isfinite(values)) || ~isscalar(window) || ~isfinite(window) || window~=fix(window) || window<1 || window>numel(values)
    error('Invalid moving-average inputs');
  end
  v=values(:)';n=numel(v);sma=zeros(1,n-window+1);ema=zeros(1,n);ema(1)=v(1);
  acc=sum(v(1:window));sma(1)=acc/window;
  for i=window+1:n
    acc=acc+v(i)-v(i-window);sma(i-window+1)=acc/window;
  end
  alpha=2/(window+1);
  for i=2:n
    ema(i)=alpha*v(i)+(1-alpha)*ema(i-1);
  end
  result=struct('last_sma',sma(end),'last_ema',ema(end),'sma',sma,'ema',ema);
end
'''
    if l == 'Julia':
        return f'''# {note}
function {fn}(values,window)
  n=length(values)
  if n<1 || !all(isfinite,values) || !(window isa Integer) || window<1 || window>n
    throw(ArgumentError("Invalid moving-average inputs"))
  end
  v=Float64.(values);sma=Vector{{Float64}}(undef,n-window+1);ema=Vector{{Float64}}(undef,n)
  ema[1]=v[1];acc=sum(v[1:window]);sma[1]=acc/window
  for i in window+1:n
    acc+=v[i]-v[i-window];sma[i-window+1]=acc/window
  end
  alpha=2/(window+1)
  for i in 2:n
    ema[i]=alpha*v[i]+(1-alpha)*ema[i-1]
  end
  return (last_sma=sma[end],last_ema=ema[end],sma=sma,ema=ema)
end
'''
    if l == 'C':
        return f'''/* {note} */
#include <math.h>
#include <stddef.h>
typedef struct {{double last_sma,last_ema;size_t sma_count,ema_count;}} HyunMovingResult;
/* sma_out must hold count-window+1 doubles; ema_out must hold count doubles. */
HyunMovingResult {fn}(const double* values,size_t count,size_t window,double* sma_out,double* ema_out) {{
  HyunMovingResult fail={{NAN,NAN,0,0}};
  if(!values||!sma_out||!ema_out||!count||window<1||window>count) return fail;
  for(size_t i=0;i<count;i++) if(!isfinite(values[i]))return fail;
  double acc=0;for(size_t i=0;i<window;i++) acc+=values[i];sma_out[0]=acc/window;
  for(size_t i=window;i<count;i++){{acc+=values[i]-values[i-window];sma_out[i-window+1]=acc/window;}}
  double alpha=2.0/(window+1.0);ema_out[0]=values[0];
  for(size_t i=1;i<count;i++)ema_out[i]=alpha*values[i]+(1-alpha)*ema_out[i-1];
  HyunMovingResult out={{sma_out[count-window],ema_out[count-1],count-window+1,count}};return out;
}}
'''
    if l == 'C++':
        return f'''// {note}
#include <cmath>
#include <vector>
#include <stdexcept>
struct HyunMovingResult {{double last_sma,last_ema;std::vector<double> sma,ema;}};
HyunMovingResult {fn}(const std::vector<double>& values,size_t window) {{
  const size_t n=values.size();
  if(!n||!window||window>n)throw std::invalid_argument("Invalid window");
  for(double x:values)if(!std::isfinite(x))throw std::invalid_argument("Nonfinite observation");
  HyunMovingResult res;res.sma.resize(n-window+1);res.ema.resize(n);
  double acc=0;for(size_t i=0;i<window;i++)acc+=values[i];res.sma[0]=acc/window;
  for(size_t i=window;i<n;i++){{acc+=values[i]-values[i-window];res.sma[i-window+1]=acc/window;}}
  const double alpha=2.0/(window+1.0);res.ema[0]=values[0];
  for(size_t i=1;i<n;i++)res.ema[i]=alpha*values[i]+(1-alpha)*res.ema[i-1];
  res.last_sma=res.sma.back();res.last_ema=res.ema.back();return res;
}}
'''
    if l in ('JavaScript','TypeScript'):
        p='values: number[], window: number' if l=='TypeScript' else 'values, window'
        ret=': {lastSMA:number;lastEMA:number;sma:number[];ema:number[]}' if l=='TypeScript' else ''
        return f'''// {note}
export function {fn}({p}){ret} {{
  if(!Array.isArray(values)||!values.length||!values.every(Number.isFinite)||!Number.isInteger(window)||window<1||window>values.length)throw new RangeError("Invalid moving-average inputs");
  const n=values.length,sma=new Array(n-window+1),ema=new Array(n);
  let acc=0;for(let i=0;i<window;i++)acc+=values[i];sma[0]=acc/window;
  for(let i=window;i<n;i++){{acc+=values[i]-values[i-window];sma[i-window+1]=acc/window;}}
  const alpha=2/(window+1);ema[0]=values[0];
  for(let i=1;i<n;i++)ema[i]=alpha*values[i]+(1-alpha)*ema[i-1];
  return {{lastSMA:sma[sma.length-1],lastEMA:ema[n-1],sma,ema}};
}}
'''
    if l == 'Java':
        return f'''// {note}
public class GeneratedCalculator {{
  public static class MovingResult {{
    public final double lastSMA,lastEMA;public final double[] sma,ema;
    public MovingResult(double a,double b,double[] c,double[] d){{lastSMA=a;lastEMA=b;sma=c;ema=d;}}
  }}
  public static MovingResult {fn}(double[] values,int window){{
    if(values==null||values.length==0||window<1||window>values.length)throw new IllegalArgumentException("Invalid moving-average inputs");
    for(double x:values)if(!Double.isFinite(x))throw new IllegalArgumentException("Nonfinite observation");
    int n=values.length;double[] sma=new double[n-window+1],ema=new double[n];
    double acc=0;for(int i=0;i<window;i++)acc+=values[i];sma[0]=acc/window;
    for(int i=window;i<n;i++){{acc+=values[i]-values[i-window];sma[i-window+1]=acc/window;}}
    double alpha=2.0/(window+1);ema[0]=values[0];
    for(int i=1;i<n;i++)ema[i]=alpha*values[i]+(1-alpha)*ema[i-1];
    return new MovingResult(sma[sma.length-1],ema[n-1],sma,ema);
  }}
}}
'''
    if l == 'C#':
        return f'''// {note}
using System;
public static class GeneratedCalculator {{
  public sealed class MovingResult {{
    public double LastSMA {{get;}} public double LastEMA {{get;}}
    public double[] SMA {{get;}} public double[] EMA {{get;}}
    public MovingResult(double a,double b,double[] c,double[] d){{LastSMA=a;LastEMA=b;SMA=c;EMA=d;}}
  }}
  public static MovingResult {fn}(double[] values,int window) {{
    if(values==null||values.Length==0||window<1||window>values.Length)throw new ArgumentException("Invalid moving-average inputs");
    foreach(double x in values)if(!double.IsFinite(x))throw new ArgumentException("Nonfinite observation");
    int n=values.Length;var sma=new double[n-window+1];var ema=new double[n];
    double acc=0;for(int i=0;i<window;i++)acc+=values[i];sma[0]=acc/window;
    for(int i=window;i<n;i++){{acc+=values[i]-values[i-window];sma[i-window+1]=acc/window;}}
    double alpha=2.0/(window+1);ema[0]=values[0];
    for(int i=1;i<n;i++)ema[i]=alpha*values[i]+(1-alpha)*ema[i-1];
    return new MovingResult(sma[sma.Length-1],ema[n-1],sma,ema);
  }}
}}
'''
    if l == 'Swift':
        return f'''// {note}
import Foundation
func {fn}(_ values:[Double],_ window:Int)->(lastSMA:Double,lastEMA:Double,sma:[Double],ema:[Double]) {{
  guard !values.isEmpty,window>=1,window<=values.count,values.allSatisfy({{$0.isFinite}}) else {{return (Double.nan,Double.nan,[],[])}}
  let n=values.count;var sma=[Double](repeating:0,count:n-window+1);var ema=[Double](repeating:0,count:n)
  var acc=0.0;for i in 0..<window{{acc+=values[i]}};sma[0]=acc/Double(window)
  if window<n{{for i in window..<n{{acc+=values[i]-values[i-window];sma[i-window+1]=acc/Double(window)}}}}
  let alpha=2.0/Double(window+1);ema[0]=values[0]
  if n>1{{for i in 1..<n{{ema[i]=alpha*values[i]+(1-alpha)*ema[i-1]}}}}
  return (sma[sma.count-1],ema[n-1],sma,ema)
}}
'''
    if l == 'Kotlin':
        return f'''// {note}
import kotlin.math.*
data class MovingResult(val lastSMA:Double,val lastEMA:Double,val sma:DoubleArray,val ema:DoubleArray)
fun {fn}(values:DoubleArray,window:Int):MovingResult {{
  require(values.isNotEmpty()&&window>=1&&window<=values.size&&values.all{{it.isFinite()}}){{"Invalid moving-average inputs"}}
  val n=values.size;val sma=DoubleArray(n-window+1);val ema=DoubleArray(n)
  var acc=0.0;for(i in 0 until window)acc+=values[i];sma[0]=acc/window
  for(i in window until n){{acc+=values[i]-values[i-window];sma[i-window+1]=acc/window}}
  val alpha=2.0/(window+1);ema[0]=values[0]
  for(i in 1 until n)ema[i]=alpha*values[i]+(1-alpha)*ema[i-1]
  return MovingResult(sma.last(),ema.last(),sma,ema)
}}
'''
    if l == 'Go':
        return f'''// {note}
package main
import "math"
type MovingResult struct{{LastSMA,LastEMA float64;SMA,EMA []float64}}
func {fn}(values []float64,window int)MovingResult{{
  fail:=MovingResult{{LastSMA:math.NaN(),LastEMA:math.NaN()}}
  n:=len(values);if n<1||window<1||window>n{{return fail}}
  for _,x:=range values{{if math.IsNaN(x)||math.IsInf(x,0){{return fail}}}}
  sma:=make([]float64,n-window+1);ema:=make([]float64,n)
  acc:=0.0;for i:=0;i<window;i++{{acc+=values[i]}};sma[0]=acc/float64(window)
  for i:=window;i<n;i++{{acc+=values[i]-values[i-window];sma[i-window+1]=acc/float64(window)}}
  alpha:=2.0/float64(window+1);ema[0]=values[0]
  for i:=1;i<n;i++{{ema[i]=alpha*values[i]+(1-alpha)*ema[i-1]}}
  return MovingResult{{sma[len(sma)-1],ema[n-1],sma,ema}}
}}
'''
    if l == 'Rust':
        return f'''// {note}
#[derive(Debug)]
pub struct MovingResult{{pub last_sma:f64,pub last_ema:f64,pub sma:Vec<f64>,pub ema:Vec<f64>}}
pub fn {fn}(values:&[f64],window:usize)->MovingResult{{
  let fail=||MovingResult{{last_sma:f64::NAN,last_ema:f64::NAN,sma:vec![],ema:vec![]}};
  let n=values.len();if n<1||window<1||window>n||!values.iter().all(|x|x.is_finite()){{return fail();}}
  let(mut sma,mut ema)=(vec![0.0;n-window+1],vec![0.0;n]);
  let mut acc=0.0;for i in 0..window{{acc+=values[i];}}sma[0]=acc/window as f64;
  for i in window..n{{acc+=values[i]-values[i-window];sma[i-window+1]=acc/window as f64;}}
  let alpha=2.0/(window+1) as f64;ema[0]=values[0];
  for i in 1..n{{ema[i]=alpha*values[i]+(1.0-alpha)*ema[i-1];}}
  MovingResult{{last_sma:sma[sma.len()-1],last_ema:ema[n-1],sma,ema}}
}}
'''
    raise GenerationError(f'{l}: moving-average adapter not implemented')
