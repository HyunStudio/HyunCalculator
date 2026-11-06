"""Standalone standard-library code emitters for statistical distributions and covariance.

STAT-001 normal PDF/CDF/survival/PPF and STAT-002 sample covariance/correlation.
Python is emitted by the pre-existing full-reference code generator; these
13 targets deliberately document their output contracts and approximation error.
"""
from __future__ import annotations
import re

SUPPORTED = frozenset({'qf_normal', 'qf_cov'})

# Peter J. Acklam's rational approximation for the standard-normal quantile.
A=(-39.69683028665376,220.9460984245205,-275.9285104469687,138.357751867269,-30.66479806614716,2.506628277459239)
B=(-54.47609879822406,161.5858368580409,-155.6989798598866,66.80131188771972,-13.28068155288572)
C=(-0.007784894002430293,-0.3223964580411365,-2.400758277161838,-2.549732539343734,4.374664141464968,2.938163982698783)
D=(0.007784695709041462,0.3224671290700398,2.445134137142996,3.754408661907416)


def _poly(vals, x):
    expression=repr(float(vals[0]))
    for v in vals[1:]:
        expression=f'({expression}*{x}+({float(v)!r}))'
    return expression


def _invnorm_branches(p):
    q='q'
    tail=f'({_poly(C,q)})/({_poly(D+(1.,),q)})'
    middle=f'({_poly(A,"z2")}*z)/({_poly(B+(1.,),"z2")})'
    return tail,middle


