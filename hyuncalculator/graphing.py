"""Safe 2D function sampling. Plotting/UI are implemented in gui.py."""
from __future__ import annotations

import re
import numpy as np
from .scientific import calculate


def sample_curves(expressions: str, x_min: float = -10, x_max: float = 10,
                  points: int = 1001, degrees: bool = False):
    if not (-1e6 <= x_min < x_max <= 1e6):
        raise ValueError('Require -1e6 <= x_min < x_max <= 1e6')
    if not 20 <= points <= 10000:
        raise ValueError('Number of points must be between 20 and 10000')
    lines = [line.strip() for line in re.split(r'[;\n]+', expressions) if line.strip()]
    if not 1 <= len(lines) <= 8:
        raise ValueError('Provide 1 to 8 functions separated by newlines or semicolons')
    x = np.linspace(x_min, x_max, int(points))
    curves = []
    for line in lines:
        expr = re.sub(r'^\s*(?:y\s*=|[A-Za-z]\(x\)\s*=)', '', line, count=1)
        val = calculate(expr, variables={'x': x}, degrees=degrees)
        if np.iscomplexobj(val):
            if np.any(np.abs(np.imag(val)) > 1e-12):
                raise ValueError(f'Complex outputs cannot be plotted: {line}')
            val = np.real(val)
        if np.isscalar(val):
            y = np.full_like(x, float(val))
        else:
            y = np.asarray(val, dtype=float)
            if y.shape != x.shape:
                raise ValueError(f'Function must return a scalar or one value per x: {line}')
        y = np.where(np.isfinite(y), y, np.nan)
        if not np.any(np.isfinite(y)):
            raise ValueError(f'Function has no real finite values in range: {line}')
        # Break long discontinuities rather than drawing misleading vertical lines.
        jump = np.abs(np.diff(y))
        finite_jumps = jump[np.isfinite(jump)]
        if finite_jumps.size:
            threshold = max(np.nanpercentile(finite_jumps, 90) * 12, 1e-8)
            bad = np.where(jump > threshold)[0]
            y[bad + 1] = np.nan
        curves.append((line, x.copy(), y))
    return curves
