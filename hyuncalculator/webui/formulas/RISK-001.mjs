// Historical VaR/ES: losses=-returns; type-7 linear quantile; tail includes losses >= VaR-1e-12. Result [VaR, ES].
export function hist_var(r, confidence) {
  if(!Array.isArray(r)||r.length<3||!r.every(Number.isFinite)||!Number.isFinite(confidence)||confidence<=0||confidence>=1) throw new RangeError("Invalid VaR inputs");
  const losses=r.map(x=>-x).sort((a,b)=>a-b);
  const h=(losses.length-1)*confidence,lo=Math.floor(h),hi=Math.ceil(h);
  const cutoff=losses[lo]+(h-lo)*(losses[hi]-losses[lo]);
  const tail=losses.filter(x=>x>=cutoff-1e-12);
  return [cutoff,tail.reduce((a,b)=>a+b,0)/tail.length];
}
