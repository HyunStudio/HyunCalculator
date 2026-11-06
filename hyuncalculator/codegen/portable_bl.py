"""Black-Litterman posterior generator for thirteen non-Python target languages.

Outputs are flat [prior returns(n), posterior returns(n), posterior predictive
covariance (n*n row-major)] to preserve independent, dependency-free code.
The canonical Python generator retains the calculator's named dictionary.
"""
from __future__ import annotations

from .emitter import GenerationError

SUPPORTED = frozenset({'qf_bl'})


def generate_bl(fn, form, opt):
    if form.function != 'qf_bl' or opt.language == 'Python':
        raise GenerationError('Black-Litterman non-Python adapter only')
    if (opt.structure != 'function' or opt.iteration != 'auto' or opt.variable_names
            or opt.variant != 'periodic' or opt.imports not in ('auto', 'standard')):
        raise GenerationError('Black-Litterman requires function/auto/standard imports and canonical variables')
    lang = opt.language
    note = ('Black-Litterman: [prior(n), posterior(n), predictive_cov(n*n row-major)]; '
            'market sums to 1, cov SPD, omega strictly positive; 2<=n<=128, 1<=m<=128.')
    if lang == 'R':
        return f'''# {note}
{fn} <- function(cov, market, delta, tau, p, q, omega) {{
  n <- nrow(cov)
  if (!is.matrix(cov) || n < 2 || n > 128 || ncol(cov) != n || any(!is.finite(cov)) ||
      any(abs(cov - t(cov)) > 1e-9 + 1e-5 * abs(t(cov)))) stop("Invalid covariance")
  if (inherits(try(chol(cov),silent=TRUE),"try-error")) stop("Covariance must be SPD")
  if (length(market)!=n || any(!is.finite(market)) || abs(sum(market)-1)>1e-8+1e-5 ||
      length(delta)!=1 || length(tau)!=1 || !is.finite(delta) || !is.finite(tau) || delta<=0 || tau<=0) stop("Invalid market/delta/tau")
  m <- nrow(p)
  if (!is.matrix(p) || m<1 || m>128 || ncol(p)!=n || any(!is.finite(p)) ||
      length(q)!=m || length(omega)!=m || any(!is.finite(q)) ||
      any(!is.finite(omega)) || any(omega<=0)) stop("Invalid views")
  prior <- as.vector(delta * (cov %*% market))
  b <- tau * cov %*% t(p)
  a <- p %*% b + diag(as.vector(omega), nrow=m)
  if (inherits(try(chol(a),silent=TRUE),"try-error")) stop("Invalid posterior system")
  posterior <- as.vector(prior + b %*% solve(a, q - p %*% prior))
  predictive <- (1+tau)*cov - b %*% solve(a, t(b))
  c(prior, posterior, as.vector(t(predictive)))
}}
'''
    if lang == 'MATLAB':
        return f'''% {note}
function out = {fn}(cov, market, delta, tau, p, q, omega)
  n=size(cov,1);
  if n<2 || n>128 || size(cov,2)~=n || any(~isfinite(cov(:))) || ...
      any(any(abs(cov-cov')>1e-9+1e-5*abs(cov'))), error('Invalid covariance'); end
  [~,flag]=chol(cov); if flag~=0, error('Covariance must be SPD'); end
  market=market(:); q=q(:); omega=omega(:);
  if numel(market)~=n || any(~isfinite(market)) || abs(sum(market)-1)>1.00001e-5 || ...
      ~isscalar(delta) || ~isscalar(tau) || ~isfinite(delta) || ~isfinite(tau) || delta<=0 || tau<=0, error('Invalid market/delta/tau'); end
  m=size(p,1);
  if m<1 || m>128 || size(p,2)~=n || any(~isfinite(p(:))) || ...
      numel(q)~=m || numel(omega)~=m || any(~isfinite(q)) || any(~isfinite(omega)) || any(omega<=0), error('Invalid views'); end
  prior=delta*cov*market;
  b=tau*cov*p';
  a=p*b+diag(omega);
  [~,flag]=chol(a); if flag~=0, error('Invalid posterior system'); end
  posterior=prior+b*(a\\(q-p*prior));
  predictive=(1+tau)*cov-b*(a\\b');
  out=[prior;posterior;reshape(predictive.',[],1)];
end
'''.replace('\\\\','\\')
    if lang == 'Julia':
        return f'''# {note}
using LinearAlgebra
function {fn}(cov, market, delta, tau, p, q, omega)
  n=size(cov,1)
  if n<2 || n>128 || size(cov,2)!=n || !all(isfinite,cov) ||
     any(abs.(cov-cov') .> (1e-9 .+ 1e-5 .* abs.(cov')))
    throw(ArgumentError("Invalid covariance"))
  end
  cholesky(Symmetric(cov))
  m=size(p,1)
  if length(market)!=n || !all(isfinite,market) || abs(sum(market)-1)>1.00001e-5 ||
     !isfinite(delta) || !isfinite(tau) || delta<=0 || tau<=0 ||
     m<1 || m>128 || size(p,2)!=n || !all(isfinite,p) ||
     length(q)!=m || length(omega)!=m || !all(isfinite,q) ||
     !all(isfinite,omega) || any(omega .<= 0)
    throw(ArgumentError("Invalid views or inputs"))
  end
  prior=delta .* (cov*market)
  b=tau .* (cov*transpose(p))
  a=p*b+Diagonal(omega)
  fac=cholesky(Symmetric(a))
  posterior=prior+b*(fac\\(q-p*prior))
  predictive=(1+tau).*cov-b*(fac\\transpose(b))
  vcat(prior,posterior,vec(permutedims(predictive)))
end
'''.replace('\\\\','\\')
    if lang in ('JavaScript','TypeScript'):
        ts = lang == 'TypeScript'
        signature = ('cov: number[][], market: number[], delta: number, tau: number, p: number[][], q: number[], omega: number[]' if ts
                     else 'cov,market,delta,tau,p,q,omega')
        types = ': number[]' if ts else ''
        inner = '(a: number[][], rhs: number[])' if ts else '(a,rhs)'
        return f'''// {note}
function {fn}({signature}){types} {{
  const finite=(x{': number' if ts else ''})=>Number.isFinite(x);
  const n=cov.length,m=p.length;
  if(n<2||n>128||m<1||m>128||market.length!==n||q.length!==m||omega.length!==m||
     !finite(delta)||!finite(tau)||delta<=0||tau<=0||
     !market.every(finite)||Math.abs(market.reduce((a,b)=>a+b,0)-1)>1.00001e-5||
     !q.every(finite)||!omega.every(x=>finite(x)&&x>0)||
     !cov.every(row=>row.length===n&&row.every(finite))||!p.every(row=>row.length===n&&row.every(finite)))throw new RangeError('Invalid dimensions/inputs');
  const chol=(a{': number[][]' if ts else ''}){': number[][]' if ts else ''}=>{{
    const size=a.length,l=Array.from({{length:size}},()=>Array(size).fill(0));
    for(let i=0;i<size;i++){{
      for(let j=0;j<size;j++)if(!finite(a[i][j])||Math.abs(a[i][j]-a[j][i])>1e-9+1e-5*Math.abs(a[j][i]))throw new RangeError('Asymmetric matrix');
      for(let j=0;j<=i;j++){{let v=a[i][j];for(let k=0;k<j;k++)v-=l[i][k]*l[j][k];
        if(i===j){{if(!(v>1e-12))throw new RangeError('Not SPD');l[i][j]=Math.sqrt(v);}}
        else l[i][j]=v/l[j][j];
      }}
    }}return l;
  }};
  const solve={inner}{types}=>{{
    const l=chol(a),v=rhs.slice(),size=v.length;
    for(let i=0;i<size;i++){{for(let j=0;j<i;j++)v[i]-=l[i][j]*v[j];v[i]/=l[i][i];}}
    for(let i=size-1;i>=0;i--){{for(let j=i+1;j<size;j++)v[i]-=l[j][i]*v[j];v[i]/=l[i][i];}}return v;
  }};
  chol(cov);
  const prior=cov.map(row=>delta*row.reduce((s,v,j)=>s+v*market[j],0));
  const b=Array.from({{length:n}},(_,i)=>Array.from({{length:m}},(_,k)=>tau*cov[i].reduce((s,v,j)=>s+v*p[k][j],0)));
  const a=Array.from({{length:m}},(_,k)=>Array.from({{length:m}},(_,h)=>p[k].reduce((s,v,j)=>s+v*b[j][h],0)+(k===h?omega[k]:0)));
  const residual=q.map((v,k)=>v-p[k].reduce((s,x,j)=>s+x*prior[j],0));
  const shift=solve(a,residual);
  const posterior=prior.map((v,i)=>v+b[i].reduce((s,x,k)=>s+x*shift[k],0));
  const predictive=Array.from({{length:n}},(_,i)=>Array.from({{length:n}},(_,j)=>{{
    const z=solve(a,b[j]);return (1+tau)*cov[i][j]-b[i].reduce((s,x,k)=>s+x*z[k],0);
  }}));
  return [...prior,...posterior,...predictive.flat()];
}}
'''
    if lang == 'C++':
        return f'''// {note}
#include <vector>
#include <cmath>
#include <stdexcept>
#include <cstddef>
std::vector<double> {fn}(const std::vector<std::vector<double>>& cov,const std::vector<double>& market,double delta,double tau,const std::vector<std::vector<double>>& p,const std::vector<double>& q,const std::vector<double>& omega){{
  using Matrix=std::vector<std::vector<double>>;
  const size_t n=cov.size(),m=p.size();
  if(n<2||n>128||m<1||m>128||market.size()!=n||q.size()!=m||omega.size()!=m||
     !std::isfinite(delta)||!std::isfinite(tau)||delta<=0||tau<=0)throw std::invalid_argument("Invalid dimensions/parameters");
  auto check=[](const std::vector<double>& v){{for(double x:v)if(!std::isfinite(x))throw std::invalid_argument("Nonfinite input");}};
  check(market);check(q);check(omega);for(double x:omega)if(x<=0)throw std::invalid_argument("Invalid omega");
  double weightSum=0;for(double x:market)weightSum+=x;
  if(std::abs(weightSum-1)>1.00001e-5)throw std::invalid_argument("Weights must sum to one");
  for(const auto& row:cov){{if(row.size()!=n)throw std::invalid_argument("Invalid covariance shape");check(row);}}
  for(const auto& row:p){{if(row.size()!=n)throw std::invalid_argument("Invalid views shape");check(row);}}
  auto chol=[&](const Matrix& a){{size_t dim=a.size();Matrix l(dim,std::vector<double>(dim,0));
    for(size_t i=0;i<dim;i++){{
      for(size_t j=0;j<dim;j++)if(!std::isfinite(a[i][j])||std::abs(a[i][j]-a[j][i])>1e-9+1e-5*std::abs(a[j][i]))throw std::invalid_argument("Asymmetric matrix");
      for(size_t j=0;j<=i;j++){{double v=a[i][j];for(size_t k=0;k<j;k++)v-=l[i][k]*l[j][k];
        if(i==j){{if(!(v>1e-12))throw std::invalid_argument("Not SPD");l[i][j]=std::sqrt(v);}}
        else l[i][j]=v/l[j][j];
      }}
    }}return l;
  }};
  auto solve=[&](const Matrix& a,const std::vector<double>& rhs){{Matrix l=chol(a);std::vector<double> z=rhs;size_t dim=z.size();
    for(size_t i=0;i<dim;i++){{for(size_t j=0;j<i;j++)z[i]-=l[i][j]*z[j];z[i]/=l[i][i];}}
    for(size_t i=dim;i-->0;){{for(size_t j=i+1;j<dim;j++)z[i]-=l[j][i]*z[j];z[i]/=l[i][i];}}return z;
  }};
  (void)chol(cov);
  std::vector<double> prior(n,0),post(n,0);Matrix b(n,std::vector<double>(m,0)),a(m,std::vector<double>(m,0));
  for(size_t i=0;i<n;i++)for(size_t j=0;j<n;j++)prior[i]+=delta*cov[i][j]*market[j];
  for(size_t i=0;i<n;i++)for(size_t k=0;k<m;k++)for(size_t j=0;j<n;j++)b[i][k]+=tau*cov[i][j]*p[k][j];
  for(size_t k=0;k<m;k++)for(size_t h=0;h<m;h++){{a[k][h]=(k==h)?omega[k]:0;for(size_t j=0;j<n;j++)a[k][h]+=p[k][j]*b[j][h];}}
  std::vector<double> residual=q;
  for(size_t k=0;k<m;k++)for(size_t j=0;j<n;j++)residual[k]-=p[k][j]*prior[j];
  auto shift=solve(a,residual);
  for(size_t i=0;i<n;i++){{post[i]=prior[i];for(size_t k=0;k<m;k++)post[i]+=b[i][k]*shift[k];}}
  std::vector<double> out;out.reserve(2*n+n*n);out.insert(out.end(),prior.begin(),prior.end());out.insert(out.end(),post.begin(),post.end());
  for(size_t i=0;i<n;i++)for(size_t j=0;j<n;j++){{auto z=solve(a,b[j]);double v=(1+tau)*cov[i][j];for(size_t k=0;k<m;k++)v-=b[i][k]*z[k];out.push_back(v);}}
  return out;
}}
'''
    if lang == 'C':
        return f'''/* {note} Input cov row-major n*n, p row-major m*n, output capacity >= 2*n+n*n, return 0 on success. */
#include <math.h>
#include <stddef.h>
#include <stdlib.h>
static int bl_chol(const double*a,double*l,size_t n){{
 for(size_t i=0;i<n;i++){{for(size_t j=0;j<n;j++)if(!isfinite(a[i*n+j])||fabs(a[i*n+j]-a[j*n+i])>1e-9+1e-5*fabs(a[j*n+i]))return -1;
  for(size_t j=0;j<=i;j++){{double v=a[i*n+j];for(size_t k=0;k<j;k++)v-=l[i*n+k]*l[j*n+k];if(i==j){{if(!(v>1e-12))return -1;l[i*n+j]=sqrt(v);}}else l[i*n+j]=v/l[j*n+j];}}}}return 0;
}}
static void bl_solve(const double*l,const double*rhs,double*z,size_t n){{
 for(size_t i=0;i<n;i++){{z[i]=rhs[i];for(size_t j=0;j<i;j++)z[i]-=l[i*n+j]*z[j];z[i]/=l[i*n+i];}}
 for(size_t i=n;i-->0;){{for(size_t j=i+1;j<n;j++)z[i]-=l[j*n+i]*z[j];z[i]/=l[i*n+i];}}
}}
int {fn}(const double*cov,const double*market,size_t n,double delta,double tau,const double*p,size_t m,const double*q,const double*omega,double*out){{
 if(!cov||!market||!p||!q||!omega||!out||n<2||n>128||m<1||m>128||!isfinite(delta)||!isfinite(tau)||delta<=0||tau<=0)return -1;
 double wsum=0;for(size_t i=0;i<n;i++){{if(!isfinite(market[i]))return -1;wsum+=market[i];}}if(fabs(wsum-1)>1.00001e-5)return -1;
 for(size_t k=0;k<m;k++){{if(!isfinite(q[k])||!isfinite(omega[k])||omega[k]<=0)return -1;for(size_t j=0;j<n;j++)if(!isfinite(p[k*n+j]))return -1;}}
 double *lc=calloc(n*n,sizeof(double)),*b=calloc(n*m,sizeof(double)),*a=calloc(m*m,sizeof(double)),*la=calloc(m*m,sizeof(double));
 double *rhs=calloc(m,sizeof(double)),*z=calloc(m,sizeof(double)),*prior=calloc(n,sizeof(double)),*post=calloc(n,sizeof(double));
 if(!lc||!b||!a||!la||!rhs||!z||!prior||!post)goto fail;
 if(bl_chol(cov,lc,n))goto fail;
 for(size_t i=0;i<n;i++)for(size_t j=0;j<n;j++)prior[i]+=delta*cov[i*n+j]*market[j];
 for(size_t i=0;i<n;i++)for(size_t k=0;k<m;k++)for(size_t j=0;j<n;j++)b[i*m+k]+=tau*cov[i*n+j]*p[k*n+j];
 for(size_t k=0;k<m;k++)for(size_t h=0;h<m;h++){{a[k*m+h]=(k==h)?omega[k]:0;for(size_t j=0;j<n;j++)a[k*m+h]+=p[k*n+j]*b[j*m+h];}}
 if(bl_chol(a,la,m))goto fail;
 for(size_t k=0;k<m;k++){{rhs[k]=q[k];for(size_t j=0;j<n;j++)rhs[k]-=p[k*n+j]*prior[j];}}
 bl_solve(la,rhs,z,m);
 for(size_t i=0;i<n;i++){{post[i]=prior[i];for(size_t k=0;k<m;k++)post[i]+=b[i*m+k]*z[k];out[i]=prior[i];out[n+i]=post[i];}}
 for(size_t j=0;j<n;j++){{for(size_t k=0;k<m;k++)rhs[k]=b[j*m+k];bl_solve(la,rhs,z,m);
  for(size_t i=0;i<n;i++){{double v=(1+tau)*cov[i*n+j];for(size_t k=0;k<m;k++)v-=b[i*m+k]*z[k];out[2*n+i*n+j]=v;}}}}
 free(lc);free(b);free(a);free(la);free(rhs);free(z);free(prior);free(post);return 0;
fail:
 free(lc);free(b);free(a);free(la);free(rhs);free(z);free(prior);free(post);return -1;
}}
'''
    if lang == 'Java':
        return f'''// {note}
public final class GeneratedCalculator {{
  private static double[][] chol(double[][] a) {{
    int n=a.length;double[][] l=new double[n][n];
    for(int i=0;i<n;i++){{
      for(int j=0;j<n;j++)if(!Double.isFinite(a[i][j])||Math.abs(a[i][j]-a[j][i])>1e-9+1e-5*Math.abs(a[j][i]))throw new IllegalArgumentException("Asymmetric matrix");
      for(int j=0;j<=i;j++){{double v=a[i][j];for(int k=0;k<j;k++)v-=l[i][k]*l[j][k];
        if(i==j){{if(!(v>1e-12))throw new IllegalArgumentException("Not SPD");l[i][j]=Math.sqrt(v);}}
        else l[i][j]=v/l[j][j];
      }}
    }}return l;
  }}
  private static double[] solve(double[][] l,double[] rhs){{
    int n=rhs.length;double[] z=rhs.clone();
    for(int i=0;i<n;i++){{for(int j=0;j<i;j++)z[i]-=l[i][j]*z[j];z[i]/=l[i][i];}}
    for(int i=n-1;i>=0;i--){{for(int j=i+1;j<n;j++)z[i]-=l[j][i]*z[j];z[i]/=l[i][i];}}return z;
  }}
  public static double[] {fn}(double[][] cov,double[] market,double delta,double tau,double[][] p,double[] q,double[] omega){{
    if(cov==null||p==null||market==null||q==null||omega==null)throw new IllegalArgumentException("Null input");
    int n=cov.length,m=p.length;
    if(n<2||n>128||m<1||m>128||market.length!=n||q.length!=m||omega.length!=m||
       !Double.isFinite(delta)||!Double.isFinite(tau)||delta<=0||tau<=0)throw new IllegalArgumentException("Invalid dimensions");
    double wsum=0;for(double v:market){{if(!Double.isFinite(v))throw new IllegalArgumentException("Nonfinite market");wsum+=v;}}
    if(Math.abs(wsum-1)>1.00001e-5)throw new IllegalArgumentException("Market sum");
    for(int i=0;i<n;i++){{if(cov[i]==null||cov[i].length!=n)throw new IllegalArgumentException("Covariance shape");for(double v:cov[i])if(!Double.isFinite(v))throw new IllegalArgumentException("Covariance invalid");}}
    for(int k=0;k<m;k++){{if(p[k]==null||p[k].length!=n||!Double.isFinite(q[k])||!Double.isFinite(omega[k])||omega[k]<=0)throw new IllegalArgumentException("View shape");for(double v:p[k])if(!Double.isFinite(v))throw new IllegalArgumentException("Nonfinite views");}}
    chol(cov);
    double[] prior=new double[n],post=new double[n];double[][] b=new double[n][m],a=new double[m][m];
    for(int i=0;i<n;i++)for(int j=0;j<n;j++)prior[i]+=delta*cov[i][j]*market[j];
    for(int i=0;i<n;i++)for(int k=0;k<m;k++)for(int j=0;j<n;j++)b[i][k]+=tau*cov[i][j]*p[k][j];
    for(int k=0;k<m;k++)for(int h=0;h<m;h++){{a[k][h]=(k==h)?omega[k]:0;for(int j=0;j<n;j++)a[k][h]+=p[k][j]*b[j][h];}}
    double[][] l=chol(a);double[] residual=q.clone();
    for(int k=0;k<m;k++)for(int j=0;j<n;j++)residual[k]-=p[k][j]*prior[j];
    double[] shift=solve(l,residual),out=new double[2*n+n*n];
    for(int i=0;i<n;i++){{post[i]=prior[i];for(int k=0;k<m;k++)post[i]+=b[i][k]*shift[k];out[i]=prior[i];out[n+i]=post[i];}}
    for(int j=0;j<n;j++){{double[] rhs=new double[m];for(int k=0;k<m;k++)rhs[k]=b[j][k];double[] z=solve(l,rhs);
      for(int i=0;i<n;i++){{double v=(1+tau)*cov[i][j];for(int k=0;k<m;k++)v-=b[i][k]*z[k];out[2*n+i*n+j]=v;}}}}
    return out;
  }}
}}
'''
    if lang == 'C#':
        return f'''// {note}
using System;
public static class GeneratedCalculator {{
  private static double[,] Chol(double[,] a){{
    int n=a.GetLength(0);var l=new double[n,n];
    for(int i=0;i<n;i++){{
      for(int j=0;j<n;j++)if(!double.IsFinite(a[i,j])||Math.Abs(a[i,j]-a[j,i])>1e-9+1e-5*Math.Abs(a[j,i]))throw new ArgumentException("Asymmetric matrix");
      for(int j=0;j<=i;j++){{double v=a[i,j];for(int k=0;k<j;k++)v-=l[i,k]*l[j,k];
        if(i==j){{if(!(v>1e-12))throw new ArgumentException("Not SPD");l[i,j]=Math.Sqrt(v);}}
        else l[i,j]=v/l[j,j];
      }}
    }}return l;
  }}
  private static double[] Solve(double[,] l,double[] rhs){{
    int n=rhs.Length;var z=(double[])rhs.Clone();
    for(int i=0;i<n;i++){{for(int j=0;j<i;j++)z[i]-=l[i,j]*z[j];z[i]/=l[i,i];}}
    for(int i=n-1;i>=0;i--){{for(int j=i+1;j<n;j++)z[i]-=l[j,i]*z[j];z[i]/=l[i,i];}}return z;
  }}
  public static double[] {fn}(double[,] cov,double[] market,double delta,double tau,double[,] p,double[] q,double[] omega){{
    if(cov==null||market==null||p==null||q==null||omega==null)throw new ArgumentException("Null input");
    int n=cov.GetLength(0),m=p.GetLength(0);
    if(n<2||n>128||cov.GetLength(1)!=n||m<1||m>128||p.GetLength(1)!=n||
       market.Length!=n||q.Length!=m||omega.Length!=m||!double.IsFinite(delta)||!double.IsFinite(tau)||delta<=0||tau<=0)throw new ArgumentException("Invalid dimensions");
    double weightSum=0;foreach(double x in market){{if(!double.IsFinite(x))throw new ArgumentException("Invalid market");weightSum+=x;}}
    if(Math.Abs(weightSum-1)>1.00001e-5)throw new ArgumentException("Market sum");
    foreach(double x in cov)if(!double.IsFinite(x))throw new ArgumentException("Invalid covariance");
    foreach(double x in p)if(!double.IsFinite(x))throw new ArgumentException("Invalid view matrix");
    for(int i=0;i<m;i++)if(!double.IsFinite(q[i])||!double.IsFinite(omega[i])||omega[i]<=0)throw new ArgumentException("Invalid views");
    Chol(cov);
    var prior=new double[n];var post=new double[n];var b=new double[n,m];var a=new double[m,m];
    for(int i=0;i<n;i++)for(int j=0;j<n;j++)prior[i]+=delta*cov[i,j]*market[j];
    for(int i=0;i<n;i++)for(int k=0;k<m;k++)for(int j=0;j<n;j++)b[i,k]+=tau*cov[i,j]*p[k,j];
    for(int k=0;k<m;k++)for(int h=0;h<m;h++){{a[k,h]=(k==h)?omega[k]:0;for(int j=0;j<n;j++)a[k,h]+=p[k,j]*b[j,h];}}
    var l=Chol(a);var residual=(double[])q.Clone();
    for(int k=0;k<m;k++)for(int j=0;j<n;j++)residual[k]-=p[k,j]*prior[j];
    var shift=Solve(l,residual);var output=new double[2*n+n*n];
    for(int i=0;i<n;i++){{post[i]=prior[i];for(int k=0;k<m;k++)post[i]+=b[i,k]*shift[k];output[i]=prior[i];output[n+i]=post[i];}}
    for(int j=0;j<n;j++){{var rhs=new double[m];for(int k=0;k<m;k++)rhs[k]=b[j,k];var z=Solve(l,rhs);
      for(int i=0;i<n;i++){{double v=(1+tau)*cov[i,j];for(int k=0;k<m;k++)v-=b[i,k]*z[k];output[2*n+i*n+j]=v;}}}}
    return output;
  }}
}}
'''
    if lang == 'Swift':
        return f'''// {note}
import Foundation
enum BlackLittermanError: Error {{case invalidInput}}
func {fn}(_ cov: [[Double]],_ market: [Double],_ delta: Double,_ tau: Double,_ p: [[Double]],_ q: [Double],_ omega: [Double]) throws -> [Double] {{
  let n=cov.count,m=p.count
  guard n>=2 && n<=128 && m>=1 && m<=128 && market.count==n && q.count==m && omega.count==m &&
    delta.isFinite && tau.isFinite && delta>0 && tau>0 && market.allSatisfy({{$0.isFinite}}) &&
    abs(market.reduce(0,+)-1)<=1.00001e-5 && q.allSatisfy({{$0.isFinite}}) &&
    omega.allSatisfy({{$0.isFinite && $0>0}}) &&
    cov.allSatisfy({{$0.count==n && $0.allSatisfy({{$0.isFinite}})}}) &&
    p.allSatisfy({{$0.count==n && $0.allSatisfy({{$0.isFinite}})}}) else {{throw BlackLittermanError.invalidInput}}
  func chol(_ a: [[Double]]) throws -> [[Double]] {{
    let size=a.count
    var l=Array(repeating:Array(repeating:0.0,count:size),count:size)
    for i in 0..<size {{
      for j in 0..<size {{if !a[i][j].isFinite || abs(a[i][j]-a[j][i])>1e-9+1e-5*abs(a[j][i]) {{throw BlackLittermanError.invalidInput}}}}
      for j in 0...i {{var v=a[i][j];if j>0 {{for k in 0..<j {{v-=l[i][k]*l[j][k]}}}}
        if i==j {{guard v>1e-12 else {{throw BlackLittermanError.invalidInput}};l[i][j]=sqrt(v)}}
        else {{l[i][j]=v/l[j][j]}}
      }}
    }}
    return l
  }}
  func solve(_ l: [[Double]],_ rhs: [Double]) -> [Double] {{
    let size=rhs.count;var z=rhs
    for i in 0..<size {{if i>0 {{for j in 0..<i {{z[i]-=l[i][j]*z[j]}}}};z[i]/=l[i][i]}}
    for i in (0..<size).reversed() {{if i+1<size {{for j in (i+1)..<size {{z[i]-=l[j][i]*z[j]}}}};z[i]/=l[i][i]}}
    return z
  }}
  _ = try chol(cov)
  var prior=Array(repeating:0.0,count:n),post=Array(repeating:0.0,count:n)
  var b=Array(repeating:Array(repeating:0.0,count:m),count:n)
  var a=Array(repeating:Array(repeating:0.0,count:m),count:m)
  for i in 0..<n {{for j in 0..<n {{prior[i]+=delta*cov[i][j]*market[j]}}}}
  for i in 0..<n {{for k in 0..<m {{for j in 0..<n {{b[i][k]+=tau*cov[i][j]*p[k][j]}}}}}}
  for k in 0..<m {{for h in 0..<m {{a[k][h]=k==h ? omega[k] : 0;for j in 0..<n {{a[k][h]+=p[k][j]*b[j][h]}}}}}}
  let l=try chol(a);var residual=q
  for k in 0..<m {{for j in 0..<n {{residual[k]-=p[k][j]*prior[j]}}}}
  let shift=solve(l,residual)
  var output=Array(repeating:0.0,count:2*n+n*n)
  for i in 0..<n {{post[i]=prior[i];for k in 0..<m {{post[i]+=b[i][k]*shift[k]}};output[i]=prior[i];output[n+i]=post[i]}}
  for j in 0..<n {{var rhs=Array(repeating:0.0,count:m);for k in 0..<m {{rhs[k]=b[j][k]}};let z=solve(l,rhs)
    for i in 0..<n {{var v=(1+tau)*cov[i][j];for k in 0..<m {{v-=b[i][k]*z[k]}};output[2*n+i*n+j]=v}}}}
  return output
}}
'''
    if lang == 'Kotlin':
        return f'''// {note}
import kotlin.math.*
fun {fn}(cov:Array<DoubleArray>,market:DoubleArray,delta:Double,tau:Double,p:Array<DoubleArray>,q:DoubleArray,omega:DoubleArray):DoubleArray {{
  val n=cov.size;val m=p.size
  require(n in 2..128 && m in 1..128 && market.size==n && q.size==m && omega.size==m &&
    delta.isFinite() && tau.isFinite() && delta>0 && tau>0 && market.all{{it.isFinite()}} &&
    abs(market.sum()-1)<=1.00001e-5 && q.all{{it.isFinite()}} && omega.all{{it.isFinite() && it>0}} &&
    cov.all{{it.size==n && it.all{{x->x.isFinite()}}}} && p.all{{it.size==n && it.all{{x->x.isFinite()}}}})
  fun chol(a:Array<DoubleArray>):Array<DoubleArray> {{
    val size=a.size;val l=Array(size){{DoubleArray(size)}}
    for(i in 0 until size){{
      for(j in 0 until size)require(a[i][j].isFinite() && abs(a[i][j]-a[j][i])<=1e-9+1e-5*abs(a[j][i]))
      for(j in 0..i){{var v=a[i][j];for(k in 0 until j)v-=l[i][k]*l[j][k]
        if(i==j){{require(v>1e-12);l[i][j]=sqrt(v)}}else l[i][j]=v/l[j][j]
      }}
    }}
    return l
  }}
  fun solve(l:Array<DoubleArray>,rhs:DoubleArray):DoubleArray {{
    val size=rhs.size;val z=rhs.copyOf()
    for(i in 0 until size){{for(j in 0 until i)z[i]-=l[i][j]*z[j];z[i]/=l[i][i]}}
    for(i in size-1 downTo 0){{for(j in i+1 until size)z[i]-=l[j][i]*z[j];z[i]/=l[i][i]}}
    return z
  }}
  chol(cov)
  val prior=DoubleArray(n);val post=DoubleArray(n);val b=Array(n){{DoubleArray(m)}};val a=Array(m){{DoubleArray(m)}}
  for(i in 0 until n)for(j in 0 until n)prior[i]+=delta*cov[i][j]*market[j]
  for(i in 0 until n)for(k in 0 until m)for(j in 0 until n)b[i][k]+=tau*cov[i][j]*p[k][j]
  for(k in 0 until m)for(h in 0 until m){{a[k][h]=if(k==h)omega[k] else 0.0;for(j in 0 until n)a[k][h]+=p[k][j]*b[j][h]}}
  val l=chol(a);val residual=q.copyOf()
  for(k in 0 until m)for(j in 0 until n)residual[k]-=p[k][j]*prior[j]
  val shift=solve(l,residual);val output=DoubleArray(2*n+n*n)
  for(i in 0 until n){{post[i]=prior[i];for(k in 0 until m)post[i]+=b[i][k]*shift[k];output[i]=prior[i];output[n+i]=post[i]}}
  for(j in 0 until n){{val rhs=DoubleArray(m){{k->b[j][k]}};val z=solve(l,rhs)
    for(i in 0 until n){{var v=(1+tau)*cov[i][j];for(k in 0 until m)v-=b[i][k]*z[k];output[2*n+i*n+j]=v}}}}
  return output
}}
'''
    if lang == 'Go':
        return f'''// {note} Returns nil on invalid inputs.
package main
import "math"
func {fn}(cov [][]float64,market []float64,delta,tau float64,p [][]float64,q,omega []float64) []float64 {{
  n,m:=len(cov),len(p)
  valid:=func(v float64)bool{{return !math.IsNaN(v)&&!math.IsInf(v,0)}}
  if n<2||n>128||m<1||m>128||len(market)!=n||len(q)!=m||len(omega)!=m||!valid(delta)||!valid(tau)||delta<=0||tau<=0{{return nil}}
  weightSum:=0.0;for _,v:=range market{{if !valid(v){{return nil}};weightSum+=v}}
  if math.Abs(weightSum-1)>1.00001e-5{{return nil}}
  for i:=0;i<n;i++{{if len(cov[i])!=n{{return nil}};for _,v:=range cov[i]{{if !valid(v){{return nil}}}}}}
  for k:=0;k<m;k++{{if len(p[k])!=n||!valid(q[k])||!valid(omega[k])||omega[k]<=0{{return nil}};for _,v:=range p[k]{{if !valid(v){{return nil}}}}}}
  chol:=func(a [][]float64)[][]float64{{size:=len(a);l:=make([][]float64,size);for i:=range l{{l[i]=make([]float64,size)}}
    for i:=0;i<size;i++{{
      for j:=0;j<size;j++{{if !valid(a[i][j])||math.Abs(a[i][j]-a[j][i])>1e-9+1e-5*math.Abs(a[j][i]){{return nil}}}}
      for j:=0;j<=i;j++{{v:=a[i][j];for k:=0;k<j;k++{{v-=l[i][k]*l[j][k]}}
        if i==j{{if !(v>1e-12){{return nil}};l[i][j]=math.Sqrt(v)}}else{{l[i][j]=v/l[j][j]}}
      }}
    }}
    return l
  }}
  solve:=func(l [][]float64,rhs []float64)[]float64{{size:=len(rhs);z:=append([]float64(nil),rhs...)
    for i:=0;i<size;i++{{for j:=0;j<i;j++{{z[i]-=l[i][j]*z[j]}};z[i]/=l[i][i]}}
    for i:=size-1;i>=0;i--{{for j:=i+1;j<size;j++{{z[i]-=l[j][i]*z[j]}};z[i]/=l[i][i]}};return z
  }}
  if chol(cov)==nil{{return nil}}
  prior,post:=make([]float64,n),make([]float64,n)
  b,a:=make([][]float64,n),make([][]float64,m)
  for i:=range b{{b[i]=make([]float64,m)}};for k:=range a{{a[k]=make([]float64,m)}}
  for i:=0;i<n;i++{{for j:=0;j<n;j++{{prior[i]+=delta*cov[i][j]*market[j]}}}}
  for i:=0;i<n;i++{{for k:=0;k<m;k++{{for j:=0;j<n;j++{{b[i][k]+=tau*cov[i][j]*p[k][j]}}}}}}
  for k:=0;k<m;k++{{for h:=0;h<m;h++{{if k==h{{a[k][h]=omega[k]}};for j:=0;j<n;j++{{a[k][h]+=p[k][j]*b[j][h]}}}}}}
  l:=chol(a);if l==nil{{return nil}}
  residual:=append([]float64(nil),q...)
  for k:=0;k<m;k++{{for j:=0;j<n;j++{{residual[k]-=p[k][j]*prior[j]}}}}
  shift:=solve(l,residual);out:=make([]float64,2*n+n*n)
  for i:=0;i<n;i++{{post[i]=prior[i];for k:=0;k<m;k++{{post[i]+=b[i][k]*shift[k]}};out[i]=prior[i];out[n+i]=post[i]}}
  for j:=0;j<n;j++{{rhs:=make([]float64,m);for k:=0;k<m;k++{{rhs[k]=b[j][k]}};z:=solve(l,rhs)
    for i:=0;i<n;i++{{v:=(1+tau)*cov[i][j];for k:=0;k<m;k++{{v-=b[i][k]*z[k]}};out[2*n+i*n+j]=v}}}}
  return out
}}
'''
    if lang == 'Rust':
        return f'''// {note}
pub fn {fn}(cov:&[Vec<f64>],market:&[f64],delta:f64,tau:f64,p:&[Vec<f64>],q:&[f64],omega:&[f64])->Result<Vec<f64>,&'static str>{{
  let n=cov.len();let m=p.len();
  if n<2||n>128||m<1||m>128||market.len()!=n||q.len()!=m||omega.len()!=m||
     !delta.is_finite()||!tau.is_finite()||delta<=0.0||tau<=0.0||
     market.iter().any(|v|!v.is_finite())||(market.iter().sum::<f64>()-1.0).abs()>1.00001e-5||
     q.iter().any(|v|!v.is_finite())||omega.iter().any(|v|!v.is_finite()||*v<=0.0)||
     cov.iter().any(|row|row.len()!=n||row.iter().any(|v|!v.is_finite()))||
     p.iter().any(|row|row.len()!=n||row.iter().any(|v|!v.is_finite())){{return Err("Invalid dimensions/inputs");}}
  fn chol(a:&[Vec<f64>])->Result<Vec<Vec<f64>>,&'static str>{{
    let size=a.len();let mut l=vec![vec![0.0;size];size];
    for i in 0..size{{
      for j in 0..size{{if !a[i][j].is_finite()||(a[i][j]-a[j][i]).abs()>1e-9+1e-5*a[j][i].abs(){{return Err("Asymmetric matrix");}}}}
      for j in 0..=i{{let mut v=a[i][j];for k in 0..j{{v-=l[i][k]*l[j][k];}}
        if i==j{{if !(v>1e-12){{return Err("Not SPD");}}l[i][j]=v.sqrt();}}else{{l[i][j]=v/l[j][j];}}
      }}
    }}Ok(l)
  }}
  fn solve(l:&[Vec<f64>],rhs:&[f64])->Vec<f64>{{
    let size=rhs.len();let mut z=rhs.to_vec();
    for i in 0..size{{for j in 0..i{{z[i]-=l[i][j]*z[j];}}z[i]/=l[i][i];}}
    for i in (0..size).rev(){{for j in (i+1)..size{{z[i]-=l[j][i]*z[j];}}z[i]/=l[i][i];}}z
  }}
  let _=chol(cov)?;
  let mut prior=vec![0.0;n];let mut post=vec![0.0;n];
  let mut b=vec![vec![0.0;m];n];let mut a=vec![vec![0.0;m];m];
  for i in 0..n{{for j in 0..n{{prior[i]+=delta*cov[i][j]*market[j];}}}}
  for i in 0..n{{for k in 0..m{{for j in 0..n{{b[i][k]+=tau*cov[i][j]*p[k][j];}}}}}}
  for k in 0..m{{for h in 0..m{{a[k][h]=if k==h{{omega[k]}}else{{0.0}};for j in 0..n{{a[k][h]+=p[k][j]*b[j][h];}}}}}}
  let l=chol(&a)?;let mut residual=q.to_vec();
  for k in 0..m{{for j in 0..n{{residual[k]-=p[k][j]*prior[j];}}}}
  let shift=solve(&l,&residual);let mut out=vec![0.0;2*n+n*n];
  for i in 0..n{{post[i]=prior[i];for k in 0..m{{post[i]+=b[i][k]*shift[k];}}out[i]=prior[i];out[n+i]=post[i];}}
  for j in 0..n{{let rhs:Vec<f64>=(0..m).map(|k|b[j][k]).collect();let z=solve(&l,&rhs);
    for i in 0..n{{let mut v=(1.0+tau)*cov[i][j];for k in 0..m{{v-=b[i][k]*z[k];}}out[2*n+i*n+j]=v;}}}}
  Ok(out)
}}
'''
    raise GenerationError(f'Black-Litterman adapter for {lang} not yet implemented')
