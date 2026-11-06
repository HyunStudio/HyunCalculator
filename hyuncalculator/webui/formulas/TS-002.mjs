// HyunCalculator TS-002
export function garch(lastvar, shock, omega, alpha, beta) {
    if (((lastvar < 0.0)) || ((omega < 0.0)) || ((alpha < 0.0)) || ((beta < 0.0)) || (((alpha + beta) >= 1.0)) || !Number.isFinite(lastvar) || !Number.isFinite(shock) || !Number.isFinite(omega) || !Number.isFinite(alpha) || !Number.isFinite(beta)) throw new RangeError("Invalid quantitative inputs");
    return { "Forecast variance": ((omega + (alpha * Math.pow(shock, 2.0))) + (beta * lastvar)), "Forecast volatility": Math.sqrt(((omega + (alpha * Math.pow(shock, 2.0))) + (beta * lastvar))), "Unconditional variance": (omega / ((1.0 - alpha) - beta)) };
}
