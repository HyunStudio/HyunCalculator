export function pmt(principal, rate, n) {
    if ((principal < 0.0)) { throw new RangeError("Invalid formula inputs"); }
    if ((rate <= -(1.0))) { throw new RangeError("Invalid formula inputs"); }
    if ((n <= 0.0)) { throw new RangeError("Invalid formula inputs"); }
    return ((Math.abs(rate) < 1e-14) ? (principal / n) : ((principal * rate) / (1.0 - Math.pow((1.0 + rate), -(n)))));
}
