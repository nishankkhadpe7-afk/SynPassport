"""Marginal and correlation fidelity checks.

Measures statistical similarity between synthetic and real distributions using
Kolmogorov-Smirnov distance, Total Variation distance, and correlation matrix divergence.
"""

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from synpassport.checks.base import BaseCheck, CheckResult
from synpassport.checks.identifiers import comparable_frames

__all__ = ["MarginalFidelityCheck", "CorrelationFidelityCheck"]


class MarginalFidelityCheck(BaseCheck):
    """Computes marginal distribution agreement across individual features."""

    check_id = "marginal_fidelity"

    def run(self, real_data: Any, synth_data: Any, **kwargs: Any) -> CheckResult:
        """Evaluate marginal distribution fidelity per feature and mean aggregate."""
        seed = int(kwargs.get("seed", 1234))

        if not isinstance(synth_data, pd.DataFrame) or not isinstance(real_data, pd.DataFrame):
            return CheckResult(
                check_id=self.check_id,
                value=0.0,
                seed=seed,
                state="FAIL",
                error="Expected pandas DataFrame inputs",
            )

        # Identifier columns (all-unique keys) have no distribution to reproduce and
        # text datetimes are compared as timestamps; both are decided from real data.
        real_data, (synth_data,), id_cols = comparable_frames(real_data, synth_data)
        common_cols = [c for c in real_data.columns if c in synth_data.columns]
        if not common_cols:
            return CheckResult(
                check_id=self.check_id,
                value=0.0,
                seed=seed,
                state="FAIL",
                error="No comparable columns between real and synthetic data",
            )

        per_feature: dict[str, float] = {}

        for col in common_cols:
            real_series = real_data[col].dropna()
            synth_series = synth_data[col].dropna()

            if len(real_series) == 0 or len(synth_series) == 0:
                per_feature[col] = 0.0
                continue

            if pd.api.types.is_numeric_dtype(real_series) and pd.api.types.is_numeric_dtype(
                synth_series
            ):
                # Kolmogorov-Smirnov test complement for numerical features
                try:
                    ks_stat = stats.ks_2samp(real_series, synth_series).statistic
                    per_feature[col] = float(np.clip(1.0 - ks_stat, 0.0, 1.0))
                except Exception:
                    per_feature[col] = 0.0
            else:
                # Total Variation distance complement for categorical features
                r_counts = real_series.astype(str).value_counts(normalize=True)
                s_counts = synth_series.astype(str).value_counts(normalize=True)
                all_cats = set(r_counts.index).union(set(s_counts.index))

                tv_dist = 0.5 * sum(
                    abs(r_counts.get(cat, 0.0) - s_counts.get(cat, 0.0)) for cat in all_cats
                )
                per_feature[col] = float(np.clip(1.0 - tv_dist, 0.0, 1.0))

        score = float(np.mean(list(per_feature.values()))) if per_feature else 0.0
        worst_col = min(per_feature, key=lambda k: per_feature[k]) if per_feature else ""
        worst_val = per_feature.get(worst_col, 0.0)

        return CheckResult(
            check_id=self.check_id,
            value=score,
            n=len(synth_data),
            seed=seed,
            per_feature=per_feature,
            worst_feature=worst_col,
            worst_feature_score=worst_val,
            excluded_identifier_columns=id_cols,
        )


class CorrelationFidelityCheck(BaseCheck):
    """Computes pairwise association matrix similarity between datasets."""

    check_id = "correlation_fidelity"

    def run(self, real_data: Any, synth_data: Any, **kwargs: Any) -> CheckResult:
        """Evaluate correlation matrix distance complement."""
        seed = int(kwargs.get("seed", 1234))

        if not isinstance(synth_data, pd.DataFrame) or not isinstance(real_data, pd.DataFrame):
            return CheckResult(
                check_id=self.check_id,
                value=0.0,
                seed=seed,
                state="FAIL",
                error="Expected pandas DataFrame inputs",
            )

        real_data, (synth_data,), _ids = comparable_frames(real_data, synth_data)
        common_cols = [c for c in real_data.columns if c in synth_data.columns]
        if len(common_cols) < 2:
            return CheckResult(
                check_id=self.check_id,
                value=1.0,
                n=len(synth_data),
                seed=seed,
                note="Fewer than 2 columns; correlation is trivially 1.0",
            )

        # Convert columns to numeric representation (encoding categoricals numerically)
        r_num = pd.DataFrame(index=real_data.index)
        s_num = pd.DataFrame(index=synth_data.index)

        for col in common_cols:
            if pd.api.types.is_numeric_dtype(real_data[col]):
                r_num[col] = pd.to_numeric(real_data[col], errors="coerce").fillna(0.0)
                s_num[col] = pd.to_numeric(synth_data[col], errors="coerce").fillna(0.0)
            else:
                # Factorize categorical consistently
                cats, uniques = pd.factorize(real_data[col].astype(str))
                cat_map = {val: idx for idx, val in enumerate(uniques)}
                r_num[col] = cats
                s_num[col] = synth_data[col].astype(str).map(lambda x, m=cat_map: m.get(x, -1))

        corr_real = r_num.corr().fillna(0.0).to_numpy()
        corr_synth = s_num.corr().fillna(0.0).to_numpy()

        # Normalized distance: max possible distance between correlation matrices is 2.0 per entry
        abs_diff = np.abs(corr_real - corr_synth)
        mean_diff = float(np.mean(abs_diff)) / 2.0
        score = float(np.clip(1.0 - mean_diff, 0.0, 1.0))

        return CheckResult(
            check_id=self.check_id,
            value=score,
            n=len(synth_data),
            seed=seed,
            mean_correlation_distance=mean_diff,
        )
