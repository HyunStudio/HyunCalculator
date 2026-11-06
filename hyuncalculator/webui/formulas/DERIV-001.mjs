// HyunCalculator DERIV-001: European Black-Scholes with continuous dividend; returns Price, Delta, Gamma, Vega (per 1.00 vol), Theta (per year), Rho (per 1.00 rate).
function hyun_cdf(x){
  if(x>8)return 1;
  if(x< -8)return 0;
  const a=Math.abs(x);let term=a,v=term;
  for(let i=1;i<500;i++){term*=a*a/(2*i+1);v+=term;if(term<=1e-16*v)break;}
  return .5+(x>=0?1:-1)*Math.exp(-.5*a*a)*0.39894228040143267794*v;
}
export function bs(s,k,t,r,sigma,q,option){
  if(![s,k,t,r,sigma,q].every(Number.isFinite)||s<=0||k<=0||t<0||sigma<0||(option!=="call"&&option!=="put"))throw new RangeError("Invalid Black-Scholes inputs");
  const sign=option==="call"?1:-1;
  if(t===0)return [Math.max(sign*(s-k),0),NaN,NaN,0,NaN,0];
  if(sigma===0){const call=Math.max(s*Math.exp(-q*t)-k*Math.exp(-r*t),0),put=Math.max(k*Math.exp(-r*t)-s*Math.exp(-q*t),0);
    return [sign===1?call:put,NaN,NaN,0,NaN,NaN];}
  const root=sigma*Math.sqrt(t),d1=(Math.log(s/k)+(r-q+.5*sigma*sigma)*t)/root,d2=d1-root;
  const dq=Math.exp(-q*t),dr=Math.exp(-r*t),pdf=Math.exp(-.5*d1*d1)*0.39894228040143267794;
  const price=Math.max(0, sign*(s*dq*hyun_cdf(sign*d1)-k*dr*hyun_cdf(sign*d2)));
  const delta=sign*dq*hyun_cdf(sign*d1),gamma=dq*pdf/(s*root),vega=s*dq*pdf*Math.sqrt(t);
  const theta=-s*dq*pdf*sigma/(2*Math.sqrt(t))+sign*q*s*dq*hyun_cdf(sign*d1)-sign*r*k*dr*hyun_cdf(sign*d2);
  const rho=sign*k*t*dr*hyun_cdf(sign*d2);
  return [price,delta,gamma,vega,theta,rho];
}
