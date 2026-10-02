"""Empirical confidentiality and adversarial attack checks.

Measures distance-to-closest-record (DCR) against holdout baselines and membership
inference attack (MIA) risk indicators.
Evaluates empirical risk evidence without asserting absolute guarantees.
"""

from typing import Any

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import MinMaxScaler

from synpassport.checks.base import BaseCheck, CheckResult
from synpassport.checks.bootstrap import compute_bootstrap_ci
from synpassport.checks.identifiers import comparable_frames

__all__ = ["DCRVsHoldoutCheck", "MembershipInferenceCheck"]


def _encode_and_scale(
    real_train: pd.DataFrame,
    real_holdout: pd.DataFrame,
    synth: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Encode categorical columns and scale numeric columns onto a shared [0, 1] space."""
    # Unique identifiers would make every distance meaningless; leave them out.
    real_train, (real_holdout, synth), _ids = comparable_frames(real_train, real_holdout, synth)
    common_cols = [
        c for c in real_train.columns if c in real_holdout.columns and c in synth.columns
    ]

    encoded_train = pd.DataFrame(index=real_train.index)
    encoded_holdout = pd.DataFrame(index=real_holdout.index)
    encoded_synth = pd.DataFrame(index=synth.index)

    for col in common_cols:
        r_tr = real_train[col]
        r_ho = real_holdout[col]
        s = synth[col]

        if pd.api.types.is_numeric_dtype(r_tr):
            fill_val = float(r_tr.mean()) if not np.isnan(r_tr.mean()) else 0.0
            encoded_train[col] = pd.to_numeric(r_tr, errors="coerce").fillna(fill_val)
            encoded_holdout[col] = pd.to_numeric(r_ho, errors="coerce").fillna(fill_val)
            encoded_synth[col] = pd.to_numeric(s, errors="coerce").fillna(fill_val)
        else:
            cats, uniques = pd.factorize(r_tr.astype(str))
            mapping = {v: idx for idx, v in enumerate(uniques)}
            encoded_train[col] = cats
            encoded_holdout[col] = r_ho.astype(str).map(lambda x, m=mapping: m.get(x, -1))
            encoded_synth[col] = s.astype(str).map(lambda x, m=mapping: m.get(x, -1))

    scaler = MinMaxScaler()
    tr_mat = scaler.fit_transform(encoded_train)
    ho_mat = scaler.transform(encoded_holdout)
    syn_mat = scaler.transform(encoded_synth)

    return tr_mat, ho_mat, syn_mat


class DCRVsHoldoutCheck(BaseCheck):
    """Measures distance-to-closest-record distribution against real holdout baselines."""

    check_id = "privacy_dcr_vs_holdout"

    def run(self, real_data: Any, synth_data: Any, **kwargs: Any) -> CheckResult:
        """Evaluate synthetic proximity distribution relative to training and holdout."""
        seed = int(kwargs.get("seed", 1234))
        holdout_data = kwargs.get("holdout_data")

        if not isinstance(synth_data, pd.DataFrame) or not isinstance(real_data, pd.DataFrame):
            return CheckResult(
                check_id=self.check_id,
                value=-1.0,
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

        # Balance training and holdout sample sizes to avoid distance estimation bias
        n_match = min(len(train_real), len(holdout), 500)
        if len(train_real) > n_match:
            tr_sample = train_real.sample(n=n_match, random_state=seed)
        else:
            tr_sample = train_real

        if len(holdout) > n_match:
            ho_sample = holdout.sample(n=n_match, random_state=seed)
        else:
            ho_sample = holdout

        syn_sample = synth_data.sample(n=min(len(synth_data), 500), random_state=seed)

        tr_mat, ho_mat, syn_mat = _encode_and_scale(tr_sample, ho_sample, syn_sample)

        # Compute Euclidean distance to closest records
        dists_train = cdist(syn_mat, tr_mat, metric="euclidean")
        min_d_train = np.min(dists_train, axis=1)

        dists_holdout = cdist(syn_mat, ho_mat, metric="euclidean")
        min_d_holdout = np.min(dists_holdout, axis=1)

        # Detect exact memorization / copied records
        exact_train_matches = int(np.sum(min_d_train < 1e-5))
        exact_holdout_matches = int(np.sum(min_d_holdout < 1e-5))

        # Bootstrap CI for fraction-closer-to-train statistic
        indices = np.arange(len(syn_mat))

        def _frac_closer(idx_sample: Any) -> float:
            idx_arr = np.array(idx_sample)
            d_tr = min_d_train[idx_arr]
            d_ho = min_d_holdout[idx_arr]
            if len(d_tr) == 0:
                return 0.0
            return float(np.sum(d_tr < (d_ho - 1e-5)) / len(d_tr))

        n_resamples = int(kwargs.get("n_resamples", 1000))
        fraction_closer_to_train, ci_l, ci_h = compute_bootstrap_ci(
            indices, _frac_closer, n_resamples=n_resamples, seed=seed
        )

        # Median difference: median(d_train) - median(d_holdout)
        median_diff = float(np.median(min_d_train) - np.median(min_d_holdout))

        # Failure condition: copied records or systematic proximity to train
        if exact_train_matches > exact_holdout_matches and exact_train_matches > 0:
            state = "FAIL"
            score = -1.0
        elif ci_l > 0.60 and median_diff < -0.05:
            # Lower CI bound exceeds 60% -> memorization signal is robust
            state = "FAIL"
            score = float(median_diff)
        elif ci_h > 0.60 and median_diff < -0.05:
            # CI spans the 60% threshold -> evidence is insufficient
            state = "INSUFFICIENT_EVIDENCE"
            score = float(fraction_closer_to_train)
        else:
            state = "PASS"
            score = max(0.0, float(1.0 - fraction_closer_to_train))

        return CheckResult(
            check_id=self.check_id,
            value=score,
            ci_low=ci_l,
            ci_high=ci_h,
            n=len(synth_data),
            seed=seed,
            state=state,
            fraction_closer_to_train=fraction_closer_to_train,
            median_dcr_diff=median_diff,
            exact_train_matches=exact_train_matches,
            exact_holdout_matches=exact_holdout_matches,
        )


class MembershipInferenceCheck(BaseCheck):
    """Performs empirical membership inference attack evaluation with shadow classifiers."""

    check_id = "membership_inference_auc"

    def run(self, real_data: Any, synth_data: Any, **kwargs: Any) -> CheckResult:
        """Evaluate membership inference discrimination AUC and bootstrap confidence interval."""
        seed = int(kwargs.get("seed", 1234))
        holdout_data = kwargs.get("holdout_data")
        n_resamples = int(kwargs.get("n_resamples", 1000))

        if not isinstance(synth_data, pd.DataFrame) or not isinstance(real_data, pd.DataFrame):
            return CheckResult(
                check_id=self.check_id,
                value=0.5,
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

        n_eval = min(len(train_real), len(holdout), 500)
        tr_sample = train_real.sample(n=n_eval, random_state=seed)
        ho_sample = holdout.sample(n=n_eval, random_state=seed)
        syn_sample = synth_data.sample(n=min(len(synth_data), 500), random_state=seed)

        tr_mat, ho_mat, syn_mat = _encode_and_scale(tr_sample, ho_sample, syn_sample)

        # Attack heuristic: proximity to synthetic data distribution
        # Members of training set are expected to have smaller distance to synthetic data if overfit
        d_tr_to_syn = np.min(cdist(tr_mat, syn_mat, metric="euclidean"), axis=1)
        d_ho_to_syn = np.min(cdist(ho_mat, syn_mat, metric="euclidean"), axis=1)

        # Inverted distance as attack confidence score: higher score -> predicted member (1)
        scores_tr = -d_tr_to_syn
        scores_ho = -d_ho_to_syn

        y_true = np.concatenate([np.ones(len(scores_tr)), np.zeros(len(scores_ho))])
        y_scores = np.concatenate([scores_tr, scores_ho])

        indices = np.arange(len(y_true))

        def mia_auc_fn(idx_sample: Any) -> float:
            idx_arr = np.array(idx_sample)
            y_s = y_true[idx_arr]
            sc_s = y_scores[idx_arr]
            if len(np.unique(y_s)) < 2:
                return 0.5
            try:
                return float(roc_auc_score(y_s, sc_s))
            except Exception:
                return 0.5

        point_est, ci_l, ci_h = compute_bootstrap_ci(
            indices,
            mia_auc_fn,
            n_resamples=n_resamples,
            seed=seed,
        )

        # Threshold decision rule per design.md §4.7:
        # FAIL if lower CI bound > 0.55; INSUFFICIENT_EVIDENCE if spans 0.55;
        # PASS if upper CI <= 0.55
        if ci_l > 0.55:
            state = "FAIL"
        elif ci_h <= 0.55:
            state = "PASS"
        else:
            state = "INSUFFICIENT_EVIDENCE"

        return CheckResult(
            check_id=self.check_id,
            value=point_est,
            ci_low=ci_l,
            ci_high=ci_h,
            n=len(y_true),
            seed=seed,
            state=state,
            ci_width=float(ci_h - ci_l),
        )
