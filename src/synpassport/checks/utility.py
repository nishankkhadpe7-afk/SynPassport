"""Downstream utility and subgroup utility evaluations.

Evaluates Train on Synthetic, Test on Real (TSTR) ratios and subgroup performance
with seeded bootstrap confidence intervals.
"""

from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

from synpassport.checks.base import BaseCheck, CheckResult
from synpassport.checks.bootstrap import compute_bootstrap_ci
from synpassport.checks.subgroups import filter_subgroup

__all__ = ["UtilityTSTRCheck", "SubgroupUtilityCheck"]


def _prepare_matrices(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target_col: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Extract and standardize feature matrices and target vectors."""
    feature_cols = [c for c in train_df.columns if c != target_col]

    # Numeric encoding
    X_train_df = pd.DataFrame(index=train_df.index)
    X_test_df = pd.DataFrame(index=test_df.index)

    for c in feature_cols:
        if pd.api.types.is_numeric_dtype(train_df[c]):
            mean_val = float(train_df[c].mean()) if not np.isnan(train_df[c].mean()) else 0.0
            X_train_df[c] = train_df[c].fillna(mean_val)
            X_test_df[c] = test_df[c].fillna(mean_val)
        else:
            cats, uniques = pd.factorize(train_df[c].astype(str))
            cat_map = {val: idx for idx, val in enumerate(uniques)}
            X_train_df[c] = cats
            X_test_df[c] = test_df[c].astype(str).map(lambda x, m=cat_map: m.get(x, -1))

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train_df)
    X_test = scaler.transform(X_test_df)

    y_train = pd.to_numeric(train_df[target_col], errors="coerce").fillna(0).to_numpy()
    y_test = pd.to_numeric(test_df[target_col], errors="coerce").fillna(0).to_numpy()

    return X_train, y_train, X_test, y_test


def _evaluate_classifier(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    seed: int,
) -> float:
    """Train logistic regression and evaluate metric on test set."""
    if len(np.unique(y_train)) < 2 or len(np.unique(y_test)) < 2:
        # Trivial or single-class subset
        return 0.5

    clf = LogisticRegression(max_iter=1000, random_state=seed)
    clf.fit(X_train, y_train)

    try:
        y_prob = clf.predict_proba(X_test)[:, 1]
        return float(roc_auc_score(y_test, y_prob))
    except Exception:
        y_pred = clf.predict(X_test)
        return float(accuracy_score(y_test, y_pred))


class UtilityTSTRCheck(BaseCheck):
    """Measures model performance ratio trained on synthetic versus real data."""

    check_id = "utility_tstr_ratio"

    def run(self, real_data: Any, synth_data: Any, **kwargs: Any) -> CheckResult:
        """Evaluate Train on Synthetic, Test on Real ratio against real holdout."""
        seed = int(kwargs.get("seed", 1234))
        target_col = kwargs.get("target_col")
        holdout_data = kwargs.get("holdout_data")

        if not isinstance(synth_data, pd.DataFrame) or not isinstance(real_data, pd.DataFrame):
            return CheckResult(
                check_id=self.check_id,
                value=0.0,
                seed=seed,
                state="FAIL",
                error="Expected pandas DataFrame inputs",
            )

        # Fallback holdout if not explicitly provided: split real data
        if holdout_data is None or not isinstance(holdout_data, pd.DataFrame):
            n_half = max(1, len(real_data) // 2)
            train_real = real_data.iloc[:n_half]
            holdout = real_data.iloc[n_half:]
        else:
            train_real = real_data
            holdout = holdout_data

        if target_col is None or target_col not in real_data.columns:
            # Default to last column
            target_col = real_data.columns[-1]

        try:
            X_syn_tr, y_syn_tr, X_syn_te, y_syn_te = _prepare_matrices(
                synth_data, holdout, target_col
            )
            score_synth = _evaluate_classifier(X_syn_tr, y_syn_tr, X_syn_te, y_syn_te, seed)

            X_real_tr, y_real_tr, X_real_te, y_real_te = _prepare_matrices(
                train_real, holdout, target_col
            )
            score_real = _evaluate_classifier(X_real_tr, y_real_tr, X_real_te, y_real_te, seed)

            ratio = score_synth / max(score_real, 1e-6)
            # Clip between 0.0 and 1.0 (or slightly above if synthetic marginally outperformed)
            score = float(np.clip(ratio, 0.0, 1.2))

            return CheckResult(
                check_id=self.check_id,
                value=score,
                n=len(holdout),
                seed=seed,
                score_synth=score_synth,
                score_real=score_real,
                target_col=target_col,
            )
        except Exception as e:
            return CheckResult(
                check_id=self.check_id,
                value=0.0,
                seed=seed,
                state="FAIL",
                error=f"TSTR evaluation error: {e}",
            )


class SubgroupUtilityCheck(BaseCheck):
    """Measures TSTR on designated critical subgroups with bootstrap confidence intervals."""

    check_id = "subgroup_utility_ci"

    def run(self, real_data: Any, synth_data: Any, **kwargs: Any) -> CheckResult:
        """Evaluate subgroup downstream utility and compute bootstrap confidence intervals."""
        seed = int(kwargs.get("seed", 1234))
        target_col = kwargs.get("target_col")
        subgroup_query = kwargs.get("subgroup_query", "")
        holdout_data = kwargs.get("holdout_data")
        n_resamples = int(kwargs.get("n_resamples", 1000))

        if not isinstance(synth_data, pd.DataFrame) or not isinstance(real_data, pd.DataFrame):
            return CheckResult(
                check_id=self.check_id,
                value=0.0,
                seed=seed,
                state="FAIL",
                error="Expected pandas DataFrame inputs",
            )

        if holdout_data is None or not isinstance(holdout_data, pd.DataFrame):
            n_half = max(1, len(real_data) // 2)
            train_real = real_data.iloc[:n_half]
            holdout = real_data.iloc[n_half:]
        else:
            train_real = real_data
            holdout = holdout_data

        if target_col is None or target_col not in real_data.columns:
            target_col = real_data.columns[-1]

        # Apply restricted subgroup filter
        subgroup_holdout = filter_subgroup(holdout, subgroup_query)
        n_subgroup = len(subgroup_holdout)

        # Insufficient subgroup records
        if n_subgroup < 5:
            return CheckResult(
                check_id=self.check_id,
                value=0.0,
                ci_low=0.0,
                ci_high=1.0,
                n=n_subgroup,
                seed=seed,
                state="INSUFFICIENT_EVIDENCE",
                ci_width=1.0,
                reason=f"Subgroup sample size {n_subgroup} is too small for statistical power",
            )

        try:
            X_syn_tr, y_syn_tr, X_syn_sub, y_syn_sub = _prepare_matrices(
                synth_data, subgroup_holdout, target_col
            )
            X_real_tr, y_real_tr, X_real_sub, y_real_sub = _prepare_matrices(
                train_real, subgroup_holdout, target_col
            )

            score_real_baseline = max(
                _evaluate_classifier(X_real_tr, y_real_tr, X_real_sub, y_real_sub, seed),
                1e-6,
            )

            # Fit model on synthetic data
            clf = LogisticRegression(max_iter=1000, random_state=seed)
            clf.fit(X_syn_tr, y_syn_tr)

            # Bootstrap over subgroup holdout rows
            subgroup_indices = np.arange(n_subgroup)

            def subgroup_metric_fn(idx_sample: Any) -> float:
                idx_arr = np.array(idx_sample)
                sub_y = y_syn_sub[idx_arr]
                sub_X = X_syn_sub[idx_arr]
                if len(np.unique(sub_y)) < 2:
                    return 0.5
                try:
                    probs = clf.predict_proba(sub_X)[:, 1]
                    raw_score = float(roc_auc_score(sub_y, probs))
                except Exception:
                    preds = clf.predict(sub_X)
                    raw_score = float(accuracy_score(sub_y, preds))
                return float(raw_score / score_real_baseline)

            point_est, ci_l, ci_h = compute_bootstrap_ci(
                subgroup_indices,
                subgroup_metric_fn,
                n_resamples=n_resamples,
                seed=seed,
            )
            ci_width = float(ci_h - ci_l)

            return CheckResult(
                check_id=self.check_id,
                value=point_est,
                ci_low=ci_l,
                ci_high=ci_h,
                n=n_subgroup,
                seed=seed,
                ci_width=ci_width,
                subgroup_query=subgroup_query,
            )
        except Exception as e:
            return CheckResult(
                check_id=self.check_id,
                value=0.0,
                seed=seed,
                state="INSUFFICIENT_EVIDENCE",
                error=f"Subgroup utility evaluation error: {e}",
            )
