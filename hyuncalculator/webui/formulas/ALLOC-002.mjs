// HyunCalculator Markowitz: fully invested, short positions allowed; covariance must be symmetric positive definite. Output=[weights...,variance/expected_return].
export function target_portfolio(mu, cov, target) {
  if(!Array.isArray(cov)||cov.length<2||cov.length>2048)throw new RangeError("Invalid covariance");
  const n=cov.length;
  if(!Array.isArray(mu)||mu.length!==n||!mu.every(Number.isFinite)||!Number.isFinite(target))throw new RangeError("Invalid target");
  const l=Array.from({length:n},()=>new Array(n).fill(0));
  for(let i=0;i<n;i++){if(!Array.isArray(cov[i])||cov[i].length!==n||!cov[i].every(Number.isFinite))throw new RangeError("Nonfinite covariance");}
  for(let i=0;i<n;i++){
    for(let j=0;j<n;j++)if(Math.abs(cov[i][j]-cov[j][i])>1e-9+1e-5*Math.abs(cov[j][i]))throw new RangeError("Asymmetric covariance");
    for(let j=0;j<=i;j++){let v=cov[i][j];for(let k=0;k<j;k++)v-=l[i][k]*l[j][k];
      if(i===j){if(!(v>1e-12))throw new RangeError("Covariance not SPD");l[i][j]=Math.sqrt(v);}
      else l[i][j]=v/l[j][j];}
  }
  const solve=(rhs)=>{
    const v=rhs.slice();for(let i=0;i<n;i++){for(let j=0;j<i;j++)v[i]-=l[i][j]*v[j];v[i]/=l[i][i];}
    for(let i=n-1;i>=0;i--){for(let j=i+1;j<n;j++)v[i]-=l[j][i]*v[j];v[i]/=l[i][i];}
    return v;
  };
  const y=solve(new Array(n).fill(1)),a=y.reduce((s,v)=>s+v,0);
  if(!Number.isFinite(a)||a<=0)throw new RangeError("Invalid covariance");
  const z=solve(mu);let b=0,c=0;for(let i=0;i<n;i++){b+=z[i];c+=mu[i]*z[i];}
  const det=a*c-b*b;if(!Number.isFinite(det)||det<=1e-12)throw new RangeError("Expected returns must be distinct");
  const w=y.map((v,i)=>((c-b*target)/det)*v+((a*target-b)/det)*z[i]);
  return [...w,w.reduce((s,v,i)=>s+v*mu[i],0)];
}
