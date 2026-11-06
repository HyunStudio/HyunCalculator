"""Standalone portfolio expected return, volatility and Sharpe emitter.

Compatible with the established qf_portfolio inputs and outputs. Numerical
validation checks finite arrays, symmetry and positive definiteness (Cholesky).
For C, covariance uses a flattened *row-major* n*n buffer; all other targets
accept native 2D matrices. No dependency on third-party math packages.
"""
from __future__ import annotations
from .emitter import GenerationError

SUPPORTED = frozenset({'qf_portfolio'})


def generate_portfolio(fn, form, options):
    if options.language == 'Python': raise GenerationError('Python uses complete reference emitter')
    if options.structure != 'function' or options.iteration != 'auto' or options.variable_names or options.variant != 'periodic':
        raise GenerationError('Portfolio adapter supports function/auto and canonical argument names only')
    l = options.language
    note = 'HyunCalculator PORT-001: [Expected return, Volatility, Sharpe ratio]. Covariance SPD; weights sum to 1.'
    if l == 'R':
        return f'''# {note}
{fn} <- function(w, mu, cov, rf=0) {{
  n<-length(w)
  if(n<2 || length(mu)!=n || !is.matrix(cov) || !all(dim(cov)==c(n,n)) || any(!is.finite(w)) || any(!is.finite(mu)) || any(!is.finite(cov)) || !is.finite(rf))stop("Invalid portfolio inputs")
  if(abs(sum(w)-1)>1.001e-5 || any(abs(cov-t(cov)) > (1e-9+1e-5*abs(t(cov)))))stop("Invalid portfolio weights/covariance")
  if(inherits(try(chol(cov),silent=TRUE),"try-error"))stop("Covariance must be positive definite")
  ret<-sum(w*mu);variance<-as.numeric(t(w)%*%cov%*%w)
  vol<-sqrt(max(variance,0));return(c(ExpectedReturn=ret,Volatility=vol,Sharpe=if(vol>0)(ret-rf)/vol else NaN))
}}
'''
    if l == 'MATLAB':
        return f'''% {note}
function result = {fn}(w,mu,cov,rf)
  n=numel(w);
  if n<2 || numel(mu)~=n || ~isequal(size(cov),[n,n]) || any(~isfinite(w)) || any(~isfinite(mu)) || any(~isfinite(cov(:))) || ~isscalar(rf) || ~isfinite(rf)
    error('Invalid portfolio inputs');
  end
  w=w(:);mu=mu(:);
  if abs(sum(w)-1)>1.001e-5 || any(any(abs(cov-cov')>1e-9+1e-5*abs(cov')))
    error('Invalid weights or symmetry');
  end
  [~,pd]=chol(cov);if pd~=0,error('Covariance not SPD');end
  ret=w'*mu;var=w'*cov*w;vol=sqrt(max(var,0));
  ratio=NaN;if vol>0,ratio=(ret-rf)/vol;end
  result=[ret,vol,ratio];
end
'''
    if l == 'Julia':
        return f'''# {note}
using LinearAlgebra
function {fn}(w,mu,cov,rf=0.0)
  n=length(w)
  if n<2 || length(mu)!=n || size(cov)!=(n,n) || !all(isfinite,w) || !all(isfinite,mu) || !all(isfinite,cov) || !isfinite(rf)
    throw(ArgumentError("Invalid portfolio inputs"))
  end
  if abs(sum(w)-1)>1.001e-5 || any(abs.(cov-cov') .> 1e-9 .+ 1e-5 .*abs.(cov'))
    throw(ArgumentError("Invalid weights or covariance symmetry"))
  end
  isposdef(Symmetric(cov)) || throw(ArgumentError("Covariance not SPD"))
  ret=dot(w,mu);vol=sqrt(max(dot(w,cov*w),0))
  return (ExpectedReturn=ret,Volatility=vol,Sharpe=vol>0 ? (ret-rf)/vol : NaN)
end
'''
    if l == 'C':
        return f'''/* {note} cov is row-major n*n. */
#include <math.h>
#include <stddef.h>
#include <stdlib.h>
typedef struct {{double values[3];}} HyunResult;
HyunResult {fn}(const double* w,const double* mu,const double* cov,size_t n,double rf){{
  HyunResult fail={{{{NAN,NAN,NAN}}}};
  if(!w||!mu||!cov||n<2||n>2048||!isfinite(rf))return fail;
  double weight_sum=0,ret=0,variance=0;
  for(size_t i=0;i<n;i++){{
    if(!isfinite(w[i])||!isfinite(mu[i]))return fail;
    weight_sum+=w[i];ret+=w[i]*mu[i];
    for(size_t j=0;j<n;j++){{
      if(!isfinite(cov[i*n+j]))return fail;
      variance+=w[i]*cov[i*n+j]*w[j];
    }}
  }}
  if(fabs(weight_sum-1)>1.001e-5)return fail;
  double *cholesky=(double*)calloc(n*n,sizeof(double));if(!cholesky)return fail;
  int valid=1;
  for(size_t i=0;i<n&&valid;i++){{
    for(size_t j=0;j<n;j++)if(fabs(cov[i*n+j]-cov[j*n+i])>1e-9+1e-5*fabs(cov[j*n+i])){{valid=0;break;}}
    for(size_t j=0;j<=i&&valid;j++){{
      double v=cov[i*n+j];for(size_t k=0;k<j;k++)v-=cholesky[i*n+k]*cholesky[j*n+k];
      if(i==j){{if(v<=1e-12){{valid=0;break;}}cholesky[i*n+j]=sqrt(v);}}
      else cholesky[i*n+j]=v/cholesky[j*n+j];
    }}
  }}
  free(cholesky);if(!valid||!isfinite(variance))return fail;
  double vol=sqrt(fmax(variance,0));HyunResult out={{{{ret,vol,vol>0?(ret-rf)/vol:NAN}}}};return out;
}}
'''
    if l == 'C++':
        return f'''// {note}
#include <cmath>
#include <array>
#include <stdexcept>
#include <vector>
std::array<double,3> {fn}(const std::vector<double>& w,const std::vector<double>& mu,const std::vector<std::vector<double>>& cov,double rf=0){{
  const size_t n=w.size();if(n<2||mu.size()!=n||cov.size()!=n||!std::isfinite(rf))throw std::invalid_argument("Invalid portfolio shape");
  double total=0,ret=0,variance=0;
  for(size_t i=0;i<n;i++){{
    if(!std::isfinite(w[i])||!std::isfinite(mu[i])||cov[i].size()!=n)throw std::invalid_argument("Invalid portfolio arrays");
    total+=w[i];ret+=w[i]*mu[i];
    for(size_t j=0;j<n;j++){{if(!std::isfinite(cov[i][j]))throw std::invalid_argument("Nonfinite covariance");variance+=w[i]*cov[i][j]*w[j];}}
  }}
  if(std::abs(total-1)>1.001e-5)throw std::invalid_argument("Weights must sum to 1");
  std::vector<std::vector<double>> lower(n,std::vector<double>(n,0));
  for(size_t i=0;i<n;i++){{
    for(size_t j=0;j<n;j++)if(std::abs(cov[i][j]-cov[j][i])>1e-9+1e-5*std::abs(cov[j][i]))throw std::invalid_argument("Asymmetric covariance");
    for(size_t j=0;j<=i;j++){{double v=cov[i][j];for(size_t k=0;k<j;k++)v-=lower[i][k]*lower[j][k];
      if(i==j){{if(!(v>1e-12))throw std::invalid_argument("Non SPD covariance");lower[i][j]=std::sqrt(v);}}
      else lower[i][j]=v/lower[j][j];}}
  }}
  double vol=std::sqrt(std::max(variance,0.0));return {{ret,vol,vol>0?(ret-rf)/vol:NAN}};
}}
'''
    if l in ('JavaScript','TypeScript'):
        p='w: number[], mu: number[], cov: number[][], rf: number=0' if l=='TypeScript' else 'w, mu, cov, rf=0'
        ret=': number[]' if l=='TypeScript' else ''
        return f'''// {note}
export function {fn}({p}){ret} {{
  const n=w?.length;
  if(!Array.isArray(w)||n<2||!Array.isArray(mu)||mu.length!==n||!Array.isArray(cov)||cov.length!==n||!Number.isFinite(rf))throw new RangeError("Invalid portfolio shape");
  let total=0,ret=0,variance=0;
  for(let i=0;i<n;i++){{
    if(!Number.isFinite(w[i])||!Number.isFinite(mu[i])||!Array.isArray(cov[i])||cov[i].length!==n)throw new RangeError("Invalid portfolio arrays");
    total+=w[i];ret+=w[i]*mu[i];
    for(let j=0;j<n;j++){{if(!Number.isFinite(cov[i][j]))throw new RangeError("Nonfinite covariance");variance+=w[i]*cov[i][j]*w[j];}}
  }}
  if(Math.abs(total-1)>1.001e-5)throw new RangeError("Invalid weights");
  const lower=Array.from({{length:n}},()=>new Array(n).fill(0));
  for(let i=0;i<n;i++){{
    for(let j=0;j<n;j++)if(Math.abs(cov[i][j]-cov[j][i])>1e-9+1e-5*Math.abs(cov[j][i]))throw new RangeError("Asymmetric covariance");
    for(let j=0;j<=i;j++){{let v=cov[i][j];for(let k=0;k<j;k++)v-=lower[i][k]*lower[j][k];
      if(i===j){{if(!(v>1e-12))throw new RangeError("Non SPD covariance");lower[i][j]=Math.sqrt(v);}}
      else lower[i][j]=v/lower[j][j];}}
  }}
  const vol=Math.sqrt(Math.max(variance,0));return [ret,vol,vol>0?(ret-rf)/vol:NaN];
}}
'''
    if l == 'Java':
        return f'''// {note}
public class GeneratedCalculator {{
  public static double[] {fn}(double[] w,double[] mu,double[][] cov,double rf){{
    int n=w==null?0:w.length;
    if(n<2||mu==null||mu.length!=n||cov==null||cov.length!=n||!Double.isFinite(rf))throw new IllegalArgumentException("Invalid portfolio shape");
    double total=0,ret=0,variance=0;
    for(int i=0;i<n;i++){{
      if(!Double.isFinite(w[i])||!Double.isFinite(mu[i])||cov[i]==null||cov[i].length!=n)throw new IllegalArgumentException("Invalid portfolio arrays");
      total+=w[i];ret+=w[i]*mu[i];
      for(int j=0;j<n;j++){{if(!Double.isFinite(cov[i][j]))throw new IllegalArgumentException("Nonfinite covariance");variance+=w[i]*cov[i][j]*w[j];}}
    }}
    if(Math.abs(total-1)>1.001e-5)throw new IllegalArgumentException("Invalid weights");
    double[][] lower=new double[n][n];
    for(int i=0;i<n;i++){{
      for(int j=0;j<n;j++)if(Math.abs(cov[i][j]-cov[j][i])>1e-9+1e-5*Math.abs(cov[j][i]))throw new IllegalArgumentException("Asymmetric covariance");
      for(int j=0;j<=i;j++){{double v=cov[i][j];for(int k=0;k<j;k++)v-=lower[i][k]*lower[j][k];
        if(i==j){{if(!(v>1e-12))throw new IllegalArgumentException("Non SPD covariance");lower[i][j]=Math.sqrt(v);}}
        else lower[i][j]=v/lower[j][j];}}
    }}
    double vol=Math.sqrt(Math.max(variance,0));return new double[]{{ret,vol,vol>0?(ret-rf)/vol:Double.NaN}};
  }}
}}
'''
    if l == 'C#':
        return f'''// {note}
using System;
public static class GeneratedCalculator {{
  public static double[] {fn}(double[] w,double[] mu,double[,] cov,double rf=0){{
    int n=w?.Length??0;
    if(n<2||mu==null||mu.Length!=n||cov==null||cov.GetLength(0)!=n||cov.GetLength(1)!=n||!double.IsFinite(rf))throw new ArgumentException("Invalid portfolio shape");
    double total=0,ret=0,variance=0;
    for(int i=0;i<n;i++){{
      if(!double.IsFinite(w[i])||!double.IsFinite(mu[i]))throw new ArgumentException("Nonfinite portfolio inputs");
      total+=w[i];ret+=w[i]*mu[i];
      for(int j=0;j<n;j++){{if(!double.IsFinite(cov[i,j]))throw new ArgumentException("Nonfinite covariance");variance+=w[i]*cov[i,j]*w[j];}}
    }}
    if(Math.Abs(total-1)>1.001e-5)throw new ArgumentException("Invalid weights");
    var lower=new double[n,n];
    for(int i=0;i<n;i++){{
      for(int j=0;j<n;j++)if(Math.Abs(cov[i,j]-cov[j,i])>1e-9+1e-5*Math.Abs(cov[j,i]))throw new ArgumentException("Asymmetric covariance");
      for(int j=0;j<=i;j++){{double v=cov[i,j];for(int k=0;k<j;k++)v-=lower[i,k]*lower[j,k];
        if(i==j){{if(!(v>1e-12))throw new ArgumentException("Non SPD covariance");lower[i,j]=Math.Sqrt(v);}}
        else lower[i,j]=v/lower[j,j];}}
    }}
    double vol=Math.Sqrt(Math.Max(variance,0));return new double[]{{ret,vol,vol>0?(ret-rf)/vol:double.NaN}};
  }}
}}
'''
    if l == 'Swift':
        return f'''// {note}
import Foundation
func {fn}(_ w:[Double],_ mu:[Double],_ cov:[[Double]],_ rf:Double=0)->[Double]{{
  let n=w.count
  guard n>=2,mu.count==n,cov.count==n,rf.isFinite,w.allSatisfy({{$0.isFinite}}),mu.allSatisfy({{$0.isFinite}}),cov.allSatisfy({{$0.count==n && $0.allSatisfy({{$0.isFinite}})}}) else {{return [Double.nan,Double.nan,Double.nan]}}
  let weightSum=w.reduce(0,+)
  guard abs(weightSum-1)<=1.001e-5 else {{return [Double.nan,Double.nan,Double.nan]}}
  var ret=0.0,variance=0.0;var lower=Array(repeating:Array(repeating:0.0,count:n),count:n)
  for i in 0..<n{{
    ret+=w[i]*mu[i]
    for j in 0..<n{{variance+=w[i]*cov[i][j]*w[j]}}
  }}
  for i in 0..<n{{
    for j in 0..<n{{if abs(cov[i][j]-cov[j][i])>1e-9+1e-5*abs(cov[j][i]){{return [Double.nan,Double.nan,Double.nan]}}}}
    for j in 0...i{{
      var v=cov[i][j];if j>0{{for k in 0..<j{{v-=lower[i][k]*lower[j][k]}}}}
      if i==j{{guard v>1e-12 else {{return [Double.nan,Double.nan,Double.nan]}};lower[i][j]=sqrt(v)}}
      else{{lower[i][j]=v/lower[j][j]}}
    }}
  }}
  let vol=sqrt(max(variance,0));return [ret,vol,vol>0 ? (ret-rf)/vol : Double.nan]
}}
'''
    if l == 'Kotlin':
        return f'''// {note}
import kotlin.math.*
fun {fn}(w:DoubleArray,mu:DoubleArray,cov:Array<DoubleArray>,rf:Double=0.0):DoubleArray{{
  val n=w.size
  require(n>=2&&mu.size==n&&cov.size==n&&rf.isFinite()&&w.all{{it.isFinite()}}&&mu.all{{it.isFinite()}}&&cov.all{{it.size==n&&it.all{{x->x.isFinite()}}}}){{"Invalid portfolio shape"}}
  require(abs(w.sum()-1)<=1.001e-5){{"Invalid weights"}}
  var ret=0.0;var variance=0.0;val lower=Array(n){{DoubleArray(n)}}
  for(i in 0 until n){{ret+=w[i]*mu[i];for(j in 0 until n){{variance+=w[i]*cov[i][j]*w[j]}}}}
  for(i in 0 until n){{
    for(j in 0 until n)require(abs(cov[i][j]-cov[j][i])<=1e-9+1e-5*abs(cov[j][i])){{"Asymmetric covariance"}}
    for(j in 0..i){{
      var v=cov[i][j];for(k in 0 until j)v-=lower[i][k]*lower[j][k]
      if(i==j){{require(v>1e-12){{"Non SPD covariance"}};lower[i][j]=sqrt(v)}}
      else lower[i][j]=v/lower[j][j]
    }}
  }}
  val vol=sqrt(max(variance,0.0));return doubleArrayOf(ret,vol,if(vol>0)(ret-rf)/vol else Double.NaN)
}}
'''
    if l == 'Go':
        return f'''// {note}
package main
import "math"
func {fn}(w,mu []float64,cov [][]float64,rf float64)[3]float64{{
  fail:=[3]float64{{math.NaN(),math.NaN(),math.NaN()}}
  n:=len(w);if n<2||len(mu)!=n||len(cov)!=n||math.IsNaN(rf)||math.IsInf(rf,0){{return fail}}
  total,ret,variance:=0.0,0.0,0.0
  for i:=0;i<n;i++{{
    if len(cov[i])!=n||math.IsNaN(w[i])||math.IsInf(w[i],0)||math.IsNaN(mu[i])||math.IsInf(mu[i],0){{return fail}}
    total+=w[i];ret+=w[i]*mu[i]
    for j:=0;j<n;j++{{if math.IsNaN(cov[i][j])||math.IsInf(cov[i][j],0){{return fail}};variance+=w[i]*cov[i][j]*w[j]}}
  }}
  if math.Abs(total-1)>1.001e-5{{return fail}}
  lower:=make([][]float64,n);for i:=0;i<n;i++{{lower[i]=make([]float64,n)}}
  for i:=0;i<n;i++{{
    for j:=0;j<n;j++{{if math.Abs(cov[i][j]-cov[j][i])>1e-9+1e-5*math.Abs(cov[j][i]){{return fail}}}}
    for j:=0;j<=i;j++{{
      v:=cov[i][j];for k:=0;k<j;k++{{v-=lower[i][k]*lower[j][k]}}
      if i==j{{if !(v>1e-12){{return fail}};lower[i][j]=math.Sqrt(v)}}else{{lower[i][j]=v/lower[j][j]}}
    }}
  }}
  vol:=math.Sqrt(math.Max(variance,0));sharpe:=math.NaN();if vol>0{{sharpe=(ret-rf)/vol}}
  return [3]float64{{ret,vol,sharpe}}
}}
'''
    if l == 'Rust':
        return f'''// {note}
pub fn {fn}(w:&[f64],mu:&[f64],cov:&[Vec<f64>],rf:f64)->[f64;3]{{
  let fail=[f64::NAN;3];let n=w.len();
  if n<2||mu.len()!=n||cov.len()!=n||!rf.is_finite()||!w.iter().all(|x|x.is_finite())||!mu.iter().all(|x|x.is_finite())||!cov.iter().all(|row|row.len()==n&&row.iter().all(|x|x.is_finite())){{return fail;}}
  if (w.iter().sum::<f64>()-1.0).abs()>1.001e-5{{return fail;}}
  let(mut ret,mut variance)=(0.0,0.0);let mut lower=vec![vec![0.0;n];n];
  for i in 0..n{{ret+=w[i]*mu[i];for j in 0..n{{variance+=w[i]*cov[i][j]*w[j];}}}}
  for i in 0..n{{
    for j in 0..n{{if (cov[i][j]-cov[j][i]).abs()>1e-9+1e-5*cov[j][i].abs(){{return fail;}}}}
    for j in 0..=i{{
      let mut v=cov[i][j];for k in 0..j{{v-=lower[i][k]*lower[j][k];}}
      if i==j{{if !(v>1e-12){{return fail;}}lower[i][j]=v.sqrt();}}
      else{{lower[i][j]=v/lower[j][j];}}
    }}
  }}
  let vol=variance.max(0.0_f64).sqrt();[ret,vol,if vol>0.0{{(ret-rf)/vol}}else{{f64::NAN}}]
}}
'''
    raise GenerationError(f'{l}: portfolio code emitter not implemented')