def _normal(lang,fn):
    tail,mid=_invnorm_branches('p')
    note='HyunCalculator STAT-001: output [Z, PDF, CDF, survival, inverse-CDF]. Normal-CDF approximation abs error usually < 8e-8; PPF uses Acklam (~1e-9).'
    if lang in ('C','C++','JavaScript','TypeScript','Java','C#'):
        math={'C':('sqrt','log','exp','fabs','isfinite'),
              'C++':('std::sqrt','std::log','std::exp','std::fabs','std::isfinite'),
              'JavaScript':('Math.sqrt','Math.log','Math.exp','Math.abs','Number.isFinite'),
              'TypeScript':('Math.sqrt','Math.log','Math.exp','Math.abs','Number.isFinite'),
              'Java':('Math.sqrt','Math.log','Math.exp','Math.abs','Double.isFinite'),
              'C#':('Math.Sqrt','Math.Log','Math.Exp','Math.Abs','double.IsFinite')}[lang]
        sqrt,log,exp,ab,finite=math
        pp=f'''    double z=0, q=0, z2=0;
    if(p<0.02425) {{ q={sqrt}(-2*{log}(p)); z={tail}; }}
    else if(p>0.97575) {{ q={sqrt}(-2*{log}(1-p)); z=-({tail}); }}
    else {{ z=p-0.5; z2=z*z; z={mid}; }}
    return z;'''
        qq=f'''    const p0=1/(1+0.2316419*{ab}(z));
    const tail=0.3989422804014327*{exp}(-0.5*z*z)*p0*(0.319381530+p0*(-0.356563782+p0*(1.781477937+p0*(-1.821255978+p0*1.330274429))));
    return z>=0 ? 1-tail : tail;'''
        if lang in ('C','C++','Java','C#'):
            qq=qq.replace('const p0=', 'double p0=').replace('const tail=', 'double tail=')
        if lang in ('JavaScript','TypeScript'):
            pp=pp.replace('double z=', 'let z=').replace('q=0, z2=0;', 'q=0, z2=0;')
        guard=f'!{finite}(x)||!{finite}(mean)||!{finite}(sd)||!{finite}(p)||sd<=0||p<=0||p>=1'
        if lang=='C':
            return f'''/* {note} */
#include <math.h>
typedef struct {{ double values[5]; }} HyunNormalResult;
static double hyun_{fn}_ppf(double p) {{\n{pp}\n}}
static double hyun_{fn}_cdf(double z) {{\n{qq}\n}}
HyunNormalResult {fn}(double x,double mean,double sd,double p) {{
    HyunNormalResult fail={{{{NAN,NAN,NAN,NAN,NAN}}}};
    if({guard}) return fail;
    double z=(x-mean)/sd;
    double density={exp}(-0.5*z*z)*0.3989422804014327/sd;
    double cdf=hyun_{fn}_cdf(z);
    HyunNormalResult result={{{{z,density,cdf,1-cdf,mean+sd*hyun_{fn}_ppf(p)}}}};
    return result;
}}
'''
        if lang=='C++':
            return f'''// {note}
#include <array>
#include <cmath>
#include <stdexcept>
static double hyun_{fn}_ppf(double p) {{\n{pp}\n}}
static double hyun_{fn}_cdf(double z) {{\n{qq}\n}}
std::array<double,5> {fn}(double x,double mean,double sd,double p) {{
    if({guard}) throw std::invalid_argument("Invalid normal inputs");
    double z=(x-mean)/sd;
    double density={exp}(-0.5*z*z)*0.3989422804014327/sd;
    double cdf=hyun_{fn}_cdf(z);
    return {{z,density,cdf,1-cdf,mean+sd*hyun_{fn}_ppf(p)}};
}}
'''
        if lang in ('JavaScript','TypeScript'):
            ret=': number' if lang=='TypeScript' else ''
            par='p: number' if lang=='TypeScript' else 'p'
            args='x: number, mean: number, sd: number, p: number' if lang=='TypeScript' else 'x, mean, sd, p'
            return f'''// {note}
function hyun_{fn}_ppf({par}){ret} {{\n{pp}\n}}
function hyun_{fn}_cdf(z{': number' if lang=='TypeScript' else ''}){ret} {{\n{qq}\n}}
export function {fn}({args}){': number[]' if lang=='TypeScript' else ''} {{
    if({guard}) throw new RangeError("Invalid normal inputs");
    const z=(x-mean)/sd;
    const density={exp}(-0.5*z*z)*0.3989422804014327/sd;
    const cdf=hyun_{fn}_cdf(z);
    return [z,density,cdf,1-cdf,mean+sd*hyun_{fn}_ppf(p)];
}}
'''
        if lang=='Java':
            return f'''// {note}
public class GeneratedCalculator {{
  private static double hyun_{fn}_ppf(double p) {{\n{pp}\n  }}
  private static double hyun_{fn}_cdf(double z) {{\n{qq}\n  }}
  public static double[] {fn}(double x,double mean,double sd,double p) {{
    if({guard}) throw new IllegalArgumentException("Invalid normal inputs");
    double z=(x-mean)/sd;
    double density={exp}(-0.5*z*z)*0.3989422804014327/sd;
    double cdf=hyun_{fn}_cdf(z);
    return new double[] {{z,density,cdf,1-cdf,mean+sd*hyun_{fn}_ppf(p)}};
  }}
}}
'''
        if lang=='C#':
            return f'''// {note}
using System;
public static class GeneratedCalculator {{
  private static double hyun_{fn}_ppf(double p) {{\n{pp}\n  }}
  private static double hyun_{fn}_cdf(double z) {{\n{qq}\n  }}
  public static double[] {fn}(double x,double mean,double sd,double p) {{
    if({guard}) throw new ArgumentException("Invalid normal inputs");
    double z=(x-mean)/sd;
    double density={exp}(-0.5*z*z)*0.3989422804014327/sd;
    double cdf=hyun_{fn}_cdf(z);
    return new [] {{z,density,cdf,1-cdf,mean+sd*hyun_{fn}_ppf(p)}};
  }}
}}
'''
    if lang=='Swift':
        return f'''// {note}
import Foundation
private func hyun_{fn}_ppf(_ p:Double)->Double {{
  var z=0.0, q=0.0, z2=0.0
  if p<0.02425 {{ q=sqrt(-2*log(p)); z={tail} }}
  else if p>0.97575 {{ q=sqrt(-2*log(1-p)); z = -({tail}) }}
  else {{ z=p-0.5; z2=z*z; z={mid} }}
  return z
}}
private func hyun_{fn}_cdf(_ z:Double)->Double {{
  let t=1/(1+0.2316419*abs(z))
  let tail=0.3989422804014327*exp(-0.5*z*z)*t*(0.319381530+t*(-0.356563782+t*(1.781477937+t*(-1.821255978+t*1.330274429))))
  return z>=0 ? 1-tail : tail
}}
func {fn}(_ x:Double,_ mean:Double,_ sd:Double,_ p:Double)->[Double] {{
  if !x.isFinite || !mean.isFinite || !sd.isFinite || !p.isFinite || sd<=0 || p<=0 || p>=1 {{return Array(repeating:Double.nan,count:5)}}
  let z=(x-mean)/sd
  let density=exp(-0.5*z*z)*0.3989422804014327/sd
  let cdf=hyun_{fn}_cdf(z)
  return [z,density,cdf,1-cdf,mean+sd*hyun_{fn}_ppf(p)]
}}
'''
    if lang=='Kotlin':
        return f'''// {note}
import kotlin.math.*
private fun hyun_{fn}_ppf(p:Double):Double {{
  var z=0.0; var q=0.0; var z2=0.0
  if(p<0.02425){{q=sqrt(-2*ln(p));z={tail}}}
  else if(p>0.97575){{q=sqrt(-2*ln(1-p));z = -({tail})}}
  else{{z=p-0.5;z2=z*z;z={mid}}}
  return z
}}
private fun hyun_{fn}_cdf(z:Double):Double {{
  val t=1/(1+0.2316419*abs(z))
  val tail=0.3989422804014327*exp(-0.5*z*z)*t*(0.319381530+t*(-0.356563782+t*(1.781477937+t*(-1.821255978+t*1.330274429))))
  return if(z>=0) 1-tail else tail
}}
fun {fn}(x:Double,mean:Double,sd:Double,p:Double):DoubleArray {{
  if(!x.isFinite()||!mean.isFinite()||!sd.isFinite()||!p.isFinite()||sd<=0||p<=0||p>=1)throw IllegalArgumentException("Invalid normal inputs")
  val z=(x-mean)/sd; val density=exp(-0.5*z*z)*0.3989422804014327/sd; val cdf=hyun_{fn}_cdf(z)
  return doubleArrayOf(z,density,cdf,1-cdf,mean+sd*hyun_{fn}_ppf(p))
}}
'''
    if lang=='Go':
        return f'''// {note}
package main
import "math"
func hyun_{fn}_ppf(p float64)float64 {{
  var z,q,z2 float64
  if p<0.02425 {{q=math.Sqrt(-2*math.Log(p)); z={tail}}} else if p>0.97575 {{q=math.Sqrt(-2*math.Log(1-p));z = -({tail})}} else {{z=p-0.5;z2=z*z;z={mid}}}
  return z
}}
func hyun_{fn}_cdf(z float64)float64 {{
  t:=1/(1+0.2316419*math.Abs(z))
  tail:=0.3989422804014327*math.Exp(-0.5*z*z)*t*(0.319381530+t*(-0.356563782+t*(1.781477937+t*(-1.821255978+t*1.330274429))))
  if z>=0 {{return 1-tail}}; return tail
}}
func {fn}(x,mean,sd,p float64)[5]float64 {{
  invalid:=[5]float64{{math.NaN(),math.NaN(),math.NaN(),math.NaN(),math.NaN()}}
  if math.IsNaN(x)||math.IsInf(x,0)||math.IsNaN(mean)||math.IsInf(mean,0)||math.IsNaN(sd)||math.IsInf(sd,0)||math.IsNaN(p)||math.IsInf(p,0)||sd<=0||p<=0||p>=1 {{return invalid}}
  z:=(x-mean)/sd;density:=math.Exp(-0.5*z*z)*0.3989422804014327/sd;cdf:=hyun_{fn}_cdf(z)
  return [5]float64{{z,density,cdf,1-cdf,mean+sd*hyun_{fn}_ppf(p)}}
}}
'''
    if lang=='Rust':
        return f'''// {note}
fn hyun_{fn}_ppf(p:f64)->f64 {{
  let mut z:f64=0.0;let mut q:f64;let mut z2:f64;
  if p<0.02425 {{q=(-2.0*p.ln()).sqrt();z={tail};}}
  else if p>0.97575 {{q=(-2.0*(1.0-p).ln()).sqrt();z = -({tail});}}
  else {{z=p-0.5;z2=z*z;z={mid};}}
  z
}}
fn hyun_{fn}_cdf(z:f64)->f64 {{
  let t=1.0/(1.0+0.2316419*z.abs());
  let tail=0.3989422804014327*(-0.5*z*z).exp()*t*(0.319381530+t*(-0.356563782+t*(1.781477937+t*(-1.821255978+t*1.330274429))));
  if z>=0.0 {{1.0-tail}}else{{tail}}
}}
pub fn {fn}(x:f64,mean:f64,sd:f64,p:f64)->[f64;5] {{
  if !x.is_finite()||!mean.is_finite()||!sd.is_finite()||!p.is_finite()||sd<=0.0||p<=0.0||p>=1.0 {{return [f64::NAN;5]}}
  let z=(x-mean)/sd;let density=(-0.5*z*z).exp()*0.3989422804014327/sd;let cdf=hyun_{fn}_cdf(z);
  [z,density,cdf,1.0-cdf,mean+sd*hyun_{fn}_ppf(p)]
}}
'''
    if lang=='R':
        return f'''# {note}
hyun_{fn}_ppf <- function(p) {{
  z<-0; q<-0;z2<-0
  if(p<0.02425){{q<-sqrt(-2*log(p));z<-{tail}}} else if(p>0.97575){{q<-sqrt(-2*log(1-p));z<- -({tail})}} else{{z<-p-0.5;z2<-z*z;z<-{mid}}}
  z
}}
hyun_{fn}_cdf <- function(z){{
  t<-1/(1+0.2316419*abs(z));tail<-0.3989422804014327*exp(-0.5*z*z)*t*(0.319381530+t*(-0.356563782+t*(1.781477937+t*(-1.821255978+t*1.330274429))))
  if(z>=0)1-tail else tail
}}
{fn} <- function(x,mean,sd,p){{
  if(length(x)!=1||length(mean)!=1||length(sd)!=1||length(p)!=1||any(!is.finite(c(x,mean,sd,p)))||sd<=0||p<=0||p>=1)stop("Invalid normal inputs")
  z<-(x-mean)/sd;density<-exp(-0.5*z*z)*0.3989422804014327/sd;cdf<-hyun_{fn}_cdf(z)
  return(c(Z=z,PDF=density,CDF=cdf,Survival=1-cdf,Quantile=mean+sd*hyun_{fn}_ppf(p)))
}}
'''
    if lang=='MATLAB':
        return f'''% {note}
function result={fn}(x,mean,sd,p)
  if any(~isfinite([x,mean,sd,p]))||~isscalar(x)||~isscalar(mean)||~isscalar(sd)||~isscalar(p)||sd<=0||p<=0||p>=1
    error('Invalid normal inputs');
  end
  z=(x-mean)/sd;density=exp(-0.5*z*z)*0.3989422804014327/sd;cdf=hyun_cdf(z);
  result=[z,density,cdf,1-cdf,mean+sd*hyun_ppf(p)];
end
function val=hyun_cdf(z)
  t=1/(1+0.2316419*abs(z));tail=0.3989422804014327*exp(-0.5*z*z)*t*(0.319381530+t*(-0.356563782+t*(1.781477937+t*(-1.821255978+t*1.330274429))));
  if z>=0,val=1-tail;else,val=tail;end
end
function z=hyun_ppf(p)
  z=0;q=0;z2=0;
  if p<0.02425,q=sqrt(-2*log(p));z={tail};elseif p>0.97575,q=sqrt(-2*log(1-p));z=-({tail});else,z=p-0.5;z2=z*z;z={mid};end
end
'''
    if lang=='Julia':
        mid_julia = re.sub(r'\bz\b', 'zi', mid)
        return f'''# {note}
function {fn}(x,mean,sd,p)
  if !all(isfinite,(x,mean,sd,p)) || sd<=0 || p<=0 || p>=1
    throw(ArgumentError("Invalid normal inputs"))
  end
  z=(x-mean)/sd;density=exp(-0.5*z*z)*0.3989422804014327/sd
  t=1/(1+0.2316419*abs(z));tail=0.3989422804014327*exp(-0.5*z*z)*t*(0.319381530+t*(-0.356563782+t*(1.781477937+t*(-1.821255978+t*1.330274429))))
  cdf=z>=0 ? 1-tail : tail
  q=0.0;z2=0.0;zi=0.0
  if p<0.02425
    q=sqrt(-2*log(p));zi={tail}
  elseif p>0.97575
    q=sqrt(-2*log(1-p));zi=-({tail})
  else
    zi=p-0.5;z2=zi*zi;zi={mid_julia}
  end
  return (Z=z,PDF=density,CDF=cdf,Survival=1-cdf,Quantile=mean+sd*zi)
end
'''
    raise ValueError('Unsupported language '+lang)



