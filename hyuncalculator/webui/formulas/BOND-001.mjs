// HyunCalculator BOND-001 result order: [Price, Macaulay, Modified, Convexity]
export function bond(face, coupon, yield_rate, years, freq) {
  if (![face,coupon,yield_rate,years,freq].every(Number.isFinite) || face<=0 || years<=0 || !Number.isInteger(freq) || freq<1 || yield_rate/freq<=-1) throw new RangeError("Invalid bond inputs");
  const periods=years*freq;
  if (!Number.isFinite(periods)||periods<1||Math.abs(periods-Math.round(periods))>1e-8||periods>1000000) throw new RangeError("Invalid coupon periods");
  const n=Math.round(periods), y=yield_rate/freq;
  let price=0, weighted=0, curved=0;
  for(let i=1;i<=n;i++) {
    const cash=face*coupon/freq+(i===n?face:0), pv=cash/Math.pow(1+y,i);
    price+=pv; weighted+=i*pv; curved+=i*(i+1)*pv;
  }
  if(!Number.isFinite(price)||price===0) throw new RangeError("Invalid sensitivity");
  const mac=weighted/price/freq;
  return [price,mac,mac/(1+y),curved/(price*freq*freq*Math.pow(1+y,2))];
}
