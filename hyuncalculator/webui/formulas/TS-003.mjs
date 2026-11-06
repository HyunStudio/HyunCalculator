// HyunCalculator TS-003: SMA complete windows, EMA seeded by first sample; [lastSMA,lastEMA,SMA series,EMA series]
export function moving(values, window) {
  if(!Array.isArray(values)||!values.length||!values.every(Number.isFinite)||!Number.isInteger(window)||window<1||window>values.length)throw new RangeError("Invalid moving-average inputs");
  const n=values.length,sma=new Array(n-window+1),ema=new Array(n);
  let acc=0;for(let i=0;i<window;i++)acc+=values[i];sma[0]=acc/window;
  for(let i=window;i<n;i++){acc+=values[i]-values[i-window];sma[i-window+1]=acc/window;}
  const alpha=2/(window+1);ema[0]=values[0];
  for(let i=1;i<n;i++)ema[i]=alpha*values[i]+(1-alpha)*ema[i-1];
  return {lastSMA:sma[sma.length-1],lastEMA:ema[n-1],sma,ema};
}
