export function fv(pv, rate, n) {
    if ((n < 0.0)) { throw new RangeError("Invalid formula inputs"); }
    if ((rate <= -(1.0))) { throw new RangeError("Invalid formula inputs"); }
    return (pv * Math.pow((1.0 + rate), n));
}
