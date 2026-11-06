// HyunCalculator STOCH-002
export function ou(x, level, kappa, sigma, t) {
    if (((kappa <= 0.0)) || ((sigma < 0.0)) || ((t < 0.0)) || !Number.isFinite(x) || !Number.isFinite(level) || !Number.isFinite(kappa) || !Number.isFinite(sigma) || !Number.isFinite(t)) throw new RangeError("Invalid quantitative inputs");
    return { "Expected state": (level + ((x - level) * Math.exp((-(kappa) * t)))), "Std. deviation": (sigma * Math.sqrt(((1.0 - Math.exp(((-(2.0) * kappa) * t))) / (2.0 * kappa)))) };
}
