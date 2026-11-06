"""Auditable, standalone financial loop emitters for fixed-coupon bonds and EWMA.

The 13 non-Python language profiles use an explicit domain algorithm. No
runtime code substitution or executing user-provided expressions is involved.
The result arrays preserve the order of the v1.1.0 dictionary outputs.
"""
from __future__ import annotations

from .emitter import GenerationError

SUPPORTED = frozenset({'qf_bond', 'qf_ewma'})


def _bond(lang: str, fn: str) -> str:
    """Fixed-coupon dirty price, Macaulay/modified duration, convexity.

    Inputs: face, coupon (annual decimal), yield_rate (annual nominal decimal),
    years, freq (integer payments per year). Output order: [price, Macaulay,
    modified duration, convexity] exactly as quant.bond_metrics.
    """
    if lang == 'R':
        return f'''# HyunCalculator BOND-001; result order: Price, Macaulay, Modified, Convexity
{fn} <- function(face, coupon, yield_rate, years, freq) {{
  if (any(!is.finite(c(face,coupon,yield_rate,years,freq))) || face <= 0 || years <= 0 || freq < 1 || freq != trunc(freq) || yield_rate/freq <= -1) stop("Invalid bond inputs")
  periods <- years * freq
  if (abs(periods - round(periods)) > 1e-8 || periods < 1) stop("Coupon periods must be a positive integer")
  n <- as.integer(round(periods)); y <- yield_rate/freq
  price <- 0; weighted <- 0; curved <- 0
  for (i in seq_len(n)) {{
    cash <- face*coupon/freq + if (i == n) face else 0
    pv <- cash/(1+y)^i
    price <- price + pv; weighted <- weighted + i*pv; curved <- curved + i*(i+1)*pv
  }}
  if (!is.finite(price) || price == 0) stop("Undefined bond sensitivity")
  macaulay <- weighted/price/freq
  return(c(Price=price, Macaulay=macaulay, Modified=macaulay/(1+y), Convexity=curved/(price*freq^2*(1+y)^2)))
}}
'''
    if lang == 'MATLAB':
        return f'''% HyunCalculator BOND-001; order [price,macaulay,modified,convexity]
function result = {fn}(face,coupon,yield_rate,years,freq)
    if any(~isfinite([face,coupon,yield_rate,years,freq])) || face <= 0 || years <= 0 || freq < 1 || freq ~= fix(freq) || yield_rate/freq <= -1
        error('Invalid bond inputs');
    end
    periods = years * freq;
    if abs(periods - round(periods)) > 1e-8 || periods < 1
        error('Invalid coupon periods');
    end
    n = round(periods); y = yield_rate/freq;
    price = 0; weighted = 0; curved = 0;
    for i = 1:n
        cash = face*coupon/freq;
        if i == n
            cash = cash + face;
        end
        pv = cash/(1+y)^i;
        price = price + pv;
        weighted = weighted + i*pv;
        curved = curved + i*(i+1)*pv;
    end
    if ~isfinite(price) || price == 0
        error('Undefined sensitivity');
    end
    mac = weighted/price/freq;
    result = [price,mac,mac/(1+y),curved/(price*freq^2*(1+y)^2)];
end
'''
    if lang == 'Julia':
        return f'''# HyunCalculator BOND-001; named tuple outputs
function {fn}(face,coupon,yield_rate,years,freq)
    if !all(isfinite, (face,coupon,yield_rate,years,freq)) || face <= 0 || years <= 0 || freq < 1 || freq != trunc(freq) || yield_rate/freq <= -1
        throw(ArgumentError("Invalid bond inputs"))
    end
    periods = years*freq
    if abs(periods-round(periods)) > 1e-8 || periods < 1
        throw(ArgumentError("Invalid periods"))
    end
    n = Int(round(periods)); y = yield_rate/freq
    price=0.0; weighted=0.0; curved=0.0
    for i in 1:n
        cash = face*coupon/freq + (i == n ? face : 0)
        pv = cash/(1+y)^i
        price += pv; weighted += i*pv; curved += i*(i+1)*pv
    end
    if !isfinite(price) || price == 0; throw(ArgumentError("Invalid sensitivity")); end
    mac=weighted/price/freq
    return (Price=price, Macaulay=mac, Modified=mac/(1+y), Convexity=curved/(price*freq^2*(1+y)^2))
end
'''
    # Output order is explicit for languages with tuple/array return types.
    pre = '// HyunCalculator BOND-001 result order: [Price, Macaulay, Modified, Convexity]\n'
    if lang == 'C':
        return pre+f'''#include <math.h>
#include <stddef.h>
typedef struct {{ double values[4]; }} HyunResult;
HyunResult {fn}(double face, double coupon, double yield_rate, double years, int freq) {{
    HyunResult fail = {{{{NAN,NAN,NAN,NAN}}}};
    if (!isfinite(face) || !isfinite(coupon) || !isfinite(yield_rate) || !isfinite(years) || face<=0 || years<=0 || freq<1 || yield_rate/freq<=-1) return fail;
    double periods=years*freq;
    if (!isfinite(periods) || periods<1 || fabs(periods-round(periods))>1e-8 || periods>1000000) return fail;
    int n=(int)round(periods); double y=yield_rate/freq;
    double price=0, weighted=0, curved=0;
    for (int i=1;i<=n;i++) {{
        double cash=face*coupon/freq+(i==n?face:0);
        double pv=cash/pow(1+y,i);
        price+=pv; weighted+=i*pv; curved+=i*(i+1.0)*pv;
    }}
    if (!isfinite(price) || price==0) return fail;
    double mac=weighted/price/freq;
    HyunResult result = {{{{price, mac, mac/(1+y), curved/(price*freq*freq*pow(1+y,2))}}}};
    return result;
}}
'''
    if lang == 'C++':
        return pre+f'''#include <array>
#include <cmath>
#include <stdexcept>
std::array<double,4> {fn}(double face, double coupon, double yield_rate, double years, int freq) {{
    if (!std::isfinite(face)||!std::isfinite(coupon)||!std::isfinite(yield_rate)||!std::isfinite(years)||face<=0||years<=0||freq<1||yield_rate/freq<=-1) throw std::invalid_argument("Invalid bond inputs");
    double periods=years*freq;
    if (!std::isfinite(periods)||periods<1||std::fabs(periods-std::round(periods))>1e-8||periods>1000000) throw std::invalid_argument("Invalid periods");
    int n=(int)std::round(periods); double y=yield_rate/freq;
    double price=0, weighted=0, curved=0;
    for (int i=1;i<=n;i++) {{
        double cash=face*coupon/freq+(i==n?face:0), pv=cash/std::pow(1+y,i);
        price+=pv; weighted+=i*pv; curved+=i*(i+1.0)*pv;
    }}
    if (!std::isfinite(price)||price==0) throw std::invalid_argument("Invalid sensitivity");
    double mac=weighted/price/freq;
    return {{price,mac,mac/(1+y),curved/(price*freq*freq*std::pow(1+y,2))}};
}}
'''
    if lang in ('JavaScript','TypeScript'):
        typed = ': number' if lang=='TypeScript' else ''
        ps=', '.join(name+typed for name in ('face','coupon','yield_rate','years','freq'))
        ret=': number[]' if lang=='TypeScript' else ''
        return pre+f'''export function {fn}({ps}){ret} {{
  if (![face,coupon,yield_rate,years,freq].every(Number.isFinite) || face<=0 || years<=0 || !Number.isInteger(freq) || freq<1 || yield_rate/freq<=-1) throw new RangeError("Invalid bond inputs");
  const periods=years*freq;
  if (!Number.isFinite(periods)||periods<1||Math.abs(periods-Math.round(periods))>1e-8||periods>1000000) throw new RangeError("Invalid coupon periods");
  const n=Math.round(periods), y=yield_rate/freq;
  let price=0, weighted=0, curved=0;
  for(let i=1;i<=n;i++) {{
    const cash=face*coupon/freq+(i===n?face:0), pv=cash/Math.pow(1+y,i);
    price+=pv; weighted+=i*pv; curved+=i*(i+1)*pv;
  }}
  if(!Number.isFinite(price)||price===0) throw new RangeError("Invalid sensitivity");
  const mac=weighted/price/freq;
  return [price,mac,mac/(1+y),curved/(price*freq*freq*Math.pow(1+y,2))];
}}
'''
    if lang == 'Java':
        return pre+f'''public class GeneratedCalculator {{
  public static double[] {fn}(double face,double coupon,double yield_rate,double years,int freq) {{
    if(!Double.isFinite(face)||!Double.isFinite(coupon)||!Double.isFinite(yield_rate)||!Double.isFinite(years)||face<=0||years<=0||freq<1||yield_rate/freq<=-1) throw new IllegalArgumentException("Invalid bond inputs");
    double periods=years*freq;
    if(!Double.isFinite(periods)||periods<1||Math.abs(periods-Math.rint(periods))>1e-8||periods>1000000) throw new IllegalArgumentException("Invalid periods");
    int n=(int)Math.rint(periods); double y=yield_rate/freq;
    double price=0,weighted=0,curved=0;
    for(int i=1;i<=n;i++) {{
      double cash=face*coupon/freq+(i==n?face:0), pv=cash/Math.pow(1+y,i);
      price+=pv;weighted+=i*pv;curved+=i*(i+1.0)*pv;
    }}
    if(!Double.isFinite(price)||price==0) throw new IllegalArgumentException("Invalid sensitivity");
    double mac=weighted/price/freq;
    return new double[]{{price,mac,mac/(1+y),curved/(price*freq*freq*Math.pow(1+y,2))}};
  }}
}}
'''
    if lang == 'C#':
        return pre+f'''using System;
public static class GeneratedCalculator {{
  public static double[] {fn}(double face,double coupon,double yield_rate,double years,int freq) {{
    if(!double.IsFinite(face)||!double.IsFinite(coupon)||!double.IsFinite(yield_rate)||!double.IsFinite(years)||face<=0||years<=0||freq<1||yield_rate/freq<=-1) throw new ArgumentOutOfRangeException("Invalid bond inputs");
    double periods=years*freq;
    if(!double.IsFinite(periods)||periods<1||Math.Abs(periods-Math.Round(periods))>1e-8||periods>1000000) throw new ArgumentOutOfRangeException("Invalid periods");
    int n=(int)Math.Round(periods); double y=yield_rate/freq;
    double price=0,weighted=0,curved=0;
    for(int i=1;i<=n;i++) {{
      double cash=face*coupon/freq+(i==n?face:0), pv=cash/Math.Pow(1+y,i);
      price+=pv;weighted+=i*pv;curved+=i*(i+1.0)*pv;
    }}
    if(!double.IsFinite(price)||price==0) throw new ArgumentOutOfRangeException("Invalid sensitivity");
    double mac=weighted/price/freq;
    return new double[]{{price,mac,mac/(1+y),curved/(price*freq*freq*Math.Pow(1+y,2))}};
  }}
}}
'''
    if lang == 'Swift':
        return pre+f'''import Foundation
func {fn}(_ face: Double,_ coupon: Double,_ yield_rate: Double,_ years: Double,_ freq: Int) -> [Double] {{
  guard [face,coupon,yield_rate,years].allSatisfy({{ $0.isFinite }}), face>0, years>0, freq>0, yield_rate/Double(freq) > -1 else {{return Array(repeating: Double.nan,count:4)}}
  let f=Double(freq), periods=years*f
  guard periods.isFinite, periods>=1, abs(periods.rounded()-periods)<=1e-8, periods<=1000000 else {{return Array(repeating: Double.nan,count:4)}}
  let n=Int(periods.rounded()), y=yield_rate/f
  var price=0.0, weighted=0.0, curved=0.0
  for i in 1...n {{
    let t=Double(i), pv=(face*coupon/f+(i==n ? face:0))/pow(1+y,t)
    price+=pv;weighted+=t*pv;curved+=t*(t+1)*pv
  }}
  guard price.isFinite,price != 0 else {{return Array(repeating: Double.nan,count:4)}}
  let mac=weighted/price/f
  return [price,mac,mac/(1+y),curved/(price*f*f*pow(1+y,2))]
}}
'''
    if lang == 'Kotlin':
        return pre+f'''import kotlin.math.*
fun {fn}(face:Double,coupon:Double,yield_rate:Double,years:Double,freq:Int): DoubleArray {{
  require(listOf(face,coupon,yield_rate,years).all{{it.isFinite()}} && face>0 && years>0 && freq>0 && yield_rate/freq>-1){{"Invalid bond inputs"}}
  val f=freq.toDouble(); val periods=years*f
  require(periods.isFinite() && periods>=1 && abs(periods-round(periods))<=1e-8 && periods<=1000000){{"Invalid periods"}}
  val n=round(periods).toInt(); val y=yield_rate/f
  var price=0.0;var weighted=0.0;var curved=0.0
  for(i in 1..n) {{
    val t=i.toDouble(); val cash=face*coupon/f+(if(i==n)face else 0.0)
    val pv=cash/(1+y).pow(t)
    price+=pv;weighted+=t*pv;curved+=t*(t+1)*pv
  }}
  require(price.isFinite() && price!=0.0){{"Invalid sensitivity"}}
  val mac=weighted/price/f
  return doubleArrayOf(price,mac,mac/(1+y),curved/(price*f*f*(1+y).pow(2)))
}}
'''
    if lang == 'Go':
        return pre+f'''package main
import "math"
func {fn}(face,coupon,yield_rate,years float64,freq int) [4]float64 {{
  fail:=[4]float64{{math.NaN(),math.NaN(),math.NaN(),math.NaN()}}
  if math.IsNaN(face)||math.IsNaN(coupon)||math.IsNaN(yield_rate)||math.IsNaN(years)||math.IsInf(face,0)||math.IsInf(coupon,0)||math.IsInf(yield_rate,0)||math.IsInf(years,0)||face<=0||years<=0||freq<1 {{return fail}}
  f:=float64(freq);if yield_rate/f<=-1 {{return fail}}
  periods:=years*f
  if math.IsNaN(periods)||math.IsInf(periods,0)||periods<1||math.Abs(periods-math.Round(periods))>1e-8||periods>1000000 {{return fail}}
  n:=int(math.Round(periods));y:=yield_rate/f
  price,weighted,curved:=0.0,0.0,0.0
  for i:=1;i<=n;i++ {{
    t:=float64(i);cash:=face*coupon/f;if i==n {{cash+=face}}
    pv:=cash/math.Pow(1+y,t)
    price+=pv;weighted+=t*pv;curved+=t*(t+1)*pv
  }}
  if math.IsNaN(price)||math.IsInf(price,0)||price==0 {{return fail}}
  mac:=weighted/price/f
  return [4]float64{{price,mac,mac/(1+y),curved/(price*f*f*math.Pow(1+y,2))}}
}}
'''
    if lang == 'Rust':
        return pre+f'''pub fn {fn}(face:f64,coupon:f64,yield_rate:f64,years:f64,freq:i32)->[f64;4]{{
  let fail=[f64::NAN;4];
  if !face.is_finite()||!coupon.is_finite()||!yield_rate.is_finite()||!years.is_finite()||face<=0.0||years<=0.0||freq<1 {{return fail;}}
  let f=freq as f64;if yield_rate/f<=-1.0 {{return fail;}}
  let periods=years*f;
  if !periods.is_finite()||periods<1.0||(periods-periods.round()).abs()>1e-8||periods>1000000.0 {{return fail;}}
  let n=periods.round() as i32;let y=yield_rate/f;
  let(mut price,mut weighted,mut curved)=(0.0,0.0,0.0);
  for i in 1..=n {{
    let t=i as f64;let cash=face*coupon/f+if i==n{{face}}else{{0.0}};
    let pv=cash/(1.0+y).powf(t);
    price+=pv;weighted+=t*pv;curved+=t*(t+1.0)*pv;
  }}
  if !price.is_finite()||price==0.0 {{return fail;}}
  let mac=weighted/price/f;
  [price,mac,mac/(1.0+y),curved/(price*f*f*(1.0+y).powi(2))]
}}
'''
    raise GenerationError(f'{lang}: no BOND-001 emitter')


