"""Portable standalone performance analyzer (risk_metrics) for 13 languages.

Outputs in this order: [annualized_mean, annualized_vol, annualized_sharpe,
annualized_sortino, max_drawdown, compounded_total_return].
"""
from __future__ import annotations
SUPPORTED=frozenset({'qf_performance'})


def generate_performance(fn,formula,opt):
    from .emitter import GenerationError
    if opt.language=='Python' or opt.structure!='function' or opt.iteration!='auto' or opt.variable_names or opt.variant!='periodic' or opt.imports not in ('auto','standard'):
        raise GenerationError('Performance profile supports non-Python function/auto/standard imports only')
    lang=opt.language
    note='HyunCalculator RISK-003: [annual mean, annual vol, Sharpe, Sortino, maximum drawdown, compounded return]; simple returns per period, sample ddof=1.'
    if lang=='C':
        return f'''/* {note} */
#include <math.h>
#include <stddef.h>
typedef struct {{ double values[6]; }} HyunPerformance;
HyunPerformance {fn}(const double *r,size_t n,double rf,int ppy){{
  HyunPerformance bad={{{{NAN,NAN,NAN,NAN,NAN,NAN}}}};
  if(!r||n<3||n>1000000||!isfinite(rf)||ppy<1||ppy>1000000)return bad;
  double total=0,ex=0,wealth=1,peak=1,mdd=0,down=0;
  for(size_t i=0;i<n;i++){{double x=r[i];if(!isfinite(x)||x<=-1)return bad;total+=x;ex+=x-rf;double d=fmin(x-rf,0);down+=d*d;wealth*=1+x;peak=fmax(peak,wealth);mdd=fmin(mdd,wealth/peak-1);}}
  double avg=ex/n,sq=0;
  for(size_t i=0;i<n;i++){{double e=r[i]-rf-avg;sq+=e*e;}}
  double st=sqrt(sq/(n-1)),dv=sqrt(down/n),an=sqrt((double)ppy);
  HyunPerformance out={{{{total/n*ppy,st*an,st>0?avg/st*an:NAN,dv>0?avg/dv*an:NAN,mdd,wealth-1}}}};
  return out;
}}
'''
    if lang=='C++':
        return f'''// {note}
#include <array>
#include <vector>
#include <cmath>
#include <algorithm>
#include <stdexcept>
std::array<double,6> {fn}(const std::vector<double>& r,double rf,int ppy){{
  const size_t n=r.size();if(n<3||n>1000000||!std::isfinite(rf)||ppy<1||ppy>1000000)throw std::invalid_argument("Invalid performance inputs");
  double total=0,ex=0,wealth=1,peak=1,mdd=0,down=0;
  for(double x:r){{if(!std::isfinite(x)||x<=-1)throw std::invalid_argument("Invalid return");total+=x;ex+=x-rf;double d=std::min(x-rf,0.0);down+=d*d;wealth*=1+x;peak=std::max(peak,wealth);mdd=std::min(mdd,wealth/peak-1);}}
  double avg=ex/n,sq=0;
  for(double x:r){{double e=x-rf-avg;sq+=e*e;}}
  double st=std::sqrt(sq/(n-1)),dv=std::sqrt(down/n),an=std::sqrt(double(ppy));
  return {{total/n*ppy,st*an,st>0?avg/st*an:NAN,dv>0?avg/dv*an:NAN,mdd,wealth-1}};
}}
'''
    if lang in ('JavaScript','TypeScript'):
        args='r: number[], rf: number, ppy: number' if lang=='TypeScript' else 'r, rf, ppy'
        ret=': number[]' if lang=='TypeScript' else ''
        return f'''// {note}
export function {fn}({args}){ret}{{
  if(!Array.isArray(r)||r.length<3||r.length>1000000||!Number.isFinite(rf)||!Number.isInteger(ppy)||ppy<1||ppy>1000000)throw new RangeError("Invalid performance inputs");
  const n=r.length;let total=0,ex=0,wealth=1,peak=1,mdd=0,down=0;
  for(const x of r){{if(!Number.isFinite(x)||x<=-1)throw new RangeError("Invalid return");total+=x;ex+=x-rf;const d=Math.min(x-rf,0);down+=d*d;wealth*=1+x;peak=Math.max(peak,wealth);mdd=Math.min(mdd,wealth/peak-1);}}
  const avg=ex/n;let sq=0;for(const x of r){{const e=x-rf-avg;sq+=e*e;}}
  const st=Math.sqrt(sq/(n-1)),dv=Math.sqrt(down/n),an=Math.sqrt(ppy);
  return [total/n*ppy,st*an,st>0?avg/st*an:NaN,dv>0?avg/dv*an:NaN,mdd,wealth-1];
}}
'''
    if lang=='Java':
        return f'''// {note}
public class GeneratedCalculator{{
  public static double[] {fn}(double[] r,double rf,int ppy){{
    if(r==null||r.length<3||r.length>1000000||!Double.isFinite(rf)||ppy<1||ppy>1000000)throw new IllegalArgumentException("Invalid performance inputs");
    int n=r.length;double total=0,ex=0,wealth=1,peak=1,mdd=0,down=0;
    for(double x:r){{if(!Double.isFinite(x)||x<=-1)throw new IllegalArgumentException("Invalid return");total+=x;ex+=x-rf;double d=Math.min(x-rf,0);down+=d*d;wealth*=1+x;peak=Math.max(peak,wealth);mdd=Math.min(mdd,wealth/peak-1);}}
    double avg=ex/n,sq=0;for(double x:r){{double e=x-rf-avg;sq+=e*e;}}
    double st=Math.sqrt(sq/(n-1)),dv=Math.sqrt(down/n),an=Math.sqrt(ppy);
    return new double[]{{total/n*ppy,st*an,st>0?avg/st*an:Double.NaN,dv>0?avg/dv*an:Double.NaN,mdd,wealth-1}};
  }}
}}
'''
    if lang=='C#':
        return f'''// {note}
using System;
public static class GeneratedCalculator{{
  public static double[] {fn}(double[] r,double rf,int ppy){{
    if(r==null||r.Length<3||r.Length>1000000||!double.IsFinite(rf)||ppy<1||ppy>1000000)throw new ArgumentException("Invalid performance inputs");
    int n=r.Length;double total=0,ex=0,wealth=1,peak=1,mdd=0,down=0;
    foreach(double x in r){{if(!double.IsFinite(x)||x<=-1)throw new ArgumentException("Invalid return");total+=x;ex+=x-rf;double d=Math.Min(x-rf,0);down+=d*d;wealth*=1+x;peak=Math.Max(peak,wealth);mdd=Math.Min(mdd,wealth/peak-1);}}
    double avg=ex/n,sq=0;foreach(double x in r){{double e=x-rf-avg;sq+=e*e;}}
    double st=Math.Sqrt(sq/(n-1)),dv=Math.Sqrt(down/n),an=Math.Sqrt(ppy);
    return new double[]{{total/n*ppy,st*an,st>0?avg/st*an:double.NaN,dv>0?avg/dv*an:double.NaN,mdd,wealth-1}};
  }}
}}
'''
    if lang=='Swift':
        return f'''// {note}
import Foundation
func {fn}(_ r:[Double],_ rf:Double,_ ppy:Int)->[Double]{{
  let n=r.count;if n<3 || n>1000000 || !rf.isFinite || ppy<1 || ppy>1000000 {{return []}}
  var total=0.0,ex=0.0,wealth=1.0,peak=1.0,mdd=0.0,down=0.0
  for x in r{{if !x.isFinite || x<=(-1) {{return []}};total+=x;ex+=x-rf;let d=min(x-rf,0);down+=d*d;wealth*=1+x;peak=max(peak,wealth);mdd=min(mdd,wealth/peak-1)}}
  let avg=ex/Double(n);var sq=0.0
  for x in r{{let e=x-rf-avg;sq+=e*e}}
  let st=sqrt(sq/Double(n-1)),dv=sqrt(down/Double(n)),an=sqrt(Double(ppy))
  return [total/Double(n)*Double(ppy),st*an,st>0 ? avg/st*an : Double.nan,dv>0 ? avg/dv*an : Double.nan,mdd,wealth-1]
}}
'''
    if lang=='Kotlin':
        return f'''// {note}
import kotlin.math.*
fun {fn}(r:DoubleArray,rf:Double,ppy:Int):DoubleArray{{
  val n=r.size;require(n in 3..1000000 && rf.isFinite() && ppy in 1..1000000)
  var total=0.0;var ex=0.0;var wealth=1.0;var peak=1.0;var mdd=0.0;var down=0.0
  for(x in r){{require(x.isFinite() && x>(-1));total+=x;ex+=x-rf;val d=min(x-rf,0.0);down+=d*d;wealth*=1+x;peak=max(peak,wealth);mdd=min(mdd,wealth/peak-1)}}
  val avg=ex/n;var sq=0.0;for(x in r){{val e=x-rf-avg;sq+=e*e}}
  val st=sqrt(sq/(n-1));val dv=sqrt(down/n);val an=sqrt(ppy.toDouble())
  return doubleArrayOf(total/n*ppy,st*an,if(st>0)avg/st*an else Double.NaN,if(dv>0)avg/dv*an else Double.NaN,mdd,wealth-1)
}}
'''
    if lang=='Go':
        return f'''// {note}
package main
import "math"
func {fn}(r []float64,rf float64,ppy int)[]float64{{
  n:=len(r);if n<3||n>1000000||ppy<1||ppy>1000000||math.IsNaN(rf)||math.IsInf(rf,0){{return nil}}
  total,ex,wealth,peak,mdd,down:=0.0,0.0,1.0,1.0,0.0,0.0
  for _,x:=range r{{if math.IsNaN(x)||math.IsInf(x,0)||x<=-1{{return nil}};total+=x;ex+=x-rf;d:=math.Min(x-rf,0);down+=d*d;wealth*=1+x;peak=math.Max(peak,wealth);mdd=math.Min(mdd,wealth/peak-1)}}
  avg:=ex/float64(n);sq:=0.0;for _,x:=range r{{e:=x-rf-avg;sq+=e*e}}
  st:=math.Sqrt(sq/float64(n-1));dv:=math.Sqrt(down/float64(n));an:=math.Sqrt(float64(ppy));sh,so:=math.NaN(),math.NaN()
  if st>0{{sh=avg/st*an}};if dv>0{{so=avg/dv*an}}
  return []float64{{total/float64(n)*float64(ppy),st*an,sh,so,mdd,wealth-1}}
}}
'''
    if lang=='Rust':
        return f'''// {note}
pub fn {fn}(r:&[f64],rf:f64,ppy:usize)->[f64;6]{{
  let n=r.len();if n<3||n>1000000||ppy<1||ppy>1000000||!rf.is_finite(){{return [f64::NAN;6];}}
  let (mut total,mut ex,mut wealth,mut peak,mut mdd,mut down):(f64,f64,f64,f64,f64,f64)=(0.0,0.0,1.0,1.0,0.0,0.0);
  for &x in r{{if !x.is_finite()||x<=-1.0{{return [f64::NAN;6];}}total+=x;ex+=x-rf;let d=(x-rf).min(0.0);down+=d*d;wealth*=1.0+x;peak=peak.max(wealth);mdd=mdd.min(wealth/peak-1.0);}}
  let avg=ex/(n as f64);let mut sq=0.0;for &x in r{{let e=x-rf-avg;sq+=e*e;}}
  let st=(sq/((n-1) as f64)).sqrt();let dv=(down/(n as f64)).sqrt();let an=(ppy as f64).sqrt();
  [total/(n as f64)*(ppy as f64),st*an,if st>0.0{{avg/st*an}}else{{f64::NAN}},if dv>0.0{{avg/dv*an}}else{{f64::NAN}},mdd,wealth-1.0]
}}
'''
    if lang=='R':
        return f'''# {note}
{fn} <- function(r,rf,ppy){{
  if(length(r)<3||length(r)>1000000||any(!is.finite(r))||any(r<=-1)||length(rf)!=1||!is.finite(rf)||length(ppy)!=1||!is.finite(ppy)||ppy<1||ppy>1000000||ppy!=trunc(ppy))stop("Invalid returns")
  n<-length(r); ex<-r-rf;st<-sd(ex);dv<-sqrt(mean(pmin(ex,0)^2));wealth<-cumprod(c(1,1+r));peak<-cummax(wealth)
  return(c(AnnualMean=mean(r)*ppy,AnnualVol=st*sqrt(ppy),Sharpe=if(st>0)mean(ex)/st*sqrt(ppy) else NaN,Sortino=if(dv>0)mean(ex)/dv*sqrt(ppy) else NaN,MDD=min(wealth/peak-1),TotalReturn=tail(wealth,1)-1))
}}
'''
    if lang=='MATLAB':
        return f'''% {note}
function result={fn}(r,rf,ppy)
  r=r(:);n=numel(r);
  if n<3||n>1000000||any(~isfinite(r))||any(r<=-1)||~isscalar(rf)||~isfinite(rf)||~isscalar(ppy)||~isfinite(ppy)||ppy<1||ppy>1000000||ppy~=fix(ppy)
    error('Invalid performance inputs');
  end
  ex=r-rf;st=std(ex,0);dv=sqrt(mean(min(ex,0).^2));wealth=cumprod([1;1+r]);peak=cummax(wealth);sh=NaN;so=NaN;
  if st>0,sh=mean(ex)/st*sqrt(ppy);end
  if dv>0,so=mean(ex)/dv*sqrt(ppy);end
  result=[mean(r)*ppy,st*sqrt(ppy),sh,so,min(wealth./peak-1),wealth(end)-1];
end
'''
    if lang=='Julia':
        return f'''# {note}
using Statistics
function {fn}(r,rf,ppy)
  n=length(r)
  if n<3||n>1000000||!all(isfinite,r)||any(x->x<=-1,r)||!isfinite(rf)||ppy<1||ppy>1000000||ppy!=trunc(ppy)
    throw(ArgumentError("Invalid performance inputs"))
  end
  ex=r.-rf;st=std(ex);dv=sqrt(mean(min(x,0)^2 for x in ex));wealth=cumprod(vcat(1.0,1.0 .+r));peak=accumulate(max,wealth)
  return [mean(r)*ppy,st*sqrt(ppy),st>0 ? mean(ex)/st*sqrt(ppy) : NaN,dv>0 ? mean(ex)/dv*sqrt(ppy) : NaN,minimum(wealth./peak.-1),wealth[end]-1]
end
'''
    raise ValueError('Unknown language '+lang)
