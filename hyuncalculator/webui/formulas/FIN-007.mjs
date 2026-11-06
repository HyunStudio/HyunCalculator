export function cagr(start, end, years) {
    if ((start <= 0.0)) { throw new RangeError("Invalid formula inputs"); }
    if ((end < 0.0)) { throw new RangeError("Invalid formula inputs"); }
    if ((years <= 0.0)) { throw new RangeError("Invalid formula inputs"); }
    return (Math.pow((end / start), (1.0 / years)) - 1.0);
}