def _ewma(lang: str, fn: str) -> str:
    """Return [EWMA variance, volatility], with initial r[0]**2."""
    if lang=='R':
        return f'''# HyunCalculator TS-001; [EWMA variance, EWMA volatility]
{fn} <- function(r, decay) {{
  if (length(r)<2 || any(!is.finite(r)) || !is.finite(decay) || decay<0 || decay>=1) stop("Invalid EWMA inputs")
  variance <- r[1]^2
  for (i in 2:length(r)) variance <- decay*variance+(1-decay)*r[i]^2
  return(c(Variance=variance, Volatility=sqrt(variance)))
}}
'''
    if lang=='MATLAB':
        return f'''% HyunCalculator TS-001; [variance, volatility]
function result = {fn}(r,decay)
    if numel(r)<2 || any(~isfinite(r)) || ~isscalar(decay) || ~isfinite(decay) || decay<0 || decay>=1
        error('Invalid EWMA inputs');
    end
    variance = r(1)^2;
    for i=2:numel(r)
        variance=decay*variance+(1-decay)*r(i)^2;
    end
    result=[variance,sqrt(variance)];
end
'''
    if lang=='Julia':
        return f'''# HyunCalculator TS-001; [variance, volatility]
function {fn}(r,decay)
    if length(r)<2 || !all(isfinite,r) || !isfinite(decay) || decay<0 || decay>=1
        throw(ArgumentError("Invalid EWMA inputs"))
    end
    variance = r[1]^2
    for i in 2:length(r)
        variance=decay*variance+(1-decay)*r[i]^2
    end
    return (Variance=variance, Volatility=sqrt(variance))
end
'''
    pre='// HyunCalculator TS-001 result order: [EWMA variance, EWMA volatility]\n'
    if lang=='C':
        return pre+f'''#include <math.h>
#include <stddef.h>
typedef struct {{ double values[2]; }} HyunResult;
HyunResult {fn}(const double* r,size_t count,double decay) {{
    HyunResult fail={{{{NAN,NAN}}}};
    if (!r||count<2||!isfinite(decay)||decay<0||decay>=1) return fail;
    for (size_t i=0;i<count;i++) if(!isfinite(r[i])) return fail;
    double v=r[0]*r[0];
    for(size_t i=1;i<count;i++) v=decay*v+(1-decay)*r[i]*r[i];
    HyunResult result={{{{v,sqrt(v)}}}};return result;
}}
'''
    if lang=='C++':
        return pre+f'''#include <vector>
#include <array>
#include <cmath>
#include <stdexcept>
std::array<double,2> {fn}(const std::vector<double>& r,double decay) {{
    if (r.size()<2||!std::isfinite(decay)||decay<0||decay>=1) throw std::invalid_argument("Invalid EWMA inputs");
    for(double x:r) if(!std::isfinite(x)) throw std::invalid_argument("Invalid return");
    double v=r[0]*r[0];
    for(size_t i=1;i<r.size();i++) v=decay*v+(1-decay)*r[i]*r[i];
    return {{v,std::sqrt(v)}};
}}
'''
    if lang in ('JavaScript','TypeScript'):
        pars='r: number[], decay: number' if lang=='TypeScript' else 'r, decay'
        ret=': number[]' if lang=='TypeScript' else ''
        return pre+f'''export function {fn}({pars}){ret} {{
  if(!Array.isArray(r)||r.length<2||!r.every(Number.isFinite)||!Number.isFinite(decay)||decay<0||decay>=1) throw new RangeError("Invalid EWMA inputs");
  let v=r[0]*r[0];
  for(let i=1;i<r.length;i++) v=decay*v+(1-decay)*r[i]*r[i];
  return [v,Math.sqrt(v)];
}}
'''
    if lang=='Java':
        return pre+f'''public class GeneratedCalculator {{
  public static double[] {fn}(double[] r,double decay) {{
    if(r==null||r.length<2||!Double.isFinite(decay)||decay<0||decay>=1) throw new IllegalArgumentException("Invalid EWMA inputs");
    for(double x:r) if(!Double.isFinite(x)) throw new IllegalArgumentException("Invalid returns");
    double v=r[0]*r[0];
    for(int i=1;i<r.length;i++) v=decay*v+(1-decay)*r[i]*r[i];
    return new double[]{{v,Math.sqrt(v)}};
  }}
}}
'''
    if lang=='C#':
        return pre+f'''using System;
public static class GeneratedCalculator {{
  public static double[] {fn}(double[] r,double decay) {{
    if(r==null||r.Length<2||!double.IsFinite(decay)||decay<0||decay>=1) throw new ArgumentException("Invalid EWMA inputs");
    foreach(double x in r) if(!double.IsFinite(x)) throw new ArgumentException("Invalid returns");
    double v=r[0]*r[0];
    for(int i=1;i<r.Length;i++) v=decay*v+(1-decay)*r[i]*r[i];
    return new double[]{{v,Math.Sqrt(v)}};
  }}
}}
'''
    if lang=='Swift':
        return pre+f'''import Foundation
func {fn}(_ r:[Double],_ decay:Double)->[Double] {{
  guard r.count>=2,r.allSatisfy({{$0.isFinite}}),decay.isFinite,decay>=0,decay<1 else {{return [Double.nan,Double.nan]}}
  var v=r[0]*r[0]
  for i in 1..<r.count {{v=decay*v+(1-decay)*r[i]*r[i]}}
  return [v,sqrt(v)]
}}
'''
    if lang=='Kotlin':
        return pre+f'''import kotlin.math.*
fun {fn}(r:DoubleArray,decay:Double):DoubleArray {{
  require(r.size>=2&&r.all{{it.isFinite()}}&&decay.isFinite()&&decay>=0&&decay<1){{"Invalid EWMA inputs"}}
  var v=r[0]*r[0]
  for(i in 1 until r.size) v=decay*v+(1-decay)*r[i]*r[i]
  return doubleArrayOf(v,sqrt(v))
}}
'''
    if lang=='Go':
        return pre+f'''package main
import "math"
func {fn}(r []float64,decay float64)[2]float64{{
  fail:=[2]float64{{math.NaN(),math.NaN()}}
  if len(r)<2||math.IsNaN(decay)||math.IsInf(decay,0)||decay<0||decay>=1 {{return fail}}
  for _,x:=range r {{if math.IsNaN(x)||math.IsInf(x,0){{return fail}}}}
  v:=r[0]*r[0]
  for i:=1;i<len(r);i++ {{v=decay*v+(1-decay)*r[i]*r[i]}}
  return [2]float64{{v,math.Sqrt(v)}}
}}
'''
    if lang=='Rust':
        return pre+f'''pub fn {fn}(r:&[f64],decay:f64)->[f64;2]{{
  let fail=[f64::NAN;2];
  if r.len()<2||!decay.is_finite()||decay<0.0||decay>=1.0||!r.iter().all(|x|x.is_finite()){{return fail;}}
  let mut v=r[0]*r[0];
  for i in 1..r.len() {{v=decay*v+(1.0-decay)*r[i]*r[i];}}
  [v,v.sqrt()]
}}
'''
    raise GenerationError(f'{lang}: no TS-001 emitter')


def generate_loops(function_name, formula, options):
    if options.language=='Python':raise GenerationError('Python has its own complete numerical emitter')
    if options.structure!='function':raise GenerationError('Loop-based portable profiles support function only')
    if options.iteration!='auto':raise GenerationError('Explicit for/while selection not supported in this profile')
    if options.variant!='periodic':raise GenerationError('Variant is only valid for Future Value')
    if options.variable_names:raise GenerationError('Parameter rename is not yet implemented for portable loop profiles')
    if formula.function=='qf_bond':return _bond(options.language,function_name)
    if formula.function=='qf_ewma':return _ewma(options.language,function_name)
    raise GenerationError('No loop-based portable emitter for this formula')
