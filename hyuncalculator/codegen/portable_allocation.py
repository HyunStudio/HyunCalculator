"""Standalone long/short Markowitz GMV and target-return emitters.

The two profiles share a Cholesky SPD solve.  All target languages use
column-vectors and n x n covariance matrices, except C (row-major buffer).
No specialized finance/numerical packages are required by emitted code.
"""
from __future__ import annotations
from .emitter import GenerationError

SUPPORTED = frozenset({'qf_gmv', 'qf_target'})


def generate_allocation(fn, form, options):
    if options.language == 'Python':
        raise GenerationError('Python uses reference implementation emitter')
    if (options.structure != 'function' or options.iteration != 'auto'
            or options.variable_names or options.variant != 'periodic'
            or options.imports not in ('auto','standard')):
        raise GenerationError('Markowitz supports function/auto/standard imports and canonical variable names only')
    target = form.function == 'qf_target'
    if form.function not in SUPPORTED: raise GenerationError('Unsupported allocation formula')
    language = options.language
    # Include explicit model assumptions, since these are not no-short optimizers.
    note = 'HyunCalculator Markowitz: fully invested, short positions allowed; covariance must be symmetric positive definite. Output=[weights...,variance/expected_return].'
    if language == 'R':
        params = 'mu,cov,target' if target else 'cov'
        validation = '''  if(length(mu)!=n || any(!is.finite(mu)) || !is.finite(target))stop("Invalid expected returns/target")
''' if target else ''
        calc = '''  z<-as.numeric(solve(cov,mu));b<-sum(z);c<-sum(mu*z);det<-a*c-b*b
  if(!is.finite(det)||det<=1e-12)stop("Expected returns must be distinct")
  weights<-((c-b*target)/det)*y+((a*target-b)/det)*z
''' if target else '''  weights<-y/a
'''
        return f'''# {note}
{fn} <- function({params}) {{
  n<-nrow(cov)
  if(!is.matrix(cov)||n<2||ncol(cov)!=n||any(!is.finite(cov))||any(abs(cov-t(cov))>1e-9+1e-5*abs(t(cov))))stop("Invalid covariance")
  {validation.strip()}
  if(inherits(try(chol(cov),silent=TRUE),"try-error"))stop("Covariance not SPD")
  y<-as.numeric(solve(cov,rep(1,n)));a<-sum(y)
  if(!is.finite(a)||a<=0)stop("Invalid covariance")
{calc}  metric<-{'sum(mu*weights)' if target else 'as.numeric(t(weights)%*%cov%*%weights)'}
  return(c(as.numeric(weights),metric))
}}
'''
    if language == 'MATLAB':
        params = 'mu,cov,target' if target else 'cov'
        validation = '''  if numel(mu)~=n || any(~isfinite(mu(:))) || ~isscalar(target) || ~isfinite(target),error('Invalid target');end
  mu=mu(:);
''' if target else ''
        calc = '''  z=cov\\mu;b=sum(z);c=mu'*z;det=a*c-b*b;
  if ~(isfinite(det)&&det>1e-12),error('Expected returns must be distinct');end
  weights=((c-b*target)/det)*y+((a*target-b)/det)*z;
''' if target else '  weights=y/a;\n'
        return f'''% {note}
function weights = {fn}({params})
  n=size(cov,1);
  if n<2 || size(cov,2)~=n || any(~isfinite(cov(:))) || any(any(abs(cov-cov')>1e-9+1e-5*abs(cov'))),error('Invalid covariance');end
{validation}  [~,pd]=chol(cov);if pd~=0,error('Covariance not SPD');end
  y=cov\\ones(n,1);a=sum(y);
  if ~(isfinite(a)&&a>0),error('Invalid covariance');end
{calc}  metric={"mu' * weights" if target else "weights' * cov * weights"};
  weights=[weights;metric];
end
'''.replace('\\\\','\\')
    if language == 'Julia':
        params = 'mu,cov,target' if target else 'cov'
        validation = '''  if length(mu)!=n || !all(isfinite,mu) || !isfinite(target)
    throw(ArgumentError("Invalid expected returns/target"))
  end
''' if target else ''
        calc = '''  z=fac\\mu;b=sum(z);c=dot(mu,z);det=a*c-b*b
  if !isfinite(det) || det<=1e-12
    throw(ArgumentError("Expected returns must be distinct"))
  end
  weights=((c-b*target)/det).*y .+ ((a*target-b)/det).*z
''' if target else '  weights=y./a\n'
        return f'''# {note}
using LinearAlgebra
function {fn}({params})
  n=size(cov,1)
  if n<2 || size(cov,2)!=n || !all(isfinite,cov) || any(abs.(cov-cov') .> (1e-9 .+ 1e-5 .* abs.(cov')))
    throw(ArgumentError("Invalid covariance"))
  end
{validation}  fac=cholesky(Symmetric(cov));y=fac\\ones(n);a=sum(y)
  if !isfinite(a) || a<=0
    throw(ArgumentError("Invalid covariance"))
  end
{calc}  metric={'dot(mu,weights)' if target else 'dot(weights,cov*weights)'}
  return vcat(weights,metric)
end
'''.replace('\\\\','\\')
    if language == 'C':
        args = 'const double* mu,const double* cov,size_t n,double target,double* out' if target else 'const double* cov,size_t n,double* out'
        val = '''  if(!mu||!isfinite(target))return -1;
  for(size_t i=0;i<n;i++)if(!isfinite(mu[i]))return -1;
''' if target else ''
        solve2 = '''  double *z=calloc(n,sizeof(double));if(!z){free(l);free(y);return -1;}
  for(size_t i=0;i<n;i++)z[i]=mu[i];
  for(size_t i=0;i<n;i++){for(size_t j=0;j<i;j++)z[i]-=l[i*n+j]*z[j];z[i]/=l[i*n+i];}
  for(size_t i=n;i-->0;){for(size_t j=i+1;j<n;j++)z[i]-=l[j*n+i]*z[j];z[i]/=l[i*n+i];}
  double b=0,c=0;for(size_t i=0;i<n;i++){b+=z[i];c+=mu[i]*z[i];}
  double det=a*c-b*b;if(!isfinite(det)||det<=1e-12){free(l);free(y);free(z);return -1;}
  for(size_t i=0;i<n;i++)out[i]=((c-b*target)/det)*y[i]+((a*target-b)/det)*z[i];
  free(z);
''' if target else '''  for(size_t i=0;i<n;i++)out[i]=y[i]/a;
'''
        return f'''/* {note} cov is row-major n*n. out capacity >= n+1. Returns 0 on success, -1 on failure. */
#include <math.h>
#include <stddef.h>
#include <stdlib.h>
int {fn}({args}){{
  if(!cov||!out||n<2||n>2048)return -1;
{val}  double *l=calloc(n*n,sizeof(double)),*y=calloc(n,sizeof(double));
  if(!l||!y){{free(l);free(y);return -1;}}
  int valid=1;
  for(size_t i=0;i<n&&valid;i++){{
    for(size_t j=0;j<n;j++)if(!isfinite(cov[i*n+j])||fabs(cov[i*n+j]-cov[j*n+i])>1e-9+1e-5*fabs(cov[j*n+i])){{valid=0;break;}}
    for(size_t j=0;j<=i&&valid;j++){{
      double value=cov[i*n+j];for(size_t k=0;k<j;k++)value-=l[i*n+k]*l[j*n+k];
      if(i==j){{if(!(value>1e-12)){{valid=0;break;}}l[i*n+j]=sqrt(value);}}
      else l[i*n+j]=value/l[j*n+j];
    }}
  }}
  if(!valid){{free(l);free(y);return -1;}}
  for(size_t i=0;i<n;i++)y[i]=1.0;
  for(size_t i=0;i<n;i++){{for(size_t j=0;j<i;j++)y[i]-=l[i*n+j]*y[j];y[i]/=l[i*n+i];}}
  for(size_t i=n;i-->0;){{for(size_t j=i+1;j<n;j++)y[i]-=l[j*n+i]*y[j];y[i]/=l[i*n+i];}}
  double a=0;for(size_t i=0;i<n;i++)a+=y[i];
  if(!isfinite(a)||a<=0){{free(l);free(y);return -1;}}
{solve2}  double metric=0;
  {'for(size_t i=0;i<n;i++)metric+=out[i]*mu[i];' if target else 'for(size_t i=0;i<n;i++)for(size_t j=0;j<n;j++)metric+=out[i]*cov[i*n+j]*out[j];'}
  out[n]=metric;
  free(l);free(y);return 0;
}}
'''
    if language == 'C++':
        params = 'const std::vector<double>& mu,const std::vector<std::vector<double>>& cov,double target' if target else 'const std::vector<std::vector<double>>& cov'
        validation = '''  if(mu.size()!=n||!std::isfinite(target))throw std::invalid_argument("Invalid target");
  for(double v:mu)if(!std::isfinite(v))throw std::invalid_argument("Invalid expected returns");
''' if target else ''
        calc = '''  auto z=solve(mu);double b=0,c=0;for(size_t i=0;i<n;i++){b+=z[i];c+=mu[i]*z[i];}
  double det=a*c-b*b;if(!std::isfinite(det)||det<=1e-12)throw std::invalid_argument("Expected returns must be distinct");
  std::vector<double> out(n);for(size_t i=0;i<n;i++)out[i]=((c-b*target)/det)*y[i]+((a*target-b)/det)*z[i];
  double metric=0;for(size_t i=0;i<n;i++)metric+=out[i]*mu[i];out.push_back(metric);return out;
''' if target else '''  for(double& v:y){{v/=a;}}
  double metric=0;
  for(size_t i=0;i<n;i++)for(size_t j=0;j<n;j++)metric+=y[i]*cov[i][j]*y[j];
  y.push_back(metric);return y;
'''
        return f'''// {note}
#include <vector>
#include <cmath>
#include <stdexcept>
#include <cstddef>
std::vector<double> {fn}({params}){{
  size_t n=cov.size();if(n<2||n>2048)throw std::invalid_argument("Invalid covariance shape");
{validation}  std::vector<std::vector<double>> l(n,std::vector<double>(n,0));
  for(size_t i=0;i<n;i++){{
    if(cov[i].size()!=n)throw std::invalid_argument("Invalid covariance shape");
    for(double v:cov[i])if(!std::isfinite(v))throw std::invalid_argument("Nonfinite covariance");
  }}
  for(size_t i=0;i<n;i++){{
    for(size_t j=0;j<n;j++)if(std::abs(cov[i][j]-cov[j][i])>1e-9+1e-5*std::abs(cov[j][i]))throw std::invalid_argument("Asymmetric covariance");
    for(size_t j=0;j<=i;j++){{double v=cov[i][j];for(size_t k=0;k<j;k++)v-=l[i][k]*l[j][k];
      if(i==j){{if(!(v>1e-12))throw std::invalid_argument("Covariance not SPD");l[i][j]=std::sqrt(v);}}
      else l[i][j]=v/l[j][j];}}
  }}
  auto solve=[&](std::vector<double> v){{
    for(size_t i=0;i<n;i++){{for(size_t j=0;j<i;j++)v[i]-=l[i][j]*v[j];v[i]/=l[i][i];}}
    for(size_t i=n;i-->0;){{for(size_t j=i+1;j<n;j++)v[i]-=l[j][i]*v[j];v[i]/=l[i][i];}}
    return v;
  }};
  auto y=solve(std::vector<double>(n,1));double a=0;for(double v:y)a+=v;
  if(!std::isfinite(a)||a<=0)throw std::invalid_argument("Invalid covariance");
{calc}}}
'''
    if language in ('JavaScript','TypeScript'):
        ts = language == 'TypeScript'
        params = 'mu: number[], cov: number[][], target: number' if target and ts else 'mu, cov, target' if target else 'cov: number[][]' if ts else 'cov'
        outtype=': number[]' if ts else ''
        typing=': number[]' if ts else ''
        validation='''  if(!Array.isArray(mu)||mu.length!==n||!mu.every(Number.isFinite)||!Number.isFinite(target))throw new RangeError("Invalid target");
''' if target else ''
        calc = '''  const z=solve(mu);let b=0,c=0;for(let i=0;i<n;i++){b+=z[i];c+=mu[i]*z[i];}
  const det=a*c-b*b;if(!Number.isFinite(det)||det<=1e-12)throw new RangeError("Expected returns must be distinct");
  const w=y.map((v,i)=>((c-b*target)/det)*v+((a*target-b)/det)*z[i]);
  return [...w,w.reduce((s,v,i)=>s+v*mu[i],0)];
''' if target else '''  const w=y.map(v=>v/a);let metric=0;for(let i=0;i<n;i++)for(let j=0;j<n;j++)metric+=w[i]*cov[i][j]*w[j];
  return [...w,metric];
'''
        return f'''// {note}
export function {fn}({params}){outtype} {{
  if(!Array.isArray(cov)||cov.length<2||cov.length>2048)throw new RangeError("Invalid covariance");
  const n=cov.length;
{validation}  const l=Array.from({{length:n}},()=>new Array<number>(n).fill(0));
  for(let i=0;i<n;i++){{if(!Array.isArray(cov[i])||cov[i].length!==n||!cov[i].every(Number.isFinite))throw new RangeError("Nonfinite covariance");}}
  for(let i=0;i<n;i++){{
    for(let j=0;j<n;j++)if(Math.abs(cov[i][j]-cov[j][i])>1e-9+1e-5*Math.abs(cov[j][i]))throw new RangeError("Asymmetric covariance");
    for(let j=0;j<=i;j++){{let v=cov[i][j];for(let k=0;k<j;k++)v-=l[i][k]*l[j][k];
      if(i===j){{if(!(v>1e-12))throw new RangeError("Covariance not SPD");l[i][j]=Math.sqrt(v);}}
      else l[i][j]=v/l[j][j];}}
  }}
  const solve=(rhs{typing}){outtype}=>{{
    const v=rhs.slice();for(let i=0;i<n;i++){{for(let j=0;j<i;j++)v[i]-=l[i][j]*v[j];v[i]/=l[i][i];}}
    for(let i=n-1;i>=0;i--){{for(let j=i+1;j<n;j++)v[i]-=l[j][i]*v[j];v[i]/=l[i][i];}}
    return v;
  }};
  const y=solve(new Array(n).fill(1)),a=y.reduce((s,v)=>s+v,0);
  if(!Number.isFinite(a)||a<=0)throw new RangeError("Invalid covariance");
{calc}}}
'''.replace('new Array<number>(n)', 'new Array(n)' if not ts else 'new Array<number>(n)')
    if language == 'Java':
        params = 'double[] mu,double[][] cov,double target' if target else 'double[][] cov'
        val = '''    if(mu==null||mu.length!=n||!Double.isFinite(target))throw new IllegalArgumentException("Invalid target");
    for(double d:mu)if(!Double.isFinite(d))throw new IllegalArgumentException("Invalid expected returns");
''' if target else ''
        calc = '''    double[] z=solve(l,mu);double b=0,c=0;for(int i=0;i<n;i++){b+=z[i];c+=mu[i]*z[i];}
    double det=a*c-b*b;if(!Double.isFinite(det)||det<=1e-12)throw new IllegalArgumentException("Expected returns must be distinct");
    double[] out=new double[n+1];for(int i=0;i<n;i++)out[i]=((c-b*target)/det)*y[i]+((a*target-b)/det)*z[i];
    for(int i=0;i<n;i++)out[n]+=out[i]*mu[i];return out;
''' if target else '''    double[] out=new double[n+1];for(int i=0;i<n;i++)out[i]=y[i]/a;
    for(int i=0;i<n;i++)for(int j=0;j<n;j++)out[n]+=out[i]*cov[i][j]*out[j];return out;
'''
        return f'''// {note}
public class GeneratedCalculator {{
  private static double[] solve(double[][] l,double[] rhs){{
    int n=rhs.length;double[] v=rhs.clone();
    for(int i=0;i<n;i++){{for(int j=0;j<i;j++)v[i]-=l[i][j]*v[j];v[i]/=l[i][i];}}
    for(int i=n-1;i>=0;i--){{for(int j=i+1;j<n;j++)v[i]-=l[j][i]*v[j];v[i]/=l[i][i];}}
    return v;
  }}
  public static double[] {fn}({params}){{
    int n=cov==null?0:cov.length;if(n<2||n>2048)throw new IllegalArgumentException("Invalid covariance shape");
{val}    double[][] l=new double[n][n];
    for(int i=0;i<n;i++){{if(cov[i]==null||cov[i].length!=n)throw new IllegalArgumentException("Invalid covariance row");
      for(double d:cov[i])if(!Double.isFinite(d))throw new IllegalArgumentException("Nonfinite covariance");}}
    for(int i=0;i<n;i++){{
      for(int j=0;j<n;j++)if(Math.abs(cov[i][j]-cov[j][i])>1e-9+1e-5*Math.abs(cov[j][i]))throw new IllegalArgumentException("Asymmetric covariance");
      for(int j=0;j<=i;j++){{double v=cov[i][j];for(int k=0;k<j;k++)v-=l[i][k]*l[j][k];
        if(i==j){{if(!(v>1e-12))throw new IllegalArgumentException("Covariance not SPD");l[i][j]=Math.sqrt(v);}}
        else l[i][j]=v/l[j][j];}}
    }}
    double[] rhs=new double[n];java.util.Arrays.fill(rhs,1);
    double[] y=solve(l,rhs);double a=0;for(double d:y)a+=d;
    if(!Double.isFinite(a)||a<=0)throw new IllegalArgumentException("Invalid covariance");
{calc}  }}
}}
'''
    if language == 'C#':
        params = 'double[] mu,double[,] cov,double target' if target else 'double[,] cov'
        val = '''    if(mu==null||mu.Length!=n||!double.IsFinite(target))throw new ArgumentException("Invalid target");
    foreach(double d in mu)if(!double.IsFinite(d))throw new ArgumentException("Invalid expected returns");
''' if target else ''
        calc = '''    double[] z=Solve(l,mu);double b=0,c=0;for(int i=0;i<n;i++){b+=z[i];c+=mu[i]*z[i];}
    double det=a*c-b*b;if(!double.IsFinite(det)||det<=1e-12)throw new ArgumentException("Expected returns must be distinct");
    double[] output=new double[n+1];for(int i=0;i<n;i++)output[i]=((c-b*target)/det)*y[i]+((a*target-b)/det)*z[i];
    for(int i=0;i<n;i++)output[n]+=output[i]*mu[i];return output;
''' if target else '''    double[] output=new double[n+1];for(int i=0;i<n;i++)output[i]=y[i]/a;
    for(int i=0;i<n;i++)for(int j=0;j<n;j++)output[n]+=output[i]*cov[i,j]*output[j];return output;
'''
        return f'''// {note}
using System;
public static class GeneratedCalculator {{
  private static double[] Solve(double[,] l,double[] rhs){{
    int n=rhs.Length;double[] v=(double[])rhs.Clone();
    for(int i=0;i<n;i++){{for(int j=0;j<i;j++)v[i]-=l[i,j]*v[j];v[i]/=l[i,i];}}
    for(int i=n-1;i>=0;i--){{for(int j=i+1;j<n;j++)v[i]-=l[j,i]*v[j];v[i]/=l[i,i];}}
    return v;
  }}
  public static double[] {fn}({params}){{
    int n=cov==null?0:cov.GetLength(0);if(n<2||n>2048||cov.GetLength(1)!=n)throw new ArgumentException("Invalid covariance shape");
{val}    var l=new double[n,n];
    for(int i=0;i<n;i++)for(int j=0;j<n;j++){{if(!double.IsFinite(cov[i,j]))throw new ArgumentException("Nonfinite covariance");}}
    for(int i=0;i<n;i++){{
      for(int j=0;j<n;j++)if(Math.Abs(cov[i,j]-cov[j,i])>1e-9+1e-5*Math.Abs(cov[j,i]))throw new ArgumentException("Asymmetric covariance");
      for(int j=0;j<=i;j++){{double v=cov[i,j];for(int k=0;k<j;k++)v-=l[i,k]*l[j,k];
        if(i==j){{if(!(v>1e-12))throw new ArgumentException("Covariance not SPD");l[i,j]=Math.Sqrt(v);}}
        else l[i,j]=v/l[j,j];}}
    }}
    double[] rhs=new double[n];Array.Fill(rhs,1.0);double[] y=Solve(l,rhs);double a=0;foreach(double d in y)a+=d;
    if(!double.IsFinite(a)||a<=0)throw new ArgumentException("Invalid covariance");
{calc}  }}
}}
'''
    if language == 'Swift':
        params = '_ mu: [Double],_ cov: [[Double]],_ target: Double' if target else '_ cov: [[Double]]'
        val = '''  guard mu.count == n && mu.allSatisfy({$0.isFinite}) && target.isFinite else {throw MarkowitzError.invalidInput}
''' if target else ''
        calc = '''  let z=solve(mu),b=z.reduce(0,+),c=zip(mu,z).reduce(0){$0+$1.0*$1.1},det=a*c-b*b
  guard det.isFinite && det>1e-12 else {throw MarkowitzError.invalidInput}
  let w=zip(y,z).map{((c-b*target)/det)*$0.0+((a*target-b)/det)*$0.1}
  let metric=zip(w,mu).reduce(0.0){$0+$1.0*$1.1}
  return w+[metric]
''' if target else '''  let w=y.map{$0/a};var metric=0.0
  for i in 0..<n {for j in 0..<n {metric+=w[i]*cov[i][j]*w[j]}}
  return w+[metric]
'''
        return f'''// {note}
import Foundation
enum MarkowitzError: Error {{case invalidInput}}
func {fn}({params}) throws -> [Double] {{
  let n=cov.count
  guard n>=2 && n<=2048 && cov.allSatisfy({{$0.count==n && $0.allSatisfy({{$0.isFinite}})}}) else {{throw MarkowitzError.invalidInput}}
{val}  var l=Array(repeating:Array(repeating:0.0,count:n),count:n)
  for i in 0..<n {{
    for j in 0..<n {{if abs(cov[i][j]-cov[j][i])>1e-9+1e-5*abs(cov[j][i]) {{throw MarkowitzError.invalidInput}}}}
    for j in 0...i {{var v=cov[i][j];if j>0 {{for k in 0..<j {{v-=l[i][k]*l[j][k]}}}}
      if i==j {{guard v>1e-12 else {{throw MarkowitzError.invalidInput}};l[i][j]=sqrt(v)}}
      else {{l[i][j]=v/l[j][j]}}
    }}
  }}
  func solve(_ rhs:[Double])->[Double] {{
    var v=rhs
    for i in 0..<n {{if i>0 {{for j in 0..<i {{v[i]-=l[i][j]*v[j]}}}};v[i]/=l[i][i]}}
    for i in stride(from:n-1,through:0,by:-1) {{if i+1<n {{for j in (i+1)..<n {{v[i]-=l[j][i]*v[j]}}}};v[i]/=l[i][i]}}
    return v
  }}
  let y=solve(Array(repeating:1.0,count:n)),a=y.reduce(0,+)
  guard a.isFinite && a>0 else {{throw MarkowitzError.invalidInput}}
{calc}}}
'''
    if language == 'Kotlin':
        params='mu: DoubleArray,cov: Array<DoubleArray>,target: Double' if target else 'cov: Array<DoubleArray>'
        val='''  if(mu.size!=n||!target.isFinite()||mu.any{!it.isFinite()})throw IllegalArgumentException("Invalid target")
''' if target else ''
        calc='''  val z=solve(mu);val b=z.sum();var c=0.0;for(i in 0 until n)c+=mu[i]*z[i]
  val det=a*c-b*b;if(!det.isFinite()||det<=1e-12)throw IllegalArgumentException("Expected returns must be distinct")
  val out=DoubleArray(n+1);for(i in 0 until n){out[i]=((c-b*target)/det)*y[i]+((a*target-b)/det)*z[i];out[n]+=out[i]*mu[i]};return out
''' if target else '''  val out=DoubleArray(n+1);for(i in 0 until n)out[i]=y[i]/a
  for(i in 0 until n)for(j in 0 until n)out[n]+=out[i]*cov[i][j]*out[j];return out
'''
        return f'''// {note}
import kotlin.math.*
fun {fn}({params}):DoubleArray{{
  val n=cov.size;if(n<2||n>2048||cov.any{{it.size!=n||it.any{{x->!x.isFinite()}}}})throw IllegalArgumentException("Invalid covariance")
{val}  val l=Array(n){{DoubleArray(n)}}
  for(i in 0 until n){{
    for(j in 0 until n)if(abs(cov[i][j]-cov[j][i])>1e-9+1e-5*abs(cov[j][i]))throw IllegalArgumentException("Asymmetric covariance")
    for(j in 0..i){{var v=cov[i][j];for(k in 0 until j)v-=l[i][k]*l[j][k]
      if(i==j){{if(v<=1e-12)throw IllegalArgumentException("Covariance not SPD");l[i][j]=sqrt(v)}}else l[i][j]=v/l[j][j]
    }}
  }}
  fun solve(rhs:DoubleArray):DoubleArray{{
    val v=rhs.copyOf();for(i in 0 until n){{for(j in 0 until i)v[i]-=l[i][j]*v[j];v[i]/=l[i][i]}}
    for(i in n-1 downTo 0){{for(j in i+1 until n)v[i]-=l[j][i]*v[j];v[i]/=l[i][i]}};return v
  }}
  val y=solve(DoubleArray(n){{1.0}});val a=y.sum();if(!a.isFinite()||a<=0)throw IllegalArgumentException("Invalid covariance")
{calc}}}
'''
    if language == 'Go':
        params='mu []float64,cov [][]float64,target float64' if target else 'cov [][]float64'
        val='''  if len(mu)!=n||math.IsNaN(target)||math.IsInf(target,0){return nil}
  for _,v:=range mu{if math.IsNaN(v)||math.IsInf(v,0){return nil}}
''' if target else ''
        calc='''  z:=solve(mu);b,c:=0.0,0.0;for i:=0;i<n;i++{b+=z[i];c+=mu[i]*z[i]}
  det:=a*c-b*b;if math.IsNaN(det)||math.IsInf(det,0)||det<=1e-12{return nil}
  out:=make([]float64,n+1);for i:=0;i<n;i++{out[i]=((c-b*target)/det)*y[i]+((a*target-b)/det)*z[i];out[n]+=out[i]*mu[i]};return out
''' if target else '''  out:=make([]float64,n+1);for i:=0;i<n;i++{out[i]=y[i]/a}
  for i:=0;i<n;i++{for j:=0;j<n;j++{out[n]+=out[i]*cov[i][j]*out[j]}};return out
'''
        return f'''// {note}; invalid inputs return nil.
package main
import "math"
func {fn}({params}) []float64{{
  n:=len(cov);if n<2||n>2048{{return nil}}
{val}  l:=make([][]float64,n);for i:=range l{{l[i]=make([]float64,n)}}
  for i:=0;i<n;i++{{if len(cov[i])!=n{{return nil}};for _,v:=range cov[i]{{if math.IsNaN(v)||math.IsInf(v,0){{return nil}}}}}}
  for i:=0;i<n;i++{{
    for j:=0;j<n;j++{{if math.Abs(cov[i][j]-cov[j][i])>1e-9+1e-5*math.Abs(cov[j][i]){{return nil}}}}
    for j:=0;j<=i;j++{{v:=cov[i][j];for k:=0;k<j;k++{{v-=l[i][k]*l[j][k]}}
      if i==j{{if v<=1e-12{{return nil}};l[i][j]=math.Sqrt(v)}}else{{l[i][j]=v/l[j][j]}}
    }}
  }}
  solve:=func(rhs []float64)[]float64{{v:=append([]float64(nil),rhs...);for i:=0;i<n;i++{{for j:=0;j<i;j++{{v[i]-=l[i][j]*v[j]}};v[i]/=l[i][i]}}
    for i:=n-1;i>=0;i--{{for j:=i+1;j<n;j++{{v[i]-=l[j][i]*v[j]}};v[i]/=l[i][i]}};return v}}
  ones:=make([]float64,n);for i:=range ones{{ones[i]=1}}
  y:=solve(ones);a:=0.0;for _,v:=range y{{a+=v}};if math.IsNaN(a)||math.IsInf(a,0)||a<=0{{return nil}}
{calc}}}
'''
    if language == 'Rust':
        params='mu:&[f64],cov:&[Vec<f64>],target:f64' if target else 'cov:&[Vec<f64>]'
        val='''  if mu.len()!=n||!target.is_finite()||mu.iter().any(|v|!v.is_finite()){return Err("Invalid target");}
''' if target else ''
        calc='''  let z=solve(mu);let b:f64=z.iter().sum();let c:f64=mu.iter().zip(z.iter()).map(|(u,v)|u*v).sum();let det=a*c-b*b;
  if !det.is_finite()||det<=1e-12{return Err("Expected returns must be distinct");}
  let mut out:Vec<f64>=(0..n).map(|i|((c-b*target)/det)*y[i]+((a*target-b)/det)*z[i]).collect();
  let metric:f64=out.iter().zip(mu.iter()).map(|(a,b)|a*b).sum();out.push(metric);Ok(out)
''' if target else '''  let mut out:Vec<f64>=y.iter().map(|v|v/a).collect();let mut metric=0.0;
  for i in 0..n{for j in 0..n{metric+=out[i]*cov[i][j]*out[j];}}out.push(metric);Ok(out)
'''
        return f'''// {note}
pub fn {fn}({params})->Result<Vec<f64>,&'static str>{{
  let n=cov.len();if n<2||n>2048||cov.iter().any(|row|row.len()!=n||row.iter().any(|v|!v.is_finite())){{return Err("Invalid covariance");}}
{val}  let mut l=vec![vec![0.0_f64;n];n];
  for i in 0..n{{
    for j in 0..n{{if (cov[i][j]-cov[j][i]).abs()>1e-9+1e-5*cov[j][i].abs(){{return Err("Asymmetric covariance");}}}}
    for j in 0..=i{{let mut v=cov[i][j];for k in 0..j{{v-=l[i][k]*l[j][k];}}
      if i==j{{if v<=1e-12{{return Err("Covariance not SPD");}}l[i][j]=v.sqrt();}}else{{l[i][j]=v/l[j][j];}}
    }}
  }}
  let solve=|rhs:&[f64]|->Vec<f64>{{let mut v=rhs.to_vec();for i in 0..n{{for j in 0..i{{v[i]-=l[i][j]*v[j];}}v[i]/=l[i][i];}}
    for i in (0..n).rev(){{for j in (i+1)..n{{v[i]-=l[j][i]*v[j];}}v[i]/=l[i][i];}}v}};
  let y=solve(&vec![1.0;n]);let a:f64=y.iter().sum();if !a.is_finite()||a<=0.0{{return Err("Invalid covariance");}}
{calc}}}
'''
    raise GenerationError('Unsupported allocation language')
