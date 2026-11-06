// HyunCalculator STRAT-001
export function cost(notional, commission, slippage, spread, sides) {
    if (((notional < 0.0)) || ((commission < 0.0)) || ((slippage < 0.0)) || ((spread < 0.0)) || ((sides < 1.0)) || ((sides > 2.0)) || !Number.isFinite(notional) || !Number.isFinite(commission) || !Number.isFinite(slippage) || !Number.isFinite(spread)) throw new RangeError("Invalid quantitative inputs");
    return { "One-way effective cost (bps)": ((commission + slippage) + spread), "Total traded notional": (notional * sides), "Total estimated trading cost": (((notional * sides) * ((commission + slippage) + spread)) / 10000.0), "Total cost / single-side notional": ((sides * ((commission + slippage) + spread)) / 10000.0) };
}
