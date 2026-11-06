"""Standalone 13-language historical VaR/ES code emitter.

Matches quant.historical_var_es: type-7 linear quantile of signed losses,
then inclusive empirical tail with 1e-12 comparison slack. No arbitrary code
execution or raw user expressions are embedded into generated source.
"""
from __future__ import annotations

from .emitter import GenerationError

SUPPORTED = frozenset({'qf_hist_var'})


def generate_risk(fn: str, formula, options) -> str:
    if options.language == 'Python':
        raise GenerationError('Python uses full reference implementation')
    if options.structure != 'function' or options.iteration != 'auto' or options.variable_names:
        raise GenerationError('Historical VaR uses function/auto and fixed parameter names')
    if options.variant != 'periodic':
        raise GenerationError('Variant applies only to Future Value')
    lang = options.language
    note = 'Historical VaR/ES: losses=-returns; type-7 linear quantile; tail includes losses >= VaR-1e-12. Result [VaR, ES].'
    if lang == 'R':
        return f'''# {note}
{fn} <- function(r, confidence) {{
  if(length(r)<3 || any(!is.finite(r)) || length(confidence)!=1 || !is.finite(confidence) || confidence<=0 || confidence>=1) stop("Invalid VaR inputs")
  losses <- sort(-r)
  h <- (length(r)-1)*confidence
  lo <- floor(h)+1; hi <- ceiling(h)+1
  cutoff <- losses[lo] + (h-floor(h))*(losses[hi]-losses[lo])
  tail <- losses[losses >= cutoff-1e-12]
  c(VaR=cutoff, ES=mean(tail))
}}
'''
    if lang == 'MATLAB':
        return f'''% {note}
function result = {fn}(r,confidence)
    if numel(r)<3 || any(~isfinite(r)) || ~isscalar(confidence) || ~isfinite(confidence) || confidence<=0 || confidence>=1
        error('Invalid VaR inputs');
    end
    losses = sort(-r(:));
    h = (numel(losses)-1)*confidence;
    lo=floor(h)+1; hi=ceil(h)+1;
    cutoff=losses(lo)+(h-floor(h))*(losses(hi)-losses(lo));
    tail=losses(losses>=cutoff-1e-12);
    result=[cutoff,mean(tail)];
end
'''
    if lang == 'Julia':
        return f'''# {note}
function {fn}(r, confidence)
    if length(r)<3 || !all(isfinite,r) || !isfinite(confidence) || confidence<=0 || confidence>=1
        throw(ArgumentError("Invalid VaR inputs"))
    end
    losses=sort(-collect(r)); h=(length(losses)-1)*confidence
    lo=floor(Int,h)+1; hi=ceil(Int,h)+1
    cutoff=losses[lo]+(h-floor(h))*(losses[hi]-losses[lo])
    tail=filter(x -> x>=cutoff-1e-12,losses)
    return (VaR=cutoff, ES=sum(tail)/length(tail))
end
'''
    if lang == 'C':
        return f'''/* {note} */
#include <math.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
typedef struct {{ double values[2]; }} HyunResult;
static int hyun_compare_double(const void *a,const void *b) {{
  const double x=*(const double*)a,y=*(const double*)b;
  return (x>y)-(x<y);
}}
HyunResult {fn}(const double *r,size_t count,double confidence) {{
  HyunResult invalid={{{{NAN,NAN}}}};
  if (!r || count<3 || count>10000000 || !isfinite(confidence) || confidence<=0 || confidence>=1) return invalid;
  double *losses=(double*)malloc(count*sizeof(double)); if(!losses) return invalid;
  for(size_t i=0;i<count;i++){{if(!isfinite(r[i])){{free(losses);return invalid;}}losses[i]=-r[i];}}
  qsort(losses,count,sizeof(double),hyun_compare_double);
  double h=(count-1)*confidence;size_t lo=(size_t)floor(h),hi=(size_t)ceil(h);
  double cutoff=losses[lo]+(h-floor(h))*(losses[hi]-losses[lo]);
  double total=0;size_t n_tail=0;
  for(size_t i=0;i<count;i++){{if(losses[i]>=cutoff-1e-12){{total+=losses[i];n_tail++;}}}}
  free(losses);
  HyunResult out={{{{cutoff,total/n_tail}}}};return out;
}}
'''
    if lang == 'C++':
        return f'''// {note}
#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>
#include <vector>
std::array<double,2> {fn}(const std::vector<double>& r,double confidence) {{
  if(r.size()<3 || !std::isfinite(confidence) || confidence<=0 || confidence>=1) throw std::invalid_argument("Invalid VaR inputs");
  std::vector<double> losses;losses.reserve(r.size());
  for(double x:r){{if(!std::isfinite(x))throw std::invalid_argument("Nonfinite return");losses.push_back(-x);}}
  std::sort(losses.begin(),losses.end());
  double h=(losses.size()-1)*confidence;size_t lo=(size_t)std::floor(h),hi=(size_t)std::ceil(h);
  double cutoff=losses[lo]+(h-std::floor(h))*(losses[hi]-losses[lo]);
  double total=0;size_t n_tail=0;
  for(double x:losses)if(x>=cutoff-1e-12){{total+=x;n_tail++;}}
  return {{cutoff,total/n_tail}};
}}
'''
    if lang in ('JavaScript','TypeScript'):
        p='r: number[], confidence: number' if lang=='TypeScript' else 'r, confidence'
        ret=': number[]' if lang=='TypeScript' else ''
        return f'''// {note}
export function {fn}({p}){ret} {{
  if(!Array.isArray(r)||r.length<3||!r.every(Number.isFinite)||!Number.isFinite(confidence)||confidence<=0||confidence>=1) throw new RangeError("Invalid VaR inputs");
  const losses=r.map(x=>-x).sort((a,b)=>a-b);
  const h=(losses.length-1)*confidence,lo=Math.floor(h),hi=Math.ceil(h);
  const cutoff=losses[lo]+(h-lo)*(losses[hi]-losses[lo]);
  const tail=losses.filter(x=>x>=cutoff-1e-12);
  return [cutoff,tail.reduce((a,b)=>a+b,0)/tail.length];
}}
'''
    if lang == 'Java':
        return f'''// {note}
import java.util.Arrays;
public class GeneratedCalculator {{
  public static double[] {fn}(double[] r,double confidence) {{
    if(r==null||r.length<3||!Double.isFinite(confidence)||confidence<=0||confidence>=1)throw new IllegalArgumentException("Invalid VaR inputs");
    double[] losses=new double[r.length];
    for(int i=0;i<r.length;i++){{if(!Double.isFinite(r[i]))throw new IllegalArgumentException("Nonfinite return");losses[i]=-r[i];}}
    Arrays.sort(losses);
    double h=(losses.length-1)*confidence;int lo=(int)Math.floor(h),hi=(int)Math.ceil(h);
    double cutoff=losses[lo]+(h-lo)*(losses[hi]-losses[lo]);
    double total=0;int n_tail=0;
    for(double x:losses)if(x>=cutoff-1e-12){{total+=x;n_tail++;}}
    return new double[]{{cutoff,total/n_tail}};
  }}
}}
'''
    if lang == 'C#':
        return f'''// {note}
using System;
public static class GeneratedCalculator {{
  public static double[] {fn}(double[] r,double confidence) {{
    if(r==null||r.Length<3||!double.IsFinite(confidence)||confidence<=0||confidence>=1)throw new ArgumentException("Invalid VaR inputs");
    var losses=new double[r.Length];
    for(int i=0;i<r.Length;i++){{if(!double.IsFinite(r[i]))throw new ArgumentException("Nonfinite return");losses[i]=-r[i];}}
    Array.Sort(losses);
    double h=(losses.Length-1)*confidence;int lo=(int)Math.Floor(h),hi=(int)Math.Ceiling(h);
    double cutoff=losses[lo]+(h-lo)*(losses[hi]-losses[lo]);
    double total=0;int n_tail=0;
    foreach(double x in losses)if(x>=cutoff-1e-12){{total+=x;n_tail++;}}
    return new double[]{{cutoff,total/n_tail}};
  }}
}}
'''
    if lang == 'Swift':
        return f'''// {note}
import Foundation
func {fn}(_ r:[Double],_ confidence:Double)->[Double] {{
  guard r.count>=3,r.allSatisfy({{$0.isFinite}}),confidence.isFinite,confidence>0,confidence<1 else {{return [Double.nan,Double.nan]}}
  let losses=r.map{{-$0}}.sorted()
  let h=Double(losses.count-1)*confidence,lo=Int(floor(h)),hi=Int(ceil(h))
  let cutoff=losses[lo]+(h-floor(h))*(losses[hi]-losses[lo])
  let tail=losses.filter{{$0>=cutoff-1e-12}}
  return [cutoff,tail.reduce(0,+)/Double(tail.count)]
}}
'''
    if lang == 'Kotlin':
        return f'''// {note}
import kotlin.math.*
fun {fn}(r:DoubleArray,confidence:Double):DoubleArray {{
  require(r.size>=3&&r.all{{it.isFinite()}}&&confidence.isFinite()&&confidence>0&&confidence<1){{"Invalid VaR inputs"}}
  val losses=r.map{{-it}}.sorted()
  val h=(losses.size-1)*confidence
  val lo=floor(h).toInt();val hi=ceil(h).toInt()
  val cutoff=losses[lo]+(h-floor(h))*(losses[hi]-losses[lo])
  val tail=losses.filter{{it>=cutoff-1e-12}}
  return doubleArrayOf(cutoff,tail.sum()/tail.size)
}}
'''
    if lang == 'Go':
        return f'''// {note}
package main
import ("math";"sort")
func {fn}(r []float64,confidence float64)[2]float64{{
  fail:=[2]float64{{math.NaN(),math.NaN()}}
  if len(r)<3||math.IsNaN(confidence)||math.IsInf(confidence,0)||confidence<=0||confidence>=1{{return fail}}
  losses:=make([]float64,len(r))
  for i,x:=range r{{if math.IsNaN(x)||math.IsInf(x,0){{return fail}};losses[i]=-x}}
  sort.Float64s(losses)
  h:=float64(len(losses)-1)*confidence;lo:=int(math.Floor(h));hi:=int(math.Ceil(h))
  cutoff:=losses[lo]+(h-math.Floor(h))*(losses[hi]-losses[lo])
  total:=0.0;nTail:=0
  for _,x:=range losses{{if x>=cutoff-1e-12{{total+=x;nTail++}}}}
  return [2]float64{{cutoff,total/float64(nTail)}}
}}
'''
    if lang == 'Rust':
        return f'''// {note}
pub fn {fn}(r:&[f64],confidence:f64)->[f64;2]{{
  let fail=[f64::NAN;2];
  if r.len()<3||!confidence.is_finite()||confidence<=0.0||confidence>=1.0||!r.iter().all(|x|x.is_finite()){{return fail;}}
  let mut losses:Vec<f64>=r.iter().map(|x|-x).collect();
  losses.sort_by(|a,b|a.total_cmp(b));
  let h=(losses.len()-1) as f64*confidence;let lo=h.floor() as usize;let hi=h.ceil() as usize;
  let cutoff=losses[lo]+(h-h.floor())*(losses[hi]-losses[lo]);
  let mut total=0.0;let mut n_tail=0usize;
  for x in losses{{if x>=cutoff-1e-12{{total+=x;n_tail+=1;}}}}
  [cutoff,total/n_tail as f64]
}}
'''
    raise GenerationError(f'{lang}: no historical VaR code emitter')
