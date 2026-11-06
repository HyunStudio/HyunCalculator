// HyunCalculator RISK-003: [annual mean, annual vol, Sharpe, Sortino, maximum drawdown, compounded return]; simple returns per period, sample ddof=1.
export function performance(r, rf, ppy){
  if(!Array.isArray(r)||r.length<3||r.length>1000000||!Number.isFinite(rf)||!Number.isInteger(ppy)||ppy<1||ppy>1000000)throw new RangeError("Invalid performance inputs");
  const n=r.length;let total=0,ex=0,wealth=1,peak=1,mdd=0,down=0;
  for(const x of r){if(!Number.isFinite(x)||x<=-1)throw new RangeError("Invalid return");total+=x;ex+=x-rf;const d=Math.min(x-rf,0);down+=d*d;wealth*=1+x;peak=Math.max(peak,wealth);mdd=Math.min(mdd,wealth/peak-1);}
  const avg=ex/n;let sq=0;for(const x of r){const e=x-rf-avg;sq+=e*e;}
  const st=Math.sqrt(sq/(n-1)),dv=Math.sqrt(down/n),an=Math.sqrt(ppy);
  return [total/n*ppy,st*an,st>0?avg/st*an:NaN,dv>0?avg/dv*an:NaN,mdd,wealth-1];
}
