// HyunCalculator PORT-001: [Expected return, Volatility, Sharpe ratio]. Covariance SPD; weights sum to 1.
export function portfolio(w, mu, cov, rf=0) {
  const n=w?.length;
  if(!Array.isArray(w)||n<2||!Array.isArray(mu)||mu.length!==n||!Array.isArray(cov)||cov.length!==n||!Number.isFinite(rf))throw new RangeError("Invalid portfolio shape");
  let total=0,ret=0,variance=0;
  for(let i=0;i<n;i++){
    if(!Number.isFinite(w[i])||!Number.isFinite(mu[i])||!Array.isArray(cov[i])||cov[i].length!==n)throw new RangeError("Invalid portfolio arrays");
    total+=w[i];ret+=w[i]*mu[i];
    for(let j=0;j<n;j++){if(!Number.isFinite(cov[i][j]))throw new RangeError("Nonfinite covariance");variance+=w[i]*cov[i][j]*w[j];}
  }
  if(Math.abs(total-1)>1.001e-5)throw new RangeError("Invalid weights");
  const lower=Array.from({length:n},()=>new Array(n).fill(0));
  for(let i=0;i<n;i++){
    for(let j=0;j<n;j++)if(Math.abs(cov[i][j]-cov[j][i])>1e-9+1e-5*Math.abs(cov[j][i]))throw new RangeError("Asymmetric covariance");
    for(let j=0;j<=i;j++){let v=cov[i][j];for(let k=0;k<j;k++)v-=lower[i][k]*lower[j][k];
      if(i===j){if(!(v>1e-12))throw new RangeError("Non SPD covariance");lower[i][j]=Math.sqrt(v);}
      else lower[i][j]=v/lower[j][j];}
  }
  const vol=Math.sqrt(Math.max(variance,0));return [ret,vol,vol>0?(ret-rf)/vol:NaN];
}
