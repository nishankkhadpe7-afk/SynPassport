"""Seeded bootstrap confidence interval estimation helper."""

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

__all__ = ["compute_bootstrap_ci"]


def compute_bootstrap_ci(
    data: Any,
    metric_fn: Callable[[Any], float],
    n_resamples: int = 1000,
    alpha: float = 0.05,
    seed: int = 1234,
) -> tuple[float, float, float]:
    """Calculate point estimate and empirical bootstrap confidence interval.

    Args:
        data: Sequence, numpy array, or pandas DataFrame to resample.
        metric_fn: Callable that accepts a resampled subset and returns a scalar metric.
        n_resamples: Number of bootstrap iterations (mandated >= 1000).
        alpha: Two-sided significance level (default 0.05 for 95% CI).
        seed: Deterministic random seed for reproducibility.

    Returns:
        tuple of (point_estimate, ci_low, ci_high).
    """
    n_resamples = max(1000, n_resamples)
    rng = np.random.default_rng(seed)

    # Calculate point estimate on full data
    try:
        point_estimate = float(metric_fn(data))
    except Exception:
        return 0.0, 0.0, 1.0

    n_samples = len(data)
    if n_samples < 2:
        return point_estimate, 0.0, 1.0

    boot_estimates: list[float] = []
    is_df = isinstance(data, pd.DataFrame)
    indices = np.arange(n_samples)

    for _ in range(n_resamples):
        resample_idx = rng.choice(indices, size=n_samples, replace=True)
        if is_df:
            sample_subset = data.iloc[resample_idx]
        else:
            sample_subset = [data[i] for i in resample_idx]

        try:
            val = float(metric_fn(sample_subset))
            if np.isfinite(val):
                boot_estimates.append(val)
        except Exception:
            continue

    if len(boot_estimates) < (n_resamples // 2):
        # Insufficient successful resamples
        return point_estimate, 0.0, 1.0

    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)

    ci_low = float(np.percentile(boot_estimates, lower_pct))
    ci_high = float(np.percentile(boot_estimates, upper_pct))

    return point_estimate, ci_low, ci_high
