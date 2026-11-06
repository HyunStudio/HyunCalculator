"""Self-contained Black–Scholes/Greeks emitters for the 13 non-Python targets.

The standard normal CDF is computed from an absolutely convergent series:
Phi(x) = 1/2 + phi(x) * sum_{k>=0} x^(2k+1)/(2k+1)!! (for x>=0),
with reflection for x<0. At |x|>8 the negligible tail is rounded to 0/1.
Unlike 5-term approximations, the series agrees with SciPy to about 1e-15
absolute for -8<=x<=8, without external packages. Max 499 iterations.
"""
from __future__ import annotations
from .emitter import GenerationError
SUPPORTED=frozenset({'qf_bs'})
NOTE='HyunCalculator DERIV-001: European Black-Scholes with continuous dividend; returns Price, Delta, Gamma, Vega (per 1.00 vol), Theta (per year), Rho (per 1.00 rate).'


def generate_bs(fn, formula, opt):
    if opt.language=='Python':raise GenerationError('Python uses reference implementation')
    if opt.structure!='function' or opt.iteration!='auto' or opt.variant!='periodic' or opt.variable_names:
        raise GenerationError('Black-Scholes supports function/auto and fixed parameter names only')
    l=opt.language
    if l=='R':
        return f'''# {NOTE}
hyun_cdf <- function(x) {{
  if(x>8)return(1);if(x< -8)return(0)
  a<-abs(x);term<-a;sum<-term
  for(k in 1:499){{term<-term*a*a/(2*k+1);sum<-sum+term;if(term<=1e-16*sum)break}}
  0.5+ifelse(x>=0,1,-1)*exp(-0.5*a*a)*0.39894228040143267794*sum
}}
{fn} <- function(s,k,t,r,sigma,q=0,option="call"){{
  if(any(!is.finite(c(s,k,t,r,sigma,q)))||s<=0||k<=0||t<0||sigma<0||!(option %in% c("call","put")))stop("Invalid Black-Scholes inputs")
  sign<-if(option=="call")1 else -1
  if(t==0)return(c(Price=max(sign*(s-k),0),Delta=NaN,Gamma=NaN,Vega=0,Theta=NaN,Rho=0))
  if(sigma==0){{call<-max(s*exp(-q*t)-k*exp(-r*t),0);put<-max(k*exp(-r*t)-s*exp(-q*t),0);
    return(c(Price=if(sign==1)call else put,Delta=NaN,Gamma=NaN,Vega=0,Theta=NaN,Rho=NaN))}}
  root<-sigma*sqrt(t);d1<-(log(s/k)+(r-q+0.5*sigma*sigma)*t)/root;d2<-d1-root
  dq<-exp(-q*t);dr<-exp(-r*t);pdf<-exp(-0.5*d1*d1)*0.39894228040143267794
  price<-sign*(s*dq*hyun_cdf(sign*d1)-k*dr*hyun_cdf(sign*d2))
  delta<-sign*dq*hyun_cdf(sign*d1);gamma<-dq*pdf/(s*root);vega<-s*dq*pdf*sqrt(t)
  theta<--s*dq*pdf*sigma/(2*sqrt(t))+sign*q*s*dq*hyun_cdf(sign*d1)-sign*r*k*dr*hyun_cdf(sign*d2)
  rho<-sign*k*t*dr*hyun_cdf(sign*d2)
  c(Price=price,Delta=delta,Gamma=gamma,Vega=vega,Theta=theta,Rho=rho)
}}
'''
    if l=='MATLAB':
        return f'''% {NOTE}
function result = {fn}(s,k,t,r,sigma,q,option)
  if ~isscalar(s) || ~isscalar(k) || ~isscalar(t) || ~isscalar(r) || ~isscalar(sigma) || ~isscalar(q) || any(~isfinite([s,k,t,r,sigma,q])) || s<=0 || k<=0 || t<0 || sigma<0 || ~(strcmp(option,'call') || strcmp(option,'put'))
    error('Invalid Black-Scholes inputs');
  end
  sign=1;if strcmp(option,'put'),sign=-1;end
  if t==0
    result=[max(sign*(s-k),0),NaN,NaN,0,NaN,0];return;
  end
  if sigma==0
    call=max(s*exp(-q*t)-k*exp(-r*t),0);put=max(k*exp(-r*t)-s*exp(-q*t),0);
    price=call;if sign==-1,price=put;end
    result=[price,NaN,NaN,0,NaN,NaN];return;
  end
  root=sigma*sqrt(t);d1=(log(s/k)+(r-q+0.5*sigma^2)*t)/root;d2=d1-root;
  dq=exp(-q*t);dr=exp(-r*t);pdf=exp(-0.5*d1^2)*0.39894228040143267794;
  price=sign*(s*dq*hyun_cdf(sign*d1)-k*dr*hyun_cdf(sign*d2));
  delta=sign*dq*hyun_cdf(sign*d1);gamma=dq*pdf/(s*root);vega=s*dq*pdf*sqrt(t);
  theta=-s*dq*pdf*sigma/(2*sqrt(t))+sign*q*s*dq*hyun_cdf(sign*d1)-sign*r*k*dr*hyun_cdf(sign*d2);
  rho=sign*k*t*dr*hyun_cdf(sign*d2);
  result=[price,delta,gamma,vega,theta,rho];
end
function p=hyun_cdf(x)
  if x>8,p=1;return;end
  if x< -8,p=0;return;end
  a=abs(x);term=a;v=term;
  for i=1:499
    term=term*a*a/(2*i+1);v=v+term;
    if term<=1e-16*v,break;end
  end
  sign=1;if x<0,sign=-1;end
  p=0.5+sign*exp(-0.5*a*a)*0.39894228040143267794*v;
end
'''
    if l=='Julia':
        return f'''# {NOTE}
function hyun_cdf(x)
  if x>8;return 1.0;end
  if x< -8;return 0.0;end
  a=abs(x);term=a;v=term
  for i in 1:499
    term*=a*a/(2*i+1);v+=term
    if term<=1e-16*v;break;end
  end
  return 0.5+(x>=0 ? 1.0 : -1.0)*exp(-0.5*a*a)*0.39894228040143267794*v
end
function {fn}(s,k,t,r,sigma,q=0.0,option="call")
  if !all(isfinite,(s,k,t,r,sigma,q)) || s<=0 || k<=0 || t<0 || sigma<0 || !(option in ("call","put"))
    throw(ArgumentError("Invalid Black-Scholes inputs"))
  end
  sign=option=="call" ? 1.0 : -1.0
  if t==0;return (Price=max(sign*(s-k),0.0),Delta=NaN,Gamma=NaN,Vega=0.0,Theta=NaN,Rho=0.0);end
  if sigma==0
    call=max(s*exp(-q*t)-k*exp(-r*t),0.0);put=max(k*exp(-r*t)-s*exp(-q*t),0.0)
    return (Price=sign==1 ? call : put,Delta=NaN,Gamma=NaN,Vega=0.0,Theta=NaN,Rho=NaN)
  end
  root=sigma*sqrt(t);d1=(log(s/k)+(r-q+0.5*sigma^2)*t)/root;d2=d1-root
  dq=exp(-q*t);dr=exp(-r*t);pdf=exp(-0.5*d1*d1)*0.39894228040143267794
  price=sign*(s*dq*hyun_cdf(sign*d1)-k*dr*hyun_cdf(sign*d2))
  delta=sign*dq*hyun_cdf(sign*d1);gamma=dq*pdf/(s*root);vega=s*dq*pdf*sqrt(t)
  theta=-s*dq*pdf*sigma/(2*sqrt(t))+sign*q*s*dq*hyun_cdf(sign*d1)-sign*r*k*dr*hyun_cdf(sign*d2)
  rho=sign*k*t*dr*hyun_cdf(sign*d2)
  return (Price=price,Delta=delta,Gamma=gamma,Vega=vega,Theta=theta,Rho=rho)
end
'''
    if l=='C':
        return f'''/* {NOTE} */
#include <math.h>
#include <string.h>
typedef struct {{double values[6];}} HyunResult;
static double hyun_cdf(double x){{
  if(x>8)return 1;
  if(x< -8)return 0;
  double a=fabs(x),term=a,v=term;
  for(int i=1;i<500;i++){{term*=a*a/(2*i+1);v+=term;if(term<=1e-16*v)break;}}
  return .5+(x>=0?1:-1)*exp(-.5*a*a)*0.39894228040143267794*v;
}}
HyunResult {fn}(double s,double k,double t,double r,double sigma,double q,const char* option){{
  HyunResult invalid={{{{NAN,NAN,NAN,NAN,NAN,NAN}}}};
  if(!option||!isfinite(s)||!isfinite(k)||!isfinite(t)||!isfinite(r)||!isfinite(sigma)||!isfinite(q)||s<=0||k<=0||t<0||sigma<0||(strcmp(option,"call")&&strcmp(option,"put")))return invalid;
  double sign=strcmp(option,"call")==0?1:-1;
  if(t==0){{HyunResult o={{{{fmax(sign*(s-k),0),NAN,NAN,0,NAN,0}}}};return o;}}
  if(sigma==0){{double call=fmax(s*exp(-q*t)-k*exp(-r*t),0),put=fmax(k*exp(-r*t)-s*exp(-q*t),0);
    HyunResult o={{{{sign==1?call:put,NAN,NAN,0,NAN,NAN}}}};return o;}}
  double root=sigma*sqrt(t),d1=(log(s/k)+(r-q+.5*sigma*sigma)*t)/root,d2=d1-root;
  double dq=exp(-q*t),dr=exp(-r*t),pdf=exp(-.5*d1*d1)*0.39894228040143267794;
  double price=sign*(s*dq*hyun_cdf(sign*d1)-k*dr*hyun_cdf(sign*d2));
  double delta=sign*dq*hyun_cdf(sign*d1),gamma=dq*pdf/(s*root),vega=s*dq*pdf*sqrt(t);
  double theta=-s*dq*pdf*sigma/(2*sqrt(t))+sign*q*s*dq*hyun_cdf(sign*d1)-sign*r*k*dr*hyun_cdf(sign*d2);
  double rho=sign*k*t*dr*hyun_cdf(sign*d2);
  HyunResult o={{{{price,delta,gamma,vega,theta,rho}}}};return o;
}}
'''
    if l=='C++':
        return f'''// {NOTE}
#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>
#include <string>
static double hyun_cdf(double x){{
  if(x>8)return 1;
  if(x< -8)return 0;
  double a=std::abs(x),term=a,v=term;
  for(int i=1;i<500;i++){{term*=a*a/(2*i+1);v+=term;if(term<=1e-16*v)break;}}
  return .5+(x>=0?1:-1)*std::exp(-.5*a*a)*0.39894228040143267794*v;
}}
std::array<double,6> {fn}(double s,double k,double t,double r,double sigma,double q,const std::string& option){{
  if(!std::isfinite(s)||!std::isfinite(k)||!std::isfinite(t)||!std::isfinite(r)||!std::isfinite(sigma)||!std::isfinite(q)||s<=0||k<=0||t<0||sigma<0||(option!="call"&&option!="put"))throw std::invalid_argument("Invalid Black-Scholes inputs");
  double sign=option=="call"?1:-1;
  if(t==0)return {{std::max(sign*(s-k),0.0),NAN,NAN,0,NAN,0}};
  if(sigma==0){{double call=std::max(s*std::exp(-q*t)-k*std::exp(-r*t),0.0),put=std::max(k*std::exp(-r*t)-s*std::exp(-q*t),0.0);
    return {{sign==1?call:put,NAN,NAN,0,NAN,NAN}};}}
  double root=sigma*std::sqrt(t),d1=(std::log(s/k)+(r-q+.5*sigma*sigma)*t)/root,d2=d1-root;
  double dq=std::exp(-q*t),dr=std::exp(-r*t),pdf=std::exp(-.5*d1*d1)*0.39894228040143267794;
  double price=sign*(s*dq*hyun_cdf(sign*d1)-k*dr*hyun_cdf(sign*d2));
  double delta=sign*dq*hyun_cdf(sign*d1),gamma=dq*pdf/(s*root),vega=s*dq*pdf*std::sqrt(t);
  double theta=-s*dq*pdf*sigma/(2*std::sqrt(t))+sign*q*s*dq*hyun_cdf(sign*d1)-sign*r*k*dr*hyun_cdf(sign*d2);
  double rho=sign*k*t*dr*hyun_cdf(sign*d2);
  return {{price,delta,gamma,vega,theta,rho}};
}}
'''
    if l in ('JavaScript','TypeScript'):
        typed=': number' if l=='TypeScript' else ''
        params=','.join((x+typed) for x in ('s','k','t','r','sigma','q'))+(', option: string' if l=='TypeScript' else ',option')
        ret=': number[]' if l=='TypeScript' else ''
        return f'''// {NOTE}
function hyun_cdf(x{typed}){': number' if l=='TypeScript' else ''}{{
  if(x>8)return 1;
  if(x< -8)return 0;
  const a=Math.abs(x);let term=a,v=term;
  for(let i=1;i<500;i++){{term*=a*a/(2*i+1);v+=term;if(term<=1e-16*v)break;}}
  return .5+(x>=0?1:-1)*Math.exp(-.5*a*a)*0.39894228040143267794*v;
}}
export function {fn}({params}){ret}{{
  if(![s,k,t,r,sigma,q].every(Number.isFinite)||s<=0||k<=0||t<0||sigma<0||(option!=="call"&&option!=="put"))throw new RangeError("Invalid Black-Scholes inputs");
  const sign=option==="call"?1:-1;
  if(t===0)return [Math.max(sign*(s-k),0),NaN,NaN,0,NaN,0];
  if(sigma===0){{const call=Math.max(s*Math.exp(-q*t)-k*Math.exp(-r*t),0),put=Math.max(k*Math.exp(-r*t)-s*Math.exp(-q*t),0);
    return [sign===1?call:put,NaN,NaN,0,NaN,NaN];}}
  const root=sigma*Math.sqrt(t),d1=(Math.log(s/k)+(r-q+.5*sigma*sigma)*t)/root,d2=d1-root;
  const dq=Math.exp(-q*t),dr=Math.exp(-r*t),pdf=Math.exp(-.5*d1*d1)*0.39894228040143267794;
  const price=sign*(s*dq*hyun_cdf(sign*d1)-k*dr*hyun_cdf(sign*d2));
  const delta=sign*dq*hyun_cdf(sign*d1),gamma=dq*pdf/(s*root),vega=s*dq*pdf*Math.sqrt(t);
  const theta=-s*dq*pdf*sigma/(2*Math.sqrt(t))+sign*q*s*dq*hyun_cdf(sign*d1)-sign*r*k*dr*hyun_cdf(sign*d2);
  const rho=sign*k*t*dr*hyun_cdf(sign*d2);
  return [price,delta,gamma,vega,theta,rho];
}}
'''
    if l=='Java':
        return f'''// {NOTE}
public class GeneratedCalculator{{
  private static double hyun_cdf(double x){{
    if(x>8)return 1;
  if(x< -8)return 0;
    double a=Math.abs(x),term=a,v=term;
    for(int i=1;i<500;i++){{term*=a*a/(2*i+1);v+=term;if(term<=1e-16*v)break;}}
    return .5+(x>=0?1:-1)*Math.exp(-.5*a*a)*0.39894228040143267794*v;
  }}
  public static double[] {fn}(double s,double k,double t,double r,double sigma,double q,String option){{
    if(!Double.isFinite(s)||!Double.isFinite(k)||!Double.isFinite(t)||!Double.isFinite(r)||!Double.isFinite(sigma)||!Double.isFinite(q)||s<=0||k<=0||t<0||sigma<0||(!"call".equals(option)&&!"put".equals(option)))throw new IllegalArgumentException("Invalid Black-Scholes inputs");
    double sign="call".equals(option)?1:-1;
    if(t==0)return new double[]{{Math.max(sign*(s-k),0),Double.NaN,Double.NaN,0,Double.NaN,0}};
    if(sigma==0){{double call=Math.max(s*Math.exp(-q*t)-k*Math.exp(-r*t),0),put=Math.max(k*Math.exp(-r*t)-s*Math.exp(-q*t),0);
      return new double[]{{sign==1?call:put,Double.NaN,Double.NaN,0,Double.NaN,Double.NaN}};}}
    double root=sigma*Math.sqrt(t),d1=(Math.log(s/k)+(r-q+.5*sigma*sigma)*t)/root,d2=d1-root;
    double dq=Math.exp(-q*t),dr=Math.exp(-r*t),pdf=Math.exp(-.5*d1*d1)*0.39894228040143267794;
    double price=sign*(s*dq*hyun_cdf(sign*d1)-k*dr*hyun_cdf(sign*d2));
    double delta=sign*dq*hyun_cdf(sign*d1),gamma=dq*pdf/(s*root),vega=s*dq*pdf*Math.sqrt(t);
    double theta=-s*dq*pdf*sigma/(2*Math.sqrt(t))+sign*q*s*dq*hyun_cdf(sign*d1)-sign*r*k*dr*hyun_cdf(sign*d2);
    double rho=sign*k*t*dr*hyun_cdf(sign*d2);
    return new double[]{{price,delta,gamma,vega,theta,rho}};
  }}
}}
'''
    if l=='C#':
        return f'''// {NOTE}
using System;
public static class GeneratedCalculator{{
  private static double hyun_cdf(double x){{
    if(x>8)return 1;
  if(x< -8)return 0;
    double a=Math.Abs(x),term=a,v=term;
    for(int i=1;i<500;i++){{term*=a*a/(2*i+1);v+=term;if(term<=1e-16*v)break;}}
    return .5+(x>=0?1:-1)*Math.Exp(-.5*a*a)*0.39894228040143267794*v;
  }}
  public static double[] {fn}(double s,double k,double t,double r,double sigma,double q,string option){{
    if(!double.IsFinite(s)||!double.IsFinite(k)||!double.IsFinite(t)||!double.IsFinite(r)||!double.IsFinite(sigma)||!double.IsFinite(q)||s<=0||k<=0||t<0||sigma<0||(option!="call"&&option!="put"))throw new ArgumentException("Invalid Black-Scholes inputs");
    double sign=option=="call"?1:-1;
    if(t==0)return new double[]{{Math.Max(sign*(s-k),0),double.NaN,double.NaN,0,double.NaN,0}};
    if(sigma==0){{double call=Math.Max(s*Math.Exp(-q*t)-k*Math.Exp(-r*t),0),put=Math.Max(k*Math.Exp(-r*t)-s*Math.Exp(-q*t),0);
      return new double[]{{sign==1?call:put,double.NaN,double.NaN,0,double.NaN,double.NaN}};}}
    double root=sigma*Math.Sqrt(t),d1=(Math.Log(s/k)+(r-q+.5*sigma*sigma)*t)/root,d2=d1-root;
    double dq=Math.Exp(-q*t),dr=Math.Exp(-r*t),pdf=Math.Exp(-.5*d1*d1)*0.39894228040143267794;
    double price=sign*(s*dq*hyun_cdf(sign*d1)-k*dr*hyun_cdf(sign*d2));
    double delta=sign*dq*hyun_cdf(sign*d1),gamma=dq*pdf/(s*root),vega=s*dq*pdf*Math.Sqrt(t);
    double theta=-s*dq*pdf*sigma/(2*Math.Sqrt(t))+sign*q*s*dq*hyun_cdf(sign*d1)-sign*r*k*dr*hyun_cdf(sign*d2);
    double rho=sign*k*t*dr*hyun_cdf(sign*d2);
    return new double[]{{price,delta,gamma,vega,theta,rho}};
  }}
}}
'''
    if l=='Swift':
        return f'''// {NOTE}
import Foundation
private func hyun_cdf(_ x:Double)->Double{{
  if x>8{{return 1}};if x < -8{{return 0}}
  let a=abs(x);var term=a;var v=term
  for i in 1..<500{{term*=a*a/Double(2*i+1);v+=term;if term<=1e-16*v{{break}}}}
  return 0.5+(x>=0 ? 1.0 : -1.0)*exp(-0.5*a*a)*0.39894228040143267794*v
}}
func {fn}(_ s:Double,_ k:Double,_ t:Double,_ r:Double,_ sigma:Double,_ q:Double,_ option:String)->[Double]{{
  guard [s,k,t,r,sigma,q].allSatisfy({{$0.isFinite}}),s>0,k>0,t>=0,sigma>=0,(option=="call"||option=="put") else {{return Array(repeating:Double.nan,count:6)}}
  let sign=option=="call" ? 1.0 : -1.0
  if t==0{{return [max(sign*(s-k),0),Double.nan,Double.nan,0,Double.nan,0]}}
  if sigma==0{{let call=max(s*exp(-q*t)-k*exp(-r*t),0),put=max(k*exp(-r*t)-s*exp(-q*t),0)
    return [sign==1 ? call : put,Double.nan,Double.nan,0,Double.nan,Double.nan]}}
  let root=sigma*sqrt(t),d1=(log(s/k)+(r-q+0.5*sigma*sigma)*t)/root
  let d2=d1-root,dq=exp(-q*t),dr=exp(-r*t),pdf=exp(-0.5*d1*d1)*0.39894228040143267794
  let price=sign*(s*dq*hyun_cdf(sign*d1)-k*dr*hyun_cdf(sign*d2))
  let delta=sign*dq*hyun_cdf(sign*d1),gamma=dq*pdf/(s*root),vega=s*dq*pdf*sqrt(t)
  let theta = -s*dq*pdf*sigma/(2*sqrt(t))+sign*q*s*dq*hyun_cdf(sign*d1)-sign*r*k*dr*hyun_cdf(sign*d2)
  let rho=sign*k*t*dr*hyun_cdf(sign*d2)
  return [price,delta,gamma,vega,theta,rho]
}}
'''
    if l=='Kotlin':
        return f'''// {NOTE}
import kotlin.math.*
private fun hyun_cdf(x:Double):Double{{
  if(x>8)return 1.0;if(x < -8)return 0.0
  val a=abs(x);var term=a;var v=term
  for(i in 1 until 500){{term*=a*a/(2*i+1);v+=term;if(term<=1e-16*v)break}}
  return 0.5+(if(x>=0)1.0 else -1.0)*exp(-0.5*a*a)*0.39894228040143267794*v
}}
fun {fn}(s:Double,k:Double,t:Double,r:Double,sigma:Double,q:Double,option:String):DoubleArray{{
  require(listOf(s,k,t,r,sigma,q).all{{it.isFinite()}}&&s>0&&k>0&&t>=0&&sigma>=0&&(option=="call"||option=="put")){{"Invalid Black-Scholes inputs"}}
  val sign=if(option=="call")1.0 else -1.0
  if(t==0.0)return doubleArrayOf(max(sign*(s-k),0.0),Double.NaN,Double.NaN,0.0,Double.NaN,0.0)
  if(sigma==0.0){{val call=max(s*exp(-q*t)-k*exp(-r*t),0.0);val put=max(k*exp(-r*t)-s*exp(-q*t),0.0)
    return doubleArrayOf(if(sign==1.0)call else put,Double.NaN,Double.NaN,0.0,Double.NaN,Double.NaN)}}
  val root=sigma*sqrt(t);val d1=(ln(s/k)+(r-q+0.5*sigma*sigma)*t)/root;val d2=d1-root
  val dq=exp(-q*t);val dr=exp(-r*t);val pdf=exp(-0.5*d1*d1)*0.39894228040143267794
  val price=sign*(s*dq*hyun_cdf(sign*d1)-k*dr*hyun_cdf(sign*d2))
  val delta=sign*dq*hyun_cdf(sign*d1);val gamma=dq*pdf/(s*root);val vega=s*dq*pdf*sqrt(t)
  val theta=-s*dq*pdf*sigma/(2*sqrt(t))+sign*q*s*dq*hyun_cdf(sign*d1)-sign*r*k*dr*hyun_cdf(sign*d2)
  val rho=sign*k*t*dr*hyun_cdf(sign*d2)
  return doubleArrayOf(price,delta,gamma,vega,theta,rho)
}}
'''
    if l=='Go':
        return f'''// {NOTE}
package main
import "math"
func hyun_cdf(x float64)float64{{
  if x>8{{return 1}};if x < -8{{return 0}}
  a:=math.Abs(x);term:=a;v:=term
  for i:=1;i<500;i++{{term*=a*a/float64(2*i+1);v+=term;if term<=1e-16*v{{break}}}}
  sign:=1.0;if x<0{{sign=-1}}
  return .5+sign*math.Exp(-.5*a*a)*0.39894228040143267794*v
}}
func {fn}(s,k,t,r,sigma,q float64,option string)[6]float64{{
  fail:=[6]float64{{math.NaN(),math.NaN(),math.NaN(),math.NaN(),math.NaN(),math.NaN()}}
  for _,x:=range []float64{{s,k,t,r,sigma,q}}{{if math.IsNaN(x)||math.IsInf(x,0){{return fail}}}}
  if s<=0||k<=0||t<0||sigma<0||(option!="call"&&option!="put"){{return fail}}
  sign:=1.0;if option=="put"{{sign=-1}}
  if t==0{{return [6]float64{{math.Max(sign*(s-k),0),math.NaN(),math.NaN(),0,math.NaN(),0}}}}
  if sigma==0{{call:=math.Max(s*math.Exp(-q*t)-k*math.Exp(-r*t),0);put:=math.Max(k*math.Exp(-r*t)-s*math.Exp(-q*t),0)
    price:=call;if sign==-1{{price=put}}
    return [6]float64{{price,math.NaN(),math.NaN(),0,math.NaN(),math.NaN()}}}}
  root:=sigma*math.Sqrt(t);d1:=(math.Log(s/k)+(r-q+.5*sigma*sigma)*t)/root;d2:=d1-root
  dq:=math.Exp(-q*t);dr:=math.Exp(-r*t);pdf:=math.Exp(-.5*d1*d1)*0.39894228040143267794
  price:=sign*(s*dq*hyun_cdf(sign*d1)-k*dr*hyun_cdf(sign*d2))
  delta:=sign*dq*hyun_cdf(sign*d1);gamma:=dq*pdf/(s*root);vega:=s*dq*pdf*math.Sqrt(t)
  theta:=-s*dq*pdf*sigma/(2*math.Sqrt(t))+sign*q*s*dq*hyun_cdf(sign*d1)-sign*r*k*dr*hyun_cdf(sign*d2)
  rho:=sign*k*t*dr*hyun_cdf(sign*d2)
  return [6]float64{{price,delta,gamma,vega,theta,rho}}
}}
'''
    if l=='Rust':
        return f'''// {NOTE}
fn hyun_cdf(x:f64)->f64{{
  if x>8.0{{return 1.0;}}if x< -8.0{{return 0.0;}}
  let a=x.abs();let mut term=a;let mut v=term;
  for i in 1..500{{term*=a*a/(2*i+1) as f64;v+=term;if term<=1e-16*v{{break;}}}}
  0.5+(if x>=0.0{{1.0}}else{{-1.0}})*(-0.5*a*a).exp()*0.39894228040143267794*v
}}
pub fn {fn}(s:f64,k:f64,t:f64,r:f64,sigma:f64,q:f64,option:&str)->[f64;6]{{
  let fail=[f64::NAN;6];
  if ![s,k,t,r,sigma,q].iter().all(|x|x.is_finite())||s<=0.0||k<=0.0||t<0.0||sigma<0.0||(option!="call"&&option!="put"){{return fail;}}
  let sign=if option=="call"{{1.0}}else{{-1.0}};
  if t==0.0{{return [(sign*(s-k)).max(0.0),f64::NAN,f64::NAN,0.0,f64::NAN,0.0];}}
  if sigma==0.0{{let call=(s*(-q*t).exp()-k*(-r*t).exp()).max(0.0);let put=(k*(-r*t).exp()-s*(-q*t).exp()).max(0.0);
    return [if sign==1.0{{call}}else{{put}},f64::NAN,f64::NAN,0.0,f64::NAN,f64::NAN];}}
  let root=sigma*t.sqrt();let d1=((s/k).ln()+(r-q+0.5*sigma*sigma)*t)/root;let d2=d1-root;
  let dq=(-q*t).exp();let dr=(-r*t).exp();let pdf=(-0.5*d1*d1).exp()*0.39894228040143267794;
  let price=sign*(s*dq*hyun_cdf(sign*d1)-k*dr*hyun_cdf(sign*d2));
  let delta=sign*dq*hyun_cdf(sign*d1);let gamma=dq*pdf/(s*root);let vega=s*dq*pdf*t.sqrt();
  let theta=-s*dq*pdf*sigma/(2.0*t.sqrt())+sign*q*s*dq*hyun_cdf(sign*d1)-sign*r*k*dr*hyun_cdf(sign*d2);
  let rho=sign*k*t*dr*hyun_cdf(sign*d2);
  [price,delta,gamma,vega,theta,rho]
}}
'''
    raise GenerationError(f'{l}: Black-Scholes code emitter missing')
