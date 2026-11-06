// HyunCalculator STAT-001: output [Z, PDF, CDF, survival, inverse-CDF]. Normal-CDF approximation abs error usually < 8e-8; PPF uses Acklam (~1e-9).
function hyun_normal_ppf(p) {
    let z=0, q=0, z2=0;
    if(p<0.02425) { q=Math.sqrt(-2*Math.log(p)); z=((((((-0.007784894002430293*q+(-0.3223964580411365))*q+(-2.400758277161838))*q+(-2.549732539343734))*q+(4.374664141464968))*q+(2.938163982698783)))/(((((0.007784695709041462*q+(0.3224671290700398))*q+(2.445134137142996))*q+(3.754408661907416))*q+(1.0))); }
    else if(p>0.97575) { q=Math.sqrt(-2*Math.log(1-p)); z=-(((((((-0.007784894002430293*q+(-0.3223964580411365))*q+(-2.400758277161838))*q+(-2.549732539343734))*q+(4.374664141464968))*q+(2.938163982698783)))/(((((0.007784695709041462*q+(0.3224671290700398))*q+(2.445134137142996))*q+(3.754408661907416))*q+(1.0)))); }
    else { z=p-0.5; z2=z*z; z=((((((-39.69683028665376*z2+(220.9460984245205))*z2+(-275.9285104469687))*z2+(138.357751867269))*z2+(-30.66479806614716))*z2+(2.506628277459239))*z)/((((((-54.47609879822406*z2+(161.5858368580409))*z2+(-155.6989798598866))*z2+(66.80131188771972))*z2+(-13.28068155288572))*z2+(1.0))); }
    return z;
}
function hyun_normal_cdf(z) {
    const p0=1/(1+0.2316419*Math.abs(z));
    const tail=0.3989422804014327*Math.exp(-0.5*z*z)*p0*(0.319381530+p0*(-0.356563782+p0*(1.781477937+p0*(-1.821255978+p0*1.330274429))));
    return z>=0 ? 1-tail : tail;
}
export function normal(x, mean, sd, p) {
    if(!Number.isFinite(x)||!Number.isFinite(mean)||!Number.isFinite(sd)||!Number.isFinite(p)||sd<=0||p<=0||p>=1) throw new RangeError("Invalid normal inputs");
    const z=(x-mean)/sd;
    const density=Math.exp(-0.5*z*z)*0.3989422804014327/sd;
    const cdf=hyun_normal_cdf(z);
    return [z,density,cdf,1-cdf,mean+sd*hyun_normal_ppf(p)];
}
