
// European antithetic Monte Carlo; Park-Miller 16807 + Box-Muller, pair-based SE and 95% CI. Portable seed must be 1..2147483646; RNG differs from Python/NumPy PCG64. Results: price, paired SE, CI low/high.
export function mc(s,k,t,r,sigma,q,option,paths,seed) {
    if (!Number.isFinite(s)||!Number.isFinite(k)||!Number.isFinite(t)||!Number.isFinite(r)||!Number.isFinite(sigma)||!Number.isFinite(q)||s<=0||k<=0||t<=0||sigma<0||paths<100||paths>1000000||paths%2!=0||seed<1||seed>=2147483647||(option!=="call" && option!=="put")||!Number.isSafeInteger(paths)||!Number.isSafeInteger(seed)) { throw new RangeError("Invalid Monte Carlo inputs"); }
    const sign = (option==="call" ? 1.0 : -1.0);
    const drift = (r-q-0.5*sigma*sigma)*t;
    const volStep = sigma*Math.sqrt(t);
    const disc = Math.exp(-r*t);
    let state = seed;
    let mean = 0.0;
    let m2 = 0.0;
    let pairs = paths/2;
    for (let i=1;i<=pairs;++i) {
        state = (state*16807) % 2147483647;
        const u1 = state/2147483647.0;
        state = (state*16807) % 2147483647;
        const u2 = state/2147483647.0;
        const z = Math.sqrt(-2.0*Math.log(u1))*Math.cos(6.283185307179586*u2);
        const st1 = s*Math.exp(drift+volStep*z);
        const st2 = s*Math.exp(drift-volStep*z);
        const pair = 0.5*disc*(Math.max(0.0,sign*(st1-k))+Math.max(0.0,sign*(st2-k)));
        const delta = pair-mean;
        mean += delta/i;
        m2 += delta*(pair-mean);
    }
    const se = Math.sqrt((m2/(pairs-1))/pairs);
    return [mean,se,mean-1.96*se,mean+1.96*se];
}
