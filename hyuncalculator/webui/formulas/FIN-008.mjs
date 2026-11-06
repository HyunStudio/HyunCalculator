export function effective(rate, m) {
    if ((m <= 0.0)) { throw new RangeError("Invalid formula inputs"); }
    if (((rate / m) <= -(1.0))) { throw new RangeError("Invalid formula inputs"); }
    return (Math.pow((1.0 + (rate / m)), m) - 1.0);
}
