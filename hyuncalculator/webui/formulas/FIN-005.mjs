// HyunCalculator FIN-005: scan 680 rates, bisect brackets, reject multiple IRRs. Returns annual/per-period rate as decimal.
export function calculate_irr(flows) {
  if(!Array.isArray(flows)||flows.length<2||flows.length>10000||!flows.every(Number.isFinite)||!flows.some(x=>x>0)||!flows.some(x=>x<0)) throw new RangeError("Invalid IRR cashflows");
  const valueAt=(rate)=>{let result=flows[flows.length-1],factor=1/(1+rate);for(let j=flows.length-2;j>=0;j--)result=result*factor+flows[j];return result;};
  const roots=[];let prev=0,prevval=0,hasprev=false;
  for(let i=0;i<680;i++){
    const rate=i<80?(-0.9999+0.0999*i/79):i<480?(-0.9+1.9*(i-80)/399):Math.exp(Math.log(2)+Math.log(50000)*(i-480)/199);
    const val=valueAt(rate);if(!Number.isFinite(val)){hasprev=false;continue;}
    let root=NaN;
    if(val===0)root=rate;
    else if(hasprev&&((prevval<0&&val>0)||(prevval>0&&val<0))){
      let lo=prev,hi=rate,fl=prevval;
      for(let j=0;j<120;j++){const mid=(lo+hi)/2,fm=valueAt(mid);if(fm===0){lo=hi=mid;break;}if((fl<0&&fm<0)||(fl>0&&fm>0)){lo=mid;fl=fm;}else hi=mid;}
      root=(lo+hi)/2;
    }
    if(Number.isFinite(root)&&!roots.some(x=>Math.abs(x-root)<1e-7)){roots.push(root);if(roots.length>1)throw new RangeError("Multiple IRRs");}
    prev=rate;prevval=val;hasprev=true;
  }
  if(roots.length!==1)throw new RangeError("No unique IRR");return roots[0];
}
