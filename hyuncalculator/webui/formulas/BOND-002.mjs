// HyunCalculator BOND-002: nominal YTM from dirty price
export function ytm(price,face,coupon,years,freq) {
  if(![price,face,coupon,years,freq].every(Number.isFinite)||price<=0||face<=0||coupon<0||years<=0||!Number.isInteger(freq)||freq<1) throw new RangeError("Invalid bond inputs");
  const periods=years*freq;
  if(!Number.isFinite(periods)||periods<1||periods>2400||Math.abs(periods-Math.round(periods))>1e-8) throw new RangeError("Invalid coupon periods");
  const n=Math.round(periods);
  if(coupon===0) return freq*(Math.pow(face/price,1/n)-1);
  const priceAt=(y) => {
    const a=y/freq;
    if(a<=-1) return Infinity;
    if(Math.abs(a)<1e-14) return face+face*coupon/freq*n;
    const df=Math.pow(1+a,-n);
    return face*df+face*coupon/freq*(1-df)/a;
  };
  let lo=-freq*(1-1e-8),hi=Math.max(1,coupon);
  for(let i=0;i<100&&priceAt(hi)>price;i++)hi*=2;
  if(priceAt(hi)>price)throw new RangeError("Unable to bracket yield");
  for(let i=0;i<220;i++){const mid=(lo+hi)/2;if(priceAt(mid)>price)lo=mid;else hi=mid;}
  return (lo+hi)/2;
}
