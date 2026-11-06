export function annuity(payment, rate, n) {
    if ((n <= 0.0)) { throw new RangeError("Invalid formula inputs"); }
    if ((rate <= -(1.0))) { throw new RangeError("Invalid formula inputs"); }
    return ((Math.abs(rate) < 1e-14) ? (payment * n) : ((payment * (1.0 - Math.pow((1.0 + rate), -(n)))) / rate));
}
