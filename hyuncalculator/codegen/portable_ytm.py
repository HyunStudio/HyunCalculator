"""Portable, dependency-free fixed coupon bond YTM root solver.

Returns nominal annual yield given full/dirty price of equally spaced coupons.
All 13 non-Python emitters use a bracketed bisection solver, not Newton's method.
"""
from __future__ import annotations
from .emitter import GenerationError


def generate_ytm(fn, formula, opt):
    lang=opt.language
    if formula.function!='qf_ytm' or lang=='Python': raise GenerationError('Invalid YTM profile')
    if opt.structure!='function' or opt.iteration!='auto' or opt.variant!='periodic' or opt.variable_names:
        raise GenerationError('Portable YTM currently requires function, auto iteration and canonical variable names')
    helper='hyun_bond_price_'+fn
    # The root solver and helper have matching rounding and zero-coupon policies.
    if lang=='R':
        return f'''# HyunCalculator BOND-002: annual nominal YTM; input is dirty price
{fn} <- function(price,face,coupon,years,freq) {{
  if(any(!is.finite(c(price,face,coupon,years,freq))) || price<=0 || face<=0 || coupon<0 || years<=0 || freq<1 || freq!=trunc(freq)) stop("Invalid bond inputs")
  periods <- years*freq
  if(periods<1 || periods>2400 || abs(periods-round(periods))>1e-8) stop("Invalid coupon periods")
  n <- as.integer(round(periods))
  if(coupon==0) return(freq*((face/price)^(1/n)-1))
  bondprice <- function(y) {{
    a <- y/freq
    if(a<=-1) return(Inf)
    if(abs(a)<1e-14) return(face+face*coupon/freq*n)
    df <- (1+a)^(-n)
    if(is.infinite(df)) return(Inf)
    return(face*df+face*coupon/freq*(1-df)/a)
  }}
  lo <- -freq*(1-1e-8); hi <- max(1,coupon)
  for(i in 1:100) {{ if(bondprice(hi)<=price) break; hi <- hi*2 }}
  if(bondprice(hi)>price) stop("Unable to bracket yield")
  for(i in 1:220) {{
    mid <- (lo+hi)/2
    if(bondprice(mid)>price) lo <- mid else hi <- mid
  }}
  return((lo+hi)/2)
}}
'''
    if lang=='MATLAB':
        return f'''% HyunCalculator BOND-002: dirty-price nominal YTM
function result = {fn}(price,face,coupon,years,freq)
    if any(~isfinite([price,face,coupon,years,freq])) || price<=0 || face<=0 || coupon<0 || years<=0 || freq<1 || freq~=fix(freq)
        error('Invalid bond inputs');
    end
    periods=years*freq;
    if periods<1 || periods>2400 || abs(periods-round(periods))>1e-8
        error('Invalid coupon periods');
    end
    n=round(periods);
    if coupon==0
        result=freq*((face/price)^(1/n)-1);return;
    end
    lo=-freq*(1-1e-8);hi=max(1,coupon);
    for i=1:100
        if {helper}(hi,face,coupon,freq,n)<=price
            break;
        end
        hi=hi*2;
    end
    if {helper}(hi,face,coupon,freq,n)>price
        error('Unable to bracket yield');
    end
    for i=1:220
        mid=(lo+hi)/2;
        if {helper}(mid,face,coupon,freq,n)>price
            lo=mid;
        else
            hi=mid;
        end
    end
    result=(lo+hi)/2;
end
function p={helper}(y,face,coupon,freq,n)
    a=y/freq;
    if a<=-1
        p=Inf;return;
    end
    if abs(a)<1e-14
        p=face+face*coupon/freq*n;return;
    end
    df=(1+a)^(-n);
    p=face*df+face*coupon/freq*(1-df)/a;
end
'''
    if lang=='Julia':
        return f'''# HyunCalculator BOND-002: dirty-price nominal YTM
function {fn}(price,face,coupon,years,freq)
    if !all(isfinite,(price,face,coupon,years,freq)) || price<=0 || face<=0 || coupon<0 || years<=0 || freq<1 || freq!=trunc(freq)
        throw(ArgumentError("Invalid bond inputs"))
    end
    periods=years*freq
    if periods<1 || periods>2400 || abs(periods-round(periods))>1e-8
        throw(ArgumentError("Invalid periods"))
    end
    n=Int(round(periods))
    if coupon==0;return freq*((face/price)^(1/n)-1);end
    price_at(y)=begin
        a=y/freq
        a<=-1 && return Inf
        abs(a)<1e-14 && return face+face*coupon/freq*n
        df=(1+a)^(-n)
        return face*df+face*coupon/freq*(1-df)/a
    end
    lo=-freq*(1-1e-8);hi=max(1,coupon)
    for _ in 1:100
        price_at(hi)<=price && break
        hi*=2
    end
    if price_at(hi)>price;throw(ArgumentError("Unable to bracket yield"));end
    for _ in 1:220
        mid=(lo+hi)/2
        if price_at(mid)>price;lo=mid;else;hi=mid;end
    end
    return (lo+hi)/2
end
'''
    # Common model with explicit static helper and bisection.
    if lang=='C':
        return f'''/* HyunCalculator BOND-002: nominal YTM from full/dirty price. */
#include <math.h>
static double {helper}(double y,double face,double coupon,int freq,int n) {{
  double a=y/freq;
  if(a<=-1) return INFINITY;
  if(fabs(a)<1e-14) return face+face*coupon/freq*n;
  double df=pow(1+a,-n);
  return face*df+face*coupon/freq*(1-df)/a;
}}
double {fn}(double price,double face,double coupon,double years,int freq) {{
  if(!isfinite(price)||!isfinite(face)||!isfinite(coupon)||!isfinite(years)||price<=0||face<=0||coupon<0||years<=0||freq<1) return NAN;
  double periods=years*freq;
  if(!isfinite(periods)||periods<1||periods>2400||fabs(periods-round(periods))>1e-8) return NAN;
  int n=(int)round(periods);
  if(coupon==0) return freq*(pow(face/price,1.0/n)-1);
  double lo=-freq*(1-1e-8),hi=fmax(1,coupon);
  for(int i=0;i<100 && {helper}(hi,face,coupon,freq,n)>price;i++)hi*=2;
  if({helper}(hi,face,coupon,freq,n)>price) return NAN;
  for(int i=0;i<220;i++){{double mid=(lo+hi)/2;if({helper}(mid,face,coupon,freq,n)>price)lo=mid;else hi=mid;}}
  return (lo+hi)/2;
}}
'''
    if lang=='C++':
        return f'''// HyunCalculator BOND-002: nominal YTM from dirty price
#include <cmath>
#include <algorithm>
#include <stdexcept>
static double {helper}(double y,double face,double coupon,int freq,int n) {{
  double a=y/freq;if(a<=-1) return INFINITY;
  if(std::fabs(a)<1e-14) return face+face*coupon/freq*n;
  double df=std::pow(1+a,-n);return face*df+face*coupon/freq*(1-df)/a;
}}
double {fn}(double price,double face,double coupon,double years,int freq) {{
  if(!std::isfinite(price)||!std::isfinite(face)||!std::isfinite(coupon)||!std::isfinite(years)||price<=0||face<=0||coupon<0||years<=0||freq<1) throw std::invalid_argument("Invalid bond inputs");
  double periods=years*freq;
  if(!std::isfinite(periods)||periods<1||periods>2400||std::fabs(periods-std::round(periods))>1e-8) throw std::invalid_argument("Invalid coupon periods");
  int n=(int)std::round(periods);
  if(coupon==0) return freq*(std::pow(face/price,1.0/n)-1);
  double lo=-freq*(1-1e-8), hi=std::max(1.0,coupon);
  for(int i=0;i<100&&{helper}(hi,face,coupon,freq,n)>price;i++) hi*=2;
  if({helper}(hi,face,coupon,freq,n)>price) throw std::invalid_argument("Unable to bracket yield");
  for(int i=0;i<220;i++){{double mid=(lo+hi)/2;if({helper}(mid,face,coupon,freq,n)>price)lo=mid;else hi=mid;}}
  return (lo+hi)/2;
}}
'''
    if lang in ('JavaScript','TypeScript'):
        typearg=': number' if lang=='TypeScript' else ''
        params=','.join(x+typearg for x in ('price','face','coupon','years','freq'))
        ret=': number' if lang=='TypeScript' else ''
        return f'''// HyunCalculator BOND-002: nominal YTM from dirty price
export function {fn}({params}){ret} {{
  if(![price,face,coupon,years,freq].every(Number.isFinite)||price<=0||face<=0||coupon<0||years<=0||!Number.isInteger(freq)||freq<1) throw new RangeError("Invalid bond inputs");
  const periods=years*freq;
  if(!Number.isFinite(periods)||periods<1||periods>2400||Math.abs(periods-Math.round(periods))>1e-8) throw new RangeError("Invalid coupon periods");
  const n=Math.round(periods);
  if(coupon===0) return freq*(Math.pow(face/price,1/n)-1);
  const priceAt=(y{typearg}){ret} => {{
    const a=y/freq;
    if(a<=-1) return Infinity;
    if(Math.abs(a)<1e-14) return face+face*coupon/freq*n;
    const df=Math.pow(1+a,-n);
    return face*df+face*coupon/freq*(1-df)/a;
  }};
  let lo=-freq*(1-1e-8),hi=Math.max(1,coupon);
  for(let i=0;i<100&&priceAt(hi)>price;i++)hi*=2;
  if(priceAt(hi)>price)throw new RangeError("Unable to bracket yield");
  for(let i=0;i<220;i++){{const mid=(lo+hi)/2;if(priceAt(mid)>price)lo=mid;else hi=mid;}}
  return (lo+hi)/2;
}}
'''
    if lang=='Java':
        return f'''// HyunCalculator BOND-002: nominal YTM from dirty price
public class GeneratedCalculator {{
  static double {helper}(double y,double face,double coupon,int freq,int n) {{
    double a=y/freq;if(a<=-1)return Double.POSITIVE_INFINITY;
    if(Math.abs(a)<1e-14)return face+face*coupon/freq*n;
    double df=Math.pow(1+a,-n);return face*df+face*coupon/freq*(1-df)/a;
  }}
  public static double {fn}(double price,double face,double coupon,double years,int freq) {{
    if(!Double.isFinite(price)||!Double.isFinite(face)||!Double.isFinite(coupon)||!Double.isFinite(years)||price<=0||face<=0||coupon<0||years<=0||freq<1)throw new IllegalArgumentException("Invalid bond inputs");
    double periods=years*freq;
    if(!Double.isFinite(periods)||periods<1||periods>2400||Math.abs(periods-Math.rint(periods))>1e-8)throw new IllegalArgumentException("Invalid coupon periods");
    int n=(int)Math.rint(periods);
    if(coupon==0)return freq*(Math.pow(face/price,1.0/n)-1);
    double lo=-freq*(1-1e-8),hi=Math.max(1,coupon);
    for(int i=0;i<100&&{helper}(hi,face,coupon,freq,n)>price;i++)hi*=2;
    if({helper}(hi,face,coupon,freq,n)>price)throw new IllegalArgumentException("Unable to bracket yield");
    for(int i=0;i<220;i++){{double mid=(lo+hi)/2;if({helper}(mid,face,coupon,freq,n)>price)lo=mid;else hi=mid;}}
    return (lo+hi)/2;
  }}
}}
'''
    if lang=='C#':
        return f'''// HyunCalculator BOND-002: nominal YTM from dirty price
using System;
public static class GeneratedCalculator {{
  static double {helper}(double y,double face,double coupon,int freq,int n) {{
    double a=y/freq;if(a<=-1)return double.PositiveInfinity;
    if(Math.Abs(a)<1e-14)return face+face*coupon/freq*n;
    double df=Math.Pow(1+a,-n);return face*df+face*coupon/freq*(1-df)/a;
  }}
  public static double {fn}(double price,double face,double coupon,double years,int freq) {{
    if(!double.IsFinite(price)||!double.IsFinite(face)||!double.IsFinite(coupon)||!double.IsFinite(years)||price<=0||face<=0||coupon<0||years<=0||freq<1)throw new ArgumentException("Invalid bond inputs");
    double periods=years*freq;
    if(!double.IsFinite(periods)||periods<1||periods>2400||Math.Abs(periods-Math.Round(periods))>1e-8)throw new ArgumentException("Invalid coupon periods");
    int n=(int)Math.Round(periods);
    if(coupon==0)return freq*(Math.Pow(face/price,1.0/n)-1);
    double lo=-freq*(1-1e-8),hi=Math.Max(1,coupon);
    for(int i=0;i<100&&{helper}(hi,face,coupon,freq,n)>price;i++)hi*=2;
    if({helper}(hi,face,coupon,freq,n)>price)throw new ArgumentException("Unable to bracket yield");
    for(int i=0;i<220;i++){{double mid=(lo+hi)/2;if({helper}(mid,face,coupon,freq,n)>price)lo=mid;else hi=mid;}}
    return (lo+hi)/2;
  }}
}}
'''
    if lang=='Swift':
        return f'''// HyunCalculator BOND-002: nominal YTM from dirty price
import Foundation
func {fn}(_ price:Double,_ face:Double,_ coupon:Double,_ years:Double,_ freq:Int)->Double{{
  guard [price,face,coupon,years].allSatisfy({{$0.isFinite}}),price>0,face>0,coupon>=0,years>0,freq>0 else{{return Double.nan}}
  let f=Double(freq), periods=years*f
  guard periods.isFinite, periods>=1,periods<=2400,abs(periods-periods.rounded())<=1e-8 else{{return Double.nan}}
  let n=Int(periods.rounded())
  if coupon==0{{return f*(pow(face/price,1/Double(n))-1)}}
  func priceAt(_ y:Double)->Double{{
    let a=y/f
    if a <= -1{{return Double.infinity}}
    if abs(a)<1e-14{{return face+face*coupon/f*Double(n)}}
    let df=pow(1+a,-Double(n))
    return face*df+face*coupon/f*(1-df)/a
  }}
  var lo = -f*(1-1e-8), hi=max(1.0,coupon)
  for _ in 0..<100{{if priceAt(hi)<=price{{break}}; hi*=2}}
  if priceAt(hi)>price{{return Double.nan}}
  for _ in 0..<220{{let mid=(lo+hi)/2;if priceAt(mid)>price{{lo=mid}}else{{hi=mid}}}}
  return (lo+hi)/2
}}
'''
    if lang=='Kotlin':
        return f'''// HyunCalculator BOND-002: nominal YTM from dirty price
import kotlin.math.*
fun {fn}(price:Double,face:Double,coupon:Double,years:Double,freq:Int):Double {{
  require(listOf(price,face,coupon,years).all{{it.isFinite()}}&&price>0&&face>0&&coupon>=0&&years>0&&freq>0){{"Invalid bond inputs"}}
  val f=freq.toDouble();val periods=years*f
  require(periods.isFinite()&&periods>=1&&periods<=2400&&abs(periods-round(periods))<=1e-8){{"Invalid coupon periods"}}
  val n=round(periods).toInt()
  if(coupon==0.0)return f*((face/price).pow(1/n.toDouble())-1)
  fun priceAt(y:Double):Double{{
    val a=y/f
    if(a<=-1)return Double.POSITIVE_INFINITY
    if(abs(a)<1e-14)return face+face*coupon/f*n
    val df=(1+a).pow(-n.toDouble())
    return face*df+face*coupon/f*(1-df)/a
  }}
  var lo=-f*(1-1e-8);var hi=max(1.0,coupon)
  for(i in 0 until 100){{if(priceAt(hi)<=price)break;hi*=2}}
  require(priceAt(hi)<=price){{"Unable to bracket yield"}}
  for(i in 0 until 220){{val mid=(lo+hi)/2;if(priceAt(mid)>price)lo=mid else hi=mid}}
  return (lo+hi)/2
}}
'''
    if lang=='Go':
        return f'''// HyunCalculator BOND-002: nominal YTM from dirty price
package main
import "math"
func {fn}(price,face,coupon,years float64,freq int)float64{{
  if math.IsNaN(price)||math.IsNaN(face)||math.IsNaN(coupon)||math.IsNaN(years)||math.IsInf(price,0)||math.IsInf(face,0)||math.IsInf(coupon,0)||math.IsInf(years,0)||price<=0||face<=0||coupon<0||years<=0||freq<1{{return math.NaN()}}
  f:=float64(freq);periods:=years*f
  if math.IsNaN(periods)||math.IsInf(periods,0)||periods<1||periods>2400||math.Abs(periods-math.Round(periods))>1e-8{{return math.NaN()}}
  n:=int(math.Round(periods))
  if coupon==0{{return f*(math.Pow(face/price,1/float64(n))-1)}}
  priceAt:=func(y float64)float64{{
    a:=y/f;if a<=-1{{return math.Inf(1)}}
    if math.Abs(a)<1e-14{{return face+face*coupon/f*float64(n)}}
    df:=math.Pow(1+a,-float64(n))
    return face*df+face*coupon/f*(1-df)/a
  }}
  lo,hi:=-f*(1-1e-8),math.Max(1,coupon)
  for i:=0;i<100&&priceAt(hi)>price;i++{{hi*=2}}
  if priceAt(hi)>price{{return math.NaN()}}
  for i:=0;i<220;i++{{mid:=(lo+hi)/2;if priceAt(mid)>price{{lo=mid}}else{{hi=mid}}}}
  return (lo+hi)/2
}}
'''
    if lang=='Rust':
        return f'''// HyunCalculator BOND-002: nominal YTM from dirty price
pub fn {fn}(price:f64,face:f64,coupon:f64,years:f64,freq:i32)->f64{{
  if !price.is_finite()||!face.is_finite()||!coupon.is_finite()||!years.is_finite()||price<=0.0||face<=0.0||coupon<0.0||years<=0.0||freq<1{{return f64::NAN;}}
  let f=freq as f64;let periods=years*f;
  if !periods.is_finite()||periods<1.0||periods>2400.0||(periods-periods.round()).abs()>1e-8{{return f64::NAN;}}
  let n=periods.round() as i32;
  if coupon==0.0{{return f*((face/price).powf(1.0/(n as f64))-1.0);}}
  let price_at=|y:f64|{{
    let a=y/f;
    if a<=-1.0{{return f64::INFINITY;}}
    if a.abs()<1e-14{{return face+face*coupon/f*(n as f64);}}
    let df=(1.0+a).powi(-n);
    face*df+face*coupon/f*(1.0-df)/a
  }};
  let(mut lo,mut hi)=(-f*(1.0-1e-8),1.0_f64.max(coupon));
  for _ in 0..100{{if price_at(hi)<=price{{break;}}hi*=2.0;}}
  if price_at(hi)>price{{return f64::NAN;}}
  for _ in 0..220{{let mid=(lo+hi)/2.0;if price_at(mid)>price{{lo=mid;}}else{{hi=mid;}}}}
  (lo+hi)/2.0
}}
'''
    raise GenerationError(f'{lang}: YTM emitter unavailable')
