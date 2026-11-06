// HyunCalculator STRAT-002: output flat [net compounded,gross compounded,buyhold compounded,CAGR,vol,Sharpe,Sortino,MDD,active win rate,executed changes,total turnover,total cost,positions(n),net(n),equity(n+1),buyhold(n+1)]. Signals delayed 1 period; no final liquidation.
export function backtest(r, sig, commission, slippage, rf, ppy){
  if(!Array.isArray(r)||!Array.isArray(sig)||r.length<3||r.length>100000||sig.length!==r.length||![commission,slippage,rf].every(Number.isFinite)||commission<0||slippage<0||!Number.isInteger(ppy)||ppy<1||ppy>1000000)throw new RangeError("Invalid backtest inputs");
  const n=r.length;for(let t=0;t<n;t++)if(!Number.isFinite(r[t])||r[t]<=-1||!Number.isFinite(sig[t])||Math.abs(sig[t])>1)throw new RangeError("Invalid series");
  const out=Array(4*n+14).fill(0);out[12+2*n]=1;out[13+3*n]=1;
  let netW=1,grossW=1,buyW=1,peak=1,mdd=0,prev=0,turnTotal=0,costTotal=0,sum=0,down=0,active=0,wins=0,changes=0;
  for(let t=0;t<n;t++){const pos=t?sig[t-1]:0,turn=Math.abs(pos-prev),cost=turn*(commission+slippage)/10000,gross=pos*r[t],net=gross-cost;
    if(net<=-1||!Number.isFinite(net))throw new RangeError("Invalid net return");
    out[12+t]=pos;out[12+n+t]=net;prev=pos;netW*=1+net;grossW*=1+gross;buyW*=1+r[t];out[12+2*n+t+1]=netW;out[13+3*n+t+1]=buyW;
    peak=Math.max(peak,netW);mdd=Math.min(mdd,netW/peak-1);sum+=net;const d=Math.min(net-rf,0);down+=d*d;turnTotal+=turn;costTotal+=cost;
    if(turn>1e-12)changes++;if(Math.abs(pos)>1e-12){active++;if(net>0)wins++;}
  }
  const avg=sum/n,ex=avg-rf;let sq=0;for(let t=0;t<n;t++){const e=out[12+n+t]-avg;sq+=e*e;}
  const st=Math.sqrt(sq/(n-1)),dv=Math.sqrt(down/n),annual=Math.sqrt(ppy);
  const values=[netW-1,grossW-1,buyW-1,Math.pow(netW,ppy/n)-1,st*annual,st>0?ex/st*annual:NaN,dv>0?ex/dv*annual:NaN,mdd,active?wins/active:NaN,changes,turnTotal,costTotal];
  for(let i=0;i<12;i++)out[i]=values[i];return out;
}
