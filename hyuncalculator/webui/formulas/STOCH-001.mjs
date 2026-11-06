// HyunCalculator STOCH-001
export function gbm(s, mu, sigma, t) {
    if (((s <= 0.0)) || ((sigma < 0.0)) || ((t < 0.0)) || !Number.isFinite(s) || !Number.isFinite(mu) || !Number.isFinite(sigma) || !Number.isFinite(t)) throw new RangeError("Invalid quantitative inputs");
    return { "Expected price": (s * Math.exp((mu * t))), "Std. deviation": ((s * Math.exp((mu * t))) * Math.sqrt((Math.exp((Math.pow(sigma, 2.0) * t)) - 1.0))) };
}
