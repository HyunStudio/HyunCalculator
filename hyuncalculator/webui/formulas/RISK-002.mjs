// Normal signed-loss VaR/ES using Acklam rational inverse CDF; rates/vol as decimals, outputs VaR and ES. Approximation ~1e-9 in z.
export function normal_var(mean,vol,confidence){
  if(![mean,vol,confidence].every(Number.isFinite)||vol<0||confidence<=0||confidence>=1)throw new RangeError("Invalid normal VaR inputs");
  let z,q,z2;
  if(confidence<0.02425){q=Math.sqrt(-2*Math.log(confidence));z=((((((-0.007784894002430293*q + (-0.3223964580411365))*q + (-2.400758277161838))*q + (-2.549732539343734))*q + (4.374664141464968))*q + (2.938163982698783)))/(((((0.007784695709041462*q + (0.3224671290700398))*q + (2.445134137142996))*q + (3.754408661907416))*q + (1.0)));}
  else if(confidence>0.97575){q=Math.sqrt(-2*Math.log(1-confidence));z=-(((((((-0.007784894002430293*q + (-0.3223964580411365))*q + (-2.400758277161838))*q + (-2.549732539343734))*q + (4.374664141464968))*q + (2.938163982698783)))/(((((0.007784695709041462*q + (0.3224671290700398))*q + (2.445134137142996))*q + (3.754408661907416))*q + (1.0))));}
  else{q=confidence-0.5;z2=q*q;z=((((((-39.69683028665376*z2 + (220.9460984245205))*z2 + (-275.9285104469687))*z2 + (138.357751867269))*z2 + (-30.66479806614716))*z2 + (2.506628277459239))*q)/((((((-54.47609879822406*z2 + (161.5858368580409))*z2 + (-155.6989798598866))*z2 + (66.80131188771972))*z2 + (-13.28068155288572))*z2 + (1.0)));}
  return [-mean+vol*z,-mean+vol*Math.exp(-0.5*z*z)*0.39894228040143267794/(1-confidence)];
}