def _cov(lang,fn):
    note=('HyunCalculator STAT-002: sample covariance (ddof=1), correlation. '
          'Input rows=observations, columns=assets; output flat row-major '
          '[cov(n*n), corr(n*n)], NaN correlation for zero variance.')
    if lang=='C':
        return f'''/* {note} */
#include <math.h>
#include <stdlib.h>
#include <stddef.h>
/* data is row-major rows*cols. result must hold >=2*cols*cols doubles.
   Returns 1 success, 0 invalid input. Caller owns result buffer. */
int {fn}(const double *data,size_t rows,size_t cols,double *result,size_t capacity) {{
  if(!data||!result||rows<3||cols<2||cols>128||rows>100000||capacity<2*cols*cols) return 0;
  double *avg=(double*)calloc(cols,sizeof(double));
  if(!avg) return 0;
  for(size_t i=0;i<rows;i++)for(size_t j=0;j<cols;j++){{
    double v=data[i*cols+j];if(!isfinite(v)){{free(avg);return 0;}}
    avg[j]+=v/rows;
  }}
  for(size_t j=0;j<cols;j++)for(size_t k=0;k<cols;k++){{
    double sum=0;
    for(size_t i=0;i<rows;i++)sum+=(data[i*cols+j]-avg[j])*(data[i*cols+k]-avg[k]);
    result[j*cols+k]=sum/(rows-1);
  }}
  for(size_t j=0;j<cols;j++)for(size_t k=0;k<cols;k++){{
    double denom=sqrt(result[j*cols+j])*sqrt(result[k*cols+k]);
    result[cols*cols+j*cols+k]=denom>0?result[j*cols+k]/denom:NAN;
  }}
  free(avg);return 1;
}}
'''
    if lang=='C++':
        return f'''// {note}
#include <vector>
#include <cmath>
#include <stdexcept>
std::vector<double> {fn}(const std::vector<std::vector<double>>& data) {{
  const size_t rows=data.size();if(rows<3||rows>100000)throw std::invalid_argument("Invalid row count");
  const size_t cols=data.front().size();if(cols<2||cols>128)throw std::invalid_argument("Invalid column count");
  std::vector<double> avg(cols,0),result(2*cols*cols,0);
  for(const auto& row:data){{if(row.size()!=cols)throw std::invalid_argument("Ragged rows");for(size_t j=0;j<cols;j++){{if(!std::isfinite(row[j]))throw std::invalid_argument("Nonfinite input");avg[j]+=row[j]/rows;}}}}
  for(size_t j=0;j<cols;j++)for(size_t k=0;k<cols;k++){{double sum=0;for(size_t i=0;i<rows;i++)sum+=(data[i][j]-avg[j])*(data[i][k]-avg[k]);result[j*cols+k]=sum/(rows-1);}}
  for(size_t j=0;j<cols;j++)for(size_t k=0;k<cols;k++){{double denom=std::sqrt(result[j*cols+j])*std::sqrt(result[k*cols+k]);result[cols*cols+j*cols+k]=denom>0?result[j*cols+k]/denom:NAN;}}
  return result;
}}
'''
    if lang in ('JavaScript','TypeScript'):
        arg='data: number[][]' if lang=='TypeScript' else 'data'
        ret=': number[]' if lang=='TypeScript' else ''
        return f'''// {note}
export function {fn}({arg}){ret} {{
  if(!Array.isArray(data)||data.length<3||data.length>100000)throw new RangeError("Invalid row count");
  const rows=data.length,cols=data[0]?.length;
  if(!Number.isInteger(cols)||cols<2||cols>128)throw new RangeError("Invalid columns");
  const avg=Array(cols).fill(0),result=Array(2*cols*cols).fill(0);
  for(let i=0;i<rows;i++){{if(!Array.isArray(data[i])||data[i].length!==cols||!data[i].every(Number.isFinite))throw new RangeError("Invalid row");for(let j=0;j<cols;j++)avg[j]+=data[i][j]/rows;}}
  for(let j=0;j<cols;j++)for(let k=0;k<cols;k++){{let sum=0;for(let i=0;i<rows;i++)sum+=(data[i][j]-avg[j])*(data[i][k]-avg[k]);result[j*cols+k]=sum/(rows-1);}}
  for(let j=0;j<cols;j++)for(let k=0;k<cols;k++){{const d=Math.sqrt(result[j*cols+j])*Math.sqrt(result[k*cols+k]);result[cols*cols+j*cols+k]=d>0?result[j*cols+k]/d:NaN;}}
  return result;
}}
'''
    if lang=='Java':
        return f'''// {note}
public class GeneratedCalculator {{
  public static double[] {fn}(double[][] data) {{
    if(data==null||data.length<3||data.length>100000||data[0]==null)throw new IllegalArgumentException("Invalid rows");
    int rows=data.length,cols=data[0].length;if(cols<2||cols>128)throw new IllegalArgumentException("Invalid columns");
    double[] avg=new double[cols],result=new double[2*cols*cols];
    for(double[] row:data){{if(row==null||row.length!=cols)throw new IllegalArgumentException("Ragged data");for(int j=0;j<cols;j++){{if(!Double.isFinite(row[j]))throw new IllegalArgumentException("Nonfinite");avg[j]+=row[j]/rows;}}}}
    for(int j=0;j<cols;j++)for(int k=0;k<cols;k++){{double sum=0;for(int i=0;i<rows;i++)sum+=(data[i][j]-avg[j])*(data[i][k]-avg[k]);result[j*cols+k]=sum/(rows-1);}}
    for(int j=0;j<cols;j++)for(int k=0;k<cols;k++){{double d=Math.sqrt(result[j*cols+j])*Math.sqrt(result[k*cols+k]);result[cols*cols+j*cols+k]=d>0?result[j*cols+k]/d:Double.NaN;}}
    return result;
  }}
}}
'''
    if lang=='C#':
        return f'''// {note}
using System;
public static class GeneratedCalculator {{
  public static double[] {fn}(double[][] data) {{
    if(data==null||data.Length<3||data.Length>100000||data[0]==null)throw new ArgumentException("Invalid rows");
    int rows=data.Length,cols=data[0].Length;if(cols<2||cols>128)throw new ArgumentException("Invalid columns");
    double[] avg=new double[cols],result=new double[2*cols*cols];
    foreach(var row in data){{if(row==null||row.Length!=cols)throw new ArgumentException("Ragged data");for(int j=0;j<cols;j++){{if(!double.IsFinite(row[j]))throw new ArgumentException("Nonfinite");avg[j]+=row[j]/rows;}}}}
    for(int j=0;j<cols;j++)for(int k=0;k<cols;k++){{double sum=0;for(int i=0;i<rows;i++)sum+=(data[i][j]-avg[j])*(data[i][k]-avg[k]);result[j*cols+k]=sum/(rows-1);}}
    for(int j=0;j<cols;j++)for(int k=0;k<cols;k++){{double d=Math.Sqrt(result[j*cols+j])*Math.Sqrt(result[k*cols+k]);result[cols*cols+j*cols+k]=d>0?result[j*cols+k]/d:double.NaN;}}
    return result;
  }}
}}
'''
    if lang=='Swift':
        return f'''// {note}
import Foundation
func {fn}(_ data:[[Double]])->[Double] {{
  let rows=data.count
  if rows<3 || rows>100000 {{return []}}
  let cols=data[0].count
  if cols<2 || cols>128 {{return []}}
  var avg=[Double](repeating:0,count:cols),result=[Double](repeating:0,count:2*cols*cols)
  for row in data {{
    if row.count != cols || !row.allSatisfy({{$0.isFinite}}) {{return []}}
    for j in 0..<cols {{avg[j]+=row[j]/Double(rows)}}
  }}
  for j in 0..<cols {{for k in 0..<cols {{
    var sum=0.0
    for i in 0..<rows {{sum+=(data[i][j]-avg[j])*(data[i][k]-avg[k])}}
    result[j*cols+k]=sum/Double(rows-1)
  }}}}
  for j in 0..<cols {{for k in 0..<cols {{
    let d=sqrt(result[j*cols+j])*sqrt(result[k*cols+k])
    result[cols*cols+j*cols+k]=d>0 ? result[j*cols+k]/d : Double.nan
  }}}}
  return result
}}
'''
    if lang=='Kotlin':
        return f'''// {note}
import kotlin.math.*
fun {fn}(data:Array<DoubleArray>):DoubleArray {{
  val rows=data.size;require(rows in 3..100000)
  val cols=data[0].size;require(cols in 2..128)
  val avg=DoubleArray(cols);val result=DoubleArray(2*cols*cols)
  for(row in data){{require(row.size==cols && row.all{{it.isFinite()}});for(j in 0 until cols)avg[j]+=row[j]/rows}}
  for(j in 0 until cols)for(k in 0 until cols){{var sum=0.0;for(i in 0 until rows)sum+=(data[i][j]-avg[j])*(data[i][k]-avg[k]);result[j*cols+k]=sum/(rows-1)}}
  for(j in 0 until cols)for(k in 0 until cols){{val d=sqrt(result[j*cols+j])*sqrt(result[k*cols+k]);result[cols*cols+j*cols+k]=if(d>0)result[j*cols+k]/d else Double.NaN}}
  return result
}}
'''
    if lang=='Go':
        return f'''// {note}
package main
import "math"
func {fn}(data [][]float64)[]float64 {{
  rows:=len(data);if rows<3||rows>100000{{return nil}}
  cols:=len(data[0]);if cols<2||cols>128{{return nil}}
  avg:=make([]float64,cols);result:=make([]float64,2*cols*cols)
  for _,row:=range data{{if len(row)!=cols{{return nil}};for j,v:=range row{{if math.IsNaN(v)||math.IsInf(v,0){{return nil}};avg[j]+=v/float64(rows)}}}}
  for j:=0;j<cols;j++{{for k:=0;k<cols;k++{{sum:=0.0;for i:=0;i<rows;i++{{sum+=(data[i][j]-avg[j])*(data[i][k]-avg[k])}};result[j*cols+k]=sum/float64(rows-1)}}}}
  for j:=0;j<cols;j++{{for k:=0;k<cols;k++{{d:=math.Sqrt(result[j*cols+j])*math.Sqrt(result[k*cols+k]);if d>0{{result[cols*cols+j*cols+k]=result[j*cols+k]/d}}else{{result[cols*cols+j*cols+k]=math.NaN()}}}}}}
  return result
}}
'''
    if lang=='Rust':
        return f'''// {note}
pub fn {fn}(data:&[Vec<f64>])->Vec<f64> {{
  let rows=data.len();if rows<3||rows>100000{{return vec![];}}
  let cols=data[0].len();if cols<2||cols>128{{return vec![];}}
  let mut avg=vec![0.0;cols];let mut result=vec![0.0;2*cols*cols];
  for row in data{{if row.len()!=cols || !row.iter().all(|x|x.is_finite()){{return vec![];}}for j in 0..cols{{avg[j]+=row[j]/rows as f64;}}}}
  for j in 0..cols{{for k in 0..cols{{let mut sum=0.0;for i in 0..rows{{sum+=(data[i][j]-avg[j])*(data[i][k]-avg[k]);}}result[j*cols+k]=sum/((rows-1) as f64);}}}}
  for j in 0..cols{{for k in 0..cols{{let d=result[j*cols+j].sqrt()*result[k*cols+k].sqrt();result[cols*cols+j*cols+k]=if d>0.0{{result[j*cols+k]/d}}else{{f64::NAN}};}}}}
  result
}}
'''
    if lang=='R':
        return f'''# {note}
{fn} <- function(data) {{
  if(!is.matrix(data)||nrow(data)<3||ncol(data)<2||nrow(data)>100000||ncol(data)>128||any(!is.finite(data)))stop("Invalid return matrix")
  rows<-nrow(data); cols<-ncol(data); avg<-colMeans(data); cov<-matrix(0,cols,cols);corr<-matrix(0,cols,cols)
  for(j in seq_len(cols))for(k in seq_len(cols))cov[j,k]<-sum((data[,j]-avg[j])*(data[,k]-avg[k]))/(rows-1)
  for(j in seq_len(cols))for(k in seq_len(cols)){{denom<-sqrt(cov[j,j])*sqrt(cov[k,k]);corr[j,k]<-if(denom>0)cov[j,k]/denom else NaN}}
  return(c(as.vector(t(cov)),as.vector(t(corr))))
}}
'''
    if lang=='MATLAB':
        return f'''% {note}
function result={fn}(data)
  [rows,cols]=size(data);
  if rows<3||cols<2||rows>100000||cols>128||any(~isfinite(data(:)))
    error('Invalid return matrix');
  end
  avg=mean(data,1);cv=zeros(cols,cols);cr=zeros(cols,cols);
  for j=1:cols
    for k=1:cols
      cv(j,k)=sum((data(:,j)-avg(j)).*(data(:,k)-avg(k)))/(rows-1);
    end
  end
  for j=1:cols
    for k=1:cols
      d=sqrt(cv(j,j))*sqrt(cv(k,k));
      if d>0,cr(j,k)=cv(j,k)/d;else,cr(j,k)=NaN;end
    end
  end
  result=[reshape(cv.',1,[]),reshape(cr.',1,[])];
end
'''
    if lang=='Julia':
        return f'''# {note}
function {fn}(data)
  rows,cols=size(data)
  if rows<3 || cols<2 || rows>100000 || cols>128 || !all(isfinite,data)
    throw(ArgumentError("Invalid return matrix"))
  end
  avg=vec(sum(data,dims=1))/rows;cv=zeros(cols,cols);cr=zeros(cols,cols)
  for j in 1:cols,k in 1:cols
    cv[j,k]=sum((data[i,j]-avg[j])*(data[i,k]-avg[k]) for i in 1:rows)/(rows-1)
  end
  for j in 1:cols,k in 1:cols
    d=sqrt(cv[j,j])*sqrt(cv[k,k]);cr[j,k]=d>0 ? cv[j,k]/d : NaN
  end
  return vcat(vec(permutedims(cv)),vec(permutedims(cr)))
end
'''
    raise ValueError('Unsupported language '+lang)


# Replacement for the earlier qf_normal-only dispatch above; both statistical
# profiles run through the same input-validation and language-specific emitters.
def generate_stats(fn,formula,options):
    from .emitter import GenerationError
    if options.language=='Python':raise GenerationError('Python uses reference code emitter')
    if options.structure!='function' or options.iteration!='auto' or options.variable_names or options.variant!='periodic' or options.imports not in ('auto','standard'):
        raise GenerationError('Statistical generator only supports function, auto iteration, standard imports and canonical names')
    if formula.function=='qf_normal':return _normal(options.language,fn)
    if formula.function=='qf_cov':return _cov(options.language,fn)
    raise GenerationError('Unsupported statistical formula')
