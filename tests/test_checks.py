"""Known-answer and integration tests for all 8 assurance checks and utilities."""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from synpassport.checks.bootstrap import compute_bootstrap_ci
from synpassport.checks.fidelity import CorrelationFidelityCheck, MarginalFidelityCheck
from synpassport.checks.privacy import DCRVsHoldoutCheck
from synpassport.checks.run import run_checks_pipeline
from synpassport.checks.schema import SchemaValidityCheck
from synpassport.checks.splitter import (
    get_agent_partition_metadata,
    split_train_holdout,
)
from synpassport.checks.subgroups import filter_subgroup, parse_subgroup_expression
from synpassport.checks.sufficiency import SufficiencyCheck
from synpassport.checks.utility import SubgroupUtilityCheck
from synpassport.evidence.models import EvidenceRecord
from synpassport.evidence.store import EvidenceStore
from synpassport.generators.sdv_wrapper import GaussianCopulaGenerator, SDVGeneratorWrapper

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def sample_dataset() -> pd.DataFrame:
    """Generate realistic tabular dataset with numerical and categorical features."""
    rng = np.random.default_rng(1234)
    n = 200
    age = rng.integers(20, 80, size=n)
    chol = 150 + 1.2 * age + rng.normal(0, 15, size=n)
    gender = rng.choice(["M", "F"], size=n)
    # Binary target associated with age and cholesterol
    prob = 1.0 / (1.0 + np.exp(-(0.05 * age + 0.01 * chol - 4.5)))
    target = (rng.uniform(0, 1, size=n) < prob).astype(int)

    return pd.DataFrame(
        {
            "age": age,
            "cholesterol": chol,
            "gender": gender,
            "hf_event": target,
        }
    )


# -----------------------------------------------------------------------------
# Known-Answer Tests
# -----------------------------------------------------------------------------


def test_identical_data_fidelity_near_one(sample_dataset: pd.DataFrame) -> None:
    """Known-answer: identical synthetic data yields fidelity near 1.0."""
    real = sample_dataset
    synth = sample_dataset.copy()

    # 1. Schema check
    schema_res = SchemaValidityCheck().run(real, synth)
    assert schema_res.value == 1.0
    assert schema_res.state == "PASS"

    # 2. Marginal fidelity
    marginal_res = MarginalFidelityCheck().run(real, synth)
    assert marginal_res.value == pytest.approx(1.0, abs=1e-3)

    # 3. Correlation fidelity
    corr_res = CorrelationFidelityCheck().run(real, synth)
    assert corr_res.value == pytest.approx(1.0, abs=1e-3)


def test_copied_rows_dcr_fails(sample_dataset: pd.DataFrame) -> None:
    """Known-answer: synthetic data containing exact copies of training rows fails DCR."""
    split = split_train_holdout(sample_dataset, train_ratio=0.5, seed=1234)
    # Candidate dataset simply memorizes training partition
    memorized_synth = split.train_df.copy()

    dcr_check = DCRVsHoldoutCheck()
    result = dcr_check.run(
        real_data=split.train_df,
        synth_data=memorized_synth,
        holdout_data=split.holdout_df,
        seed=1234,
    )

    assert result.state == "FAIL"
    assert result.metadata.get("exact_train_matches", 0) > 0


def test_shuffled_columns_correlation_drops(sample_dataset: pd.DataFrame) -> None:
    """Known-answer: permuting columns independently breaks correlations and drops score."""
    real = sample_dataset
    shuffled_synth = sample_dataset.copy()

    rng = np.random.default_rng(42)
    # Shuffle numeric features independently
    shuffled_synth["age"] = rng.permutation(shuffled_synth["age"].to_numpy())
    shuffled_synth["cholesterol"] = rng.permutation(shuffled_synth["cholesterol"].to_numpy())

    corr_check = CorrelationFidelityCheck()
    clean_score = corr_check.run(real, real).value
    shuffled_score = corr_check.run(real, shuffled_synth).value

    assert shuffled_score < clean_score
    assert (clean_score - shuffled_score) > 0.05


def test_tiny_subgroup_wide_ci(sample_dataset: pd.DataFrame) -> None:
    """Known-answer: extremely small subgroup yields wide CI / INSUFFICIENT_EVIDENCE."""
    split = split_train_holdout(sample_dataset, train_ratio=0.5, seed=1234)
    synth = split.train_df.copy()

    # Age >= 79 matches very few or zero rows in holdout
    subgroup_check = SubgroupUtilityCheck()
    res = subgroup_check.run(
        real_data=split.train_df,
        synth_data=synth,
        holdout_data=split.holdout_df,
        target_col="hf_event",
        subgroup_query="age >= 79",
        seed=1234,
        n_resamples=1000,
    )

    assert res.state == "INSUFFICIENT_EVIDENCE"
    assert res.metadata.get("ci_width", 1.0) >= 0.15


# -----------------------------------------------------------------------------
# Sufficiency & Power Analysis Tests
# -----------------------------------------------------------------------------


def test_sufficiency_check(sample_dataset: pd.DataFrame) -> None:
    """Verify sufficiency power analysis flags small subgroups."""
    suff_check = SufficiencyCheck()

    # Small subgroup
    small_res = suff_check.run(
        real_data=sample_dataset,
        synth_data=sample_dataset,
        subgroup_query="age >= 75",
        target_ci_width=0.15,
    )
    assert small_res.state == "INSUFFICIENT_EVIDENCE"
    assert small_res.metadata["min_n_required"] > small_res.n

    # Large subgroup
    large_df = pd.concat([sample_dataset] * 5, ignore_index=True)
    large_res = suff_check.run(
        real_data=large_df,
        synth_data=large_df,
        subgroup_query="age >= 20",
        target_ci_width=0.15,
    )
    assert large_res.state == "PASS"


