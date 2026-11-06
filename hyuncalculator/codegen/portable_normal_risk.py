"""Portable signed-loss Gaussian VaR/ES with standard-library only.

Uses the Acklam inverse-normal rational approximation (absolute z error about
1.2e-9 in the core range). All runtimes share the same coefficients. The
accuracy is a deliberate approximation of scipy.stats.norm.ppf; output is
not certified for extreme 1e-16 tail risk or production regulatory use.
"""
from __future__ import annotations
from .emitter import GenerationError

SUPPORTED = frozenset({'qf_normal_var'})

_A = (-39.69683028665376, 220.9460984245205, -275.9285104469687,
      138.357751867269, -30.66479806614716, 2.506628277459239)
_B = (-54.47609879822406, 161.5858368580409, -155.6989798598866,
      66.80131188771972, -13.28068155288572)
_C = (-0.007784894002430293, -0.3223964580411365, -2.400758277161838,
      -2.549732539343734, 4.374664141464968, 2.938163982698783)
_D = (0.007784695709041462, 0.3224671290700398, 2.445134137142996,
      3.754408661907416)


def _horner(vals, x):
    out = repr(float(vals[0]))
    for v in vals[1:]:
        out = f'({out}*{x} + ({float(v)!r}))'
    return out


def _poly(x, central=False):
    if central:
        return f'({_horner(_A,x)}*q)/({_horner(tuple(_B)+(1.0,),x)})'
    return f'({_horner(_C,x)})/({_horner(tuple(_D)+(1.0,),x)})'

TAIL = _poly('q')
CENTER = _poly('z2',central=True)
NOTE = ('Normal signed-loss VaR/ES using Acklam rational inverse CDF; '
        'rates/vol as decimals, outputs VaR and ES. Approximation ~1e-9 in z.')


