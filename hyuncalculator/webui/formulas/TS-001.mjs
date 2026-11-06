// HyunCalculator TS-001 result order: [EWMA variance, EWMA volatility]
export function ewma(r, decay) {
  if(!Array.isArray(r)||r.length<2||!r.every(Number.isFinite)||!Number.isFinite(decay)||decay<0||decay>=1) throw new RangeError("Invalid EWMA inputs");
  let v=r[0]*r[0];
  for(let i=1;i<r.length;i++) v=decay*v+(1-decay)*r[i]*r[i];
  return [v,Math.sqrt(v)];
}
