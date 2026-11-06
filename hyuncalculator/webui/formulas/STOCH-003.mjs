// HyunCalculator stochastic paths; Park-Miller 16807 + Box-Muller, seed 1..2147483646; different RNG from Python NumPy. Flat result: [theoretical_mean,theoretical_sd,simulated_mean,simulated_sd,first_path_at_t0,...,first_path_at_tN]; length steps+5.
export function brownian(years,steps,paths,seed,initial,mu,sigma) {
  if (!Number.isFinite(years)||!Number.isFinite(initial)||!Number.isFinite(mu)||!Number.isFinite(sigma)||years<0||steps<1||steps>5000||paths<2||paths>100000||steps*paths>2000000||seed<1||seed>=2147483647||!Number.isSafeInteger(steps)||!Number.isSafeInteger(paths)||!Number.isSafeInteger(seed)||sigma < 0) { throw new RangeError("Invalid stochastic inputs"); }
  const out = new Array(steps+5).fill(0.0);
  const dt=years/steps;
  const theoreticalMean=initial + mu*years;
  const theoreticalSd=sigma*Math.sqrt(years);
  const driftStep=mu*dt;
  const noiseStep=sigma*Math.sqrt(dt);
  let state=seed;
  let mean=0.0, m2=0.0;
  out[0]=theoreticalMean; out[1]=theoreticalSd;
  for (let p=0;p<paths;p++) {
    let value=initial;
    if(p===0) out[4]=value;
    for(let j=0;j<steps;j++) {
      state=(state*16807)%2147483647; const u1=state/2147483647.0;
      state=(state*16807)%2147483647; const u2=state/2147483647.0;
      const z=Math.sqrt(-2.0*Math.log(u1))*Math.cos(6.283185307179586*u2);
      value=value + driftStep + noiseStep*z;
      if(p===0) out[5+j]=value;
    }
    const delta=value-mean; mean+=delta/(p+1); m2+=delta*(value-mean);
  }
  out[2]=mean; out[3]=Math.sqrt(m2/(paths-1));
  return out;
}