def generate_normal_risk(fn, formula, opt):
    if opt.language == 'Python':
        raise GenerationError('Python uses SciPy reference implementation')
    if opt.structure != 'function' or opt.iteration != 'auto' or opt.variable_names or opt.variant != 'periodic':
        raise GenerationError('Normal VaR uses function/auto and fixed parameters')
    l = opt.language
    # Tail polynomial is negative for lower tail, positive sign is explicitly inverted for upper tail.
    if l == 'R':
        return f'''# {NOTE}
{fn} <- function(mean,vol,confidence){{
  if(any(!is.finite(c(mean,vol,confidence)))||vol<0||confidence<=0||confidence>=1)stop("Invalid normal VaR inputs")
  if(confidence<0.02425){{q<-sqrt(-2*log(confidence));z<-{TAIL}}} else if(confidence>0.97575){{q<-sqrt(-2*log(1-confidence));z<- -({TAIL})}} else{{q<-confidence-0.5;z2<-q*q;z<-{CENTER}}}
  c(VaR=-mean+vol*z,ES=-mean+vol*exp(-0.5*z*z)/sqrt(2*pi)/(1-confidence))
}}
'''
    if l == 'MATLAB':
        return f'''% {NOTE}
function result = {fn}(mean,vol,confidence)
  if ~isscalar(mean) || ~isscalar(vol) || ~isscalar(confidence) || any(~isfinite([mean,vol,confidence])) || vol<0 || confidence<=0 || confidence>=1
    error('Invalid normal VaR inputs');
  end
  if confidence<0.02425
    q=sqrt(-2*log(confidence));z={TAIL};
  elseif confidence>0.97575
    q=sqrt(-2*log(1-confidence));z=-({TAIL});
  else
    q=confidence-0.5;z2=q*q;z={CENTER};
  end
  result=[-mean+vol*z,-mean+vol*exp(-0.5*z*z)/sqrt(2*pi)/(1-confidence)];
end
'''
    if l == 'Julia':
        return f'''# {NOTE}
function {fn}(mean,vol,confidence)
  if !all(isfinite,(mean,vol,confidence)) || vol<0 || confidence<=0 || confidence>=1
    throw(ArgumentError("Invalid normal VaR inputs"))
  end
  z=0.0
  if confidence<0.02425
    q=sqrt(-2*log(confidence));z={TAIL}
  elseif confidence>0.97575
    q=sqrt(-2*log(1-confidence));z=-({TAIL})
  else
    q=confidence-0.5;z2=q*q;z={CENTER}
  end
  return (VaR=-mean+vol*z,ES=-mean+vol*exp(-0.5*z*z)/sqrt(2*pi)/(1-confidence))
end
'''
    if l == 'C':
        return f'''/* {NOTE} */
#include <math.h>
typedef struct {{double values[2];}} HyunResult;
HyunResult {fn}(double mean,double vol,double confidence){{
  HyunResult bad={{{{NAN,NAN}}}};
  if(!isfinite(mean)||!isfinite(vol)||!isfinite(confidence)||vol<0||confidence<=0||confidence>=1)return bad;
  double z,q,z2;
  if(confidence<0.02425){{q=sqrt(-2*log(confidence));z={TAIL};}}
  else if(confidence>0.97575){{q=sqrt(-2*log(1-confidence));z=-({TAIL});}}
  else{{q=confidence-0.5;z2=q*q;z={CENTER};}}
  HyunResult out={{{{-mean+vol*z,-mean+vol*exp(-0.5*z*z)*0.39894228040143267794/(1-confidence)}}}};
  return out;
}}
'''
    if l == 'C++':
        return f'''// {NOTE}
#include <array>
#include <cmath>
#include <stdexcept>
std::array<double,2> {fn}(double mean,double vol,double confidence){{
  if(!std::isfinite(mean)||!std::isfinite(vol)||!std::isfinite(confidence)||vol<0||confidence<=0||confidence>=1)throw std::invalid_argument("Invalid normal VaR inputs");
  double z,q,z2;
  if(confidence<0.02425){{q=std::sqrt(-2*std::log(confidence));z={TAIL};}}
  else if(confidence>0.97575){{q=std::sqrt(-2*std::log(1-confidence));z=-({TAIL});}}
  else{{q=confidence-0.5;z2=q*q;z={CENTER};}}
  return {{-mean+vol*z,-mean+vol*std::exp(-0.5*z*z)*0.39894228040143267794/(1-confidence)}};
}}
'''
    if l in ('JavaScript','TypeScript'):
        params='mean: number,vol: number,confidence: number' if l=='TypeScript' else 'mean,vol,confidence'
        ret=': number[]' if l=='TypeScript' else ''
        return f'''// {NOTE}
export function {fn}({params}){ret}{{
  if(![mean,vol,confidence].every(Number.isFinite)||vol<0||confidence<=0||confidence>=1)throw new RangeError("Invalid normal VaR inputs");
  let z,q,z2;
  if(confidence<0.02425){{q=Math.sqrt(-2*Math.log(confidence));z={TAIL};}}
  else if(confidence>0.97575){{q=Math.sqrt(-2*Math.log(1-confidence));z=-({TAIL});}}
  else{{q=confidence-0.5;z2=q*q;z={CENTER};}}
  return [-mean+vol*z,-mean+vol*Math.exp(-0.5*z*z)*0.39894228040143267794/(1-confidence)];
}}
'''
    if l == 'Java':
        return f'''// {NOTE}
public class GeneratedCalculator{{
  public static double[] {fn}(double mean,double vol,double confidence){{
    if(!Double.isFinite(mean)||!Double.isFinite(vol)||!Double.isFinite(confidence)||vol<0||confidence<=0||confidence>=1)throw new IllegalArgumentException("Invalid normal VaR inputs");
    double z,q,z2;
    if(confidence<0.02425){{q=Math.sqrt(-2*Math.log(confidence));z={TAIL};}}
    else if(confidence>0.97575){{q=Math.sqrt(-2*Math.log(1-confidence));z=-({TAIL});}}
    else{{q=confidence-0.5;z2=q*q;z={CENTER};}}
    return new double[]{{-mean+vol*z,-mean+vol*Math.exp(-0.5*z*z)*0.39894228040143267794/(1-confidence)}};
  }}
}}
'''
    if l == 'C#':
        return f'''// {NOTE}
using System;
public static class GeneratedCalculator{{
  public static double[] {fn}(double mean,double vol,double confidence){{
    if(!double.IsFinite(mean)||!double.IsFinite(vol)||!double.IsFinite(confidence)||vol<0||confidence<=0||confidence>=1)throw new ArgumentException("Invalid normal VaR inputs");
    double z,q,z2;
    if(confidence<0.02425){{q=Math.Sqrt(-2*Math.Log(confidence));z={TAIL};}}
    else if(confidence>0.97575){{q=Math.Sqrt(-2*Math.Log(1-confidence));z=-({TAIL});}}
    else{{q=confidence-0.5;z2=q*q;z={CENTER};}}
    return new double[]{{-mean+vol*z,-mean+vol*Math.Exp(-0.5*z*z)*0.39894228040143267794/(1-confidence)}};
  }}
}}
'''
    if l == 'Swift':
        return f'''// {NOTE}
import Foundation
func {fn}(_ mean:Double,_ vol:Double,_ confidence:Double)->[Double]{{
  guard [mean,vol,confidence].allSatisfy({{$0.isFinite}}),vol>=0,confidence>0,confidence<1 else {{return [Double.nan,Double.nan]}}
  let z:Double
  if confidence<0.02425{{let q=sqrt(-2*log(confidence));z={TAIL}}} else if confidence>0.97575{{let q=sqrt(-2*log(1-confidence));z = -({TAIL})}} else{{let q=confidence-0.5;let z2=q*q;z={CENTER}}}
  return [-mean+vol*z,-mean+vol*exp(-0.5*z*z)*0.39894228040143267794/(1-confidence)]
}}
'''
    if l == 'Kotlin':
        return f'''// {NOTE}
import kotlin.math.*
fun {fn}(mean:Double,vol:Double,confidence:Double):DoubleArray{{
  require(listOf(mean,vol,confidence).all{{it.isFinite()}}&&vol>=0&&confidence>0&&confidence<1){{"Invalid normal VaR inputs"}}
  val z:Double
  if(confidence<0.02425){{val q=sqrt(-2*ln(confidence));z={TAIL}}}
  else if(confidence>0.97575){{val q=sqrt(-2*ln(1-confidence));z=-({TAIL})}} else{{val q=confidence-0.5;val z2=q*q;z={CENTER}}}
  return doubleArrayOf(-mean+vol*z,-mean+vol*exp(-0.5*z*z)*0.39894228040143267794/(1-confidence))
}}
'''
    if l == 'Go':
        return f'''// {NOTE}
package main
import "math"
func {fn}(mean,vol,confidence float64)[2]float64{{
  for _,v:=range []float64{{mean,vol,confidence}}{{if math.IsNaN(v)||math.IsInf(v,0){{return [2]float64{{math.NaN(),math.NaN()}}}}}}
  if vol<0||confidence<=0||confidence>=1{{return [2]float64{{math.NaN(),math.NaN()}}}}
  var z float64
  if confidence<0.02425{{q:=math.Sqrt(-2*math.Log(confidence));z={TAIL}}} else if confidence>0.97575{{q:=math.Sqrt(-2*math.Log(1-confidence));z=-({TAIL})}} else{{q:=confidence-0.5;z2:=q*q;z={CENTER}}}
  return [2]float64{{-mean+vol*z,-mean+vol*math.Exp(-0.5*z*z)*0.39894228040143267794/(1-confidence)}}
}}
'''
    if l == 'Rust':
        return f'''// {NOTE}
pub fn {fn}(mean:f64,vol:f64,confidence:f64)->[f64;2]{{
  if ![mean,vol,confidence].iter().all(|x|x.is_finite())||vol<0.0||confidence<=0.0||confidence>=1.0{{return [f64::NAN;2];}}
  let z:f64;
  if confidence<0.02425{{let q=(-2.0*confidence.ln()).sqrt();z={TAIL};}}
  else if confidence>0.97575{{let q=(-2.0*(1.0-confidence).ln()).sqrt();z=-({TAIL});}}
  else{{let q=confidence-0.5;let z2=q*q;z={CENTER};}}
  [-mean+vol*z,-mean+vol*(-0.5*z*z).exp()*0.39894228040143267794/(1.0-confidence)]
}}
'''
    raise GenerationError(f'Unsupported normal VaR language: {l}')
