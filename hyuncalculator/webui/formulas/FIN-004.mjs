
export function npv(rate, flows) {
    if (rate <= -1) { throw new RangeError("Invalid rate"); }
    let total = 0.0;
    for (let t = 0; t < flows.length; t++) { total += flows[t] / Math.pow(1 + rate, t); }
    return total;
}