# -----------------------------------------------------------------------------
# Bootstrap CI Helper Tests
# -----------------------------------------------------------------------------


def test_bootstrap_ci_helper_coverage() -> None:
    """Verify bootstrap CI helper returns valid confidence bounds with >= 1000 resamples."""
    rng = np.random.default_rng(1234)
    sample_values = rng.normal(loc=10.0, scale=2.0, size=100)

    point_est, ci_l, ci_h = compute_bootstrap_ci(
        sample_values,
        lambda s: float(np.mean(s)),
        n_resamples=1000,
        alpha=0.05,
        seed=1234,
    )

    assert ci_l <= point_est <= ci_h
    assert 9.0 < point_est < 11.0
    assert (ci_h - ci_l) < 2.0


# -----------------------------------------------------------------------------
# Train/Holdout Partition & Isolation Tests
# -----------------------------------------------------------------------------


def test_train_holdout_splitter_isolation(sample_dataset: pd.DataFrame) -> None:
    """Verify holdout dataset is partitioned, hashed, and agent metadata excludes rows."""
    split = split_train_holdout(sample_dataset, train_ratio=0.6, seed=1234)

    assert len(split.train_df) == 120
    assert len(split.holdout_df) == 80
    assert len(split.holdout_sha256) == 64

    # Verify agent metadata has no raw rows
    agent_meta = get_agent_partition_metadata(split)
    assert "train_df" not in agent_meta
    assert "holdout_df" not in agent_meta
    assert agent_meta["n_train"] == 120
    assert agent_meta["holdout_sha256"] == split.holdout_sha256


# -----------------------------------------------------------------------------
# Subgroup Restricted Grammar Tests
# -----------------------------------------------------------------------------


def test_restricted_subgroup_parsing(sample_dataset: pd.DataFrame) -> None:
    """Verify non-eval restricted grammar expression parser and filtering."""
    parsed = parse_subgroup_expression("age >= 65 and gender == 'F'")
    assert len(parsed) == 2
    assert parsed[0] == ("age", ">=", 65)
    assert parsed[1] == ("gender", "==", "F")

    filtered = filter_subgroup(sample_dataset, "age >= 65 and gender == 'F'")
    assert all(filtered["age"] >= 65)
    assert all(filtered["gender"] == "F")


# -----------------------------------------------------------------------------
# Generators Tests
# -----------------------------------------------------------------------------


def test_gaussian_copula_generator(sample_dataset: pd.DataFrame) -> None:
    """Verify Gaussian Copula fitting and deterministic seeded sampling."""
    gen = GaussianCopulaGenerator(seed=1234)
    gen.fit(sample_dataset)

    sample1 = gen.sample(num_rows=50, seed=42)
    sample2 = gen.sample(num_rows=50, seed=42)

    assert len(sample1) == 50
    assert list(sample1.columns) == list(sample_dataset.columns)
    # Seeded sampling reproducibility
    pd.testing.assert_frame_equal(sample1, sample2)


def test_sdv_wrapper_factory(sample_dataset: pd.DataFrame) -> None:
    """Verify SDV unified wrapper generation."""
    wrapper = SDVGeneratorWrapper(model_type="gaussian_copula", seed=1234)
    wrapper.fit(sample_dataset)
    synth = wrapper.sample(num_rows=30, seed=99)
    assert len(synth) == 30


# -----------------------------------------------------------------------------
# Evidence Store Tests
# -----------------------------------------------------------------------------


def test_sqlite_evidence_store() -> None:
    """Verify SQLite append-only persistence and retrieval."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_evidence.db"
        store = EvidenceStore(db_path=db_path)

        rec = EvidenceRecord(
            run_id="run_test",
            candidate_id="cand_1",
            check_id="marginal_fidelity",
            value=0.92,
            ci_low=0.90,
            ci_high=0.94,
            n=200,
            seed=1234,
            state="PASS",
            metadata={"dimension": "fidelity"},
        )

        row_id = store.record_evidence(rec)
        assert row_id > 0

        rows = store.get_run_evidence(run_id="run_test")
        assert len(rows) == 1
        assert rows[0]["check_id"] == "marginal_fidelity"
        assert rows[0]["value"] == 0.92
        assert rows[0]["metadata"]["dimension"] == "fidelity"


# -----------------------------------------------------------------------------
# CLI Pipeline Run Test
# -----------------------------------------------------------------------------


def test_cli_checks_run_pipeline(sample_dataset: pd.DataFrame) -> None:
    """Verify python -m synpassport.checks.run writes required evidence to SQLite."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_csv = Path(tmp_dir) / "real.csv"
        synth_csv = Path(tmp_dir) / "synth.csv"
        db_path = Path(tmp_dir) / "synpassport.db"

        sample_dataset.to_csv(data_csv, index=False)
        sample_dataset.to_csv(synth_csv, index=False)

        records = run_checks_pipeline(
            data_path=data_csv,
            synth_path=synth_csv,
            policy_id_or_path="ml-sensitive-v1",
            db_path=db_path,
            run_id="cli_test_run",
            candidate_id="cand_cli",
            seed=1234,
            target_col="hf_event",
            subgroup_query="age >= 65",
        )

        assert len(records) > 0
        store = EvidenceStore(db_path=db_path)
        persisted = store.get_run_evidence(run_id="cli_test_run")
        assert len(persisted) == len(records)
