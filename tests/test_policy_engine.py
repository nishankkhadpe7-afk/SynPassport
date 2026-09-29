"""Tests for policy profile loading, canonical hashing, and deterministic policy engine."""

import copy
from typing import Any

import pytest

from synpassport.policy import (
    CheckState,
    PolicyProfile,
    aggregate_use_verdict,
    compute_policy_hash,
    evaluate_policy,
    evaluate_policy_detailed,
    load_policy,
    load_policy_profile,
)

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def perfect_evidence() -> list[dict[str, Any]]:
    """Evidence where all checks exceed thresholds with narrow confidence intervals."""
    return [
        {"check_id": "schema_validity", "value": 1.0, "state": "PASS"},
        {"check_id": "marginal_fidelity", "value": 0.94, "ci_low": 0.92, "ci_high": 0.96},
        {"check_id": "correlation_fidelity", "value": 0.91, "ci_low": 0.88, "ci_high": 0.94},
        {"check_id": "utility_tstr_ratio", "value": 0.93, "ci_low": 0.91, "ci_high": 0.95},
        {"check_id": "subgroup_utility_ci_width", "value": 0.08},
        {"check_id": "privacy_dcr_vs_holdout", "value": 0.05, "state": "PASS"},
        {"check_id": "membership_inference_auc", "value": 0.51, "ci_low": 0.48, "ci_high": 0.54},
    ]


@pytest.fixture
def demo_step4_evidence() -> list[dict[str, Any]]:
    """Demo Step 4 evidence: prototyping passes, clinical has wide subgroup CI."""
    return [
        {"check_id": "schema_validity", "value": 1.0, "state": "PASS"},
        {"check_id": "marginal_fidelity", "value": 0.92, "ci_low": 0.90, "ci_high": 0.94},
        {"check_id": "correlation_fidelity", "value": 0.88, "ci_low": 0.85, "ci_high": 0.91},
        {"check_id": "utility_tstr_ratio", "value": 0.91, "ci_low": 0.90, "ci_high": 0.92},
        # Exceeds max 0.15 threshold -> INSUFFICIENT_EVIDENCE
        {"check_id": "subgroup_utility_ci_width", "value": 0.22},
        {"check_id": "privacy_dcr_vs_holdout", "value": 0.04, "state": "PASS"},
        {"check_id": "membership_inference_auc", "value": 0.52, "ci_low": 0.49, "ci_high": 0.54},
    ]


@pytest.fixture
def privacy_failing_evidence() -> list[dict[str, Any]]:
    """Evidence where candidate fails empirical confidentiality checks."""
    return [
        {"check_id": "schema_validity", "value": 1.0, "state": "PASS"},
        {"check_id": "marginal_fidelity", "value": 0.93, "ci_low": 0.91, "ci_high": 0.95},
        {"check_id": "correlation_fidelity", "value": 0.89, "ci_low": 0.86, "ci_high": 0.92},
        {"check_id": "utility_tstr_ratio", "value": 0.92, "ci_low": 0.90, "ci_high": 0.94},
        {"check_id": "subgroup_utility_ci_width", "value": 0.10},
        # Fails: systematically closer to training than holdout
        {"check_id": "privacy_dcr_vs_holdout", "value": -0.15, "state": "FAIL"},
        # Fails: attack AUC lower bound > 0.55
        {"check_id": "membership_inference_auc", "value": 0.68, "ci_low": 0.62, "ci_high": 0.74},
    ]


# -----------------------------------------------------------------------------
# Policy Loader & Hasher Tests
# -----------------------------------------------------------------------------


def test_load_all_three_policy_profiles() -> None:
    """Verify loading the 3 policy profiles from policies/ directory."""
    for profile_id in ("software-testing", "ml-prototyping", "ml-sensitive-v1"):
        policy = load_policy(profile_id)
        assert policy["id"] == profile_id
        assert policy["version"] == 1
        assert "sha256" in policy
        assert len(policy["sha256"]) == 64
        assert "requires" in policy
        assert "uses" in policy
        assert "budget" in policy

        # Test model loading as well
        model = load_policy_profile(profile_id)
        assert isinstance(model, PolicyProfile)
        assert model.id == profile_id


def test_policy_hash_determinism_and_sensitivity() -> None:
    """Verify policy hashing is deterministic and sensitive to content modifications."""
    p1 = load_policy("ml-sensitive-v1")
    p2 = load_policy("ml-sensitive-v1")
    assert p1["sha256"] == p2["sha256"]

    # Changing a threshold must modify canonical hash
    mutated = copy.deepcopy(p1)
    mutated["requires"]["marginal_fidelity"]["min"] = 0.95
    new_hash = compute_policy_hash(mutated)
    assert new_hash != p1["sha256"]


# -----------------------------------------------------------------------------
# State Function & CI Decision Rule Tests
# -----------------------------------------------------------------------------


def test_state_function_missing_evidence_yields_insufficient() -> None:
    """Missing required evidence must always return INSUFFICIENT_EVIDENCE."""
    policy = load_policy("software-testing")
    # Provide empty evidence
    verdicts = evaluate_policy(policy, [])
    assert verdicts["software_testing"] == CheckState.INSUFFICIENT_EVIDENCE.value


def test_state_function_errored_evidence_yields_insufficient() -> None:
    """Evidence with error flag must return INSUFFICIENT_EVIDENCE."""
    policy = load_policy("software-testing")
    errored_evidence = [
        {"check_id": "schema_validity", "value": 1.0, "state": "PASS"},
        {"check_id": "marginal_fidelity", "error": "OutOfMemory during KS computation"},
    ]
    bundle = evaluate_policy_detailed(policy, errored_evidence)
    assert bundle.check_evaluations["marginal_fidelity"].state == CheckState.INSUFFICIENT_EVIDENCE
    assert bundle.verdicts["software_testing"] == CheckState.INSUFFICIENT_EVIDENCE.value


def test_state_function_ci_width_limit() -> None:
    """Confidence interval width exceeding policy limit must return INSUFFICIENT_EVIDENCE."""
    policy = load_policy("ml-sensitive-v1")
    # Policy requires subgroup_utility_ci_width max 0.15
    evidence_too_wide = [
        {"check_id": "schema_validity", "value": 1.0, "state": "PASS"},
        {"check_id": "marginal_fidelity", "value": 0.95, "ci_low": 0.94, "ci_high": 0.96},
        {"check_id": "correlation_fidelity", "value": 0.90, "ci_low": 0.88, "ci_high": 0.92},
        {"check_id": "utility_tstr_ratio", "value": 0.92, "ci_low": 0.90, "ci_high": 0.94},
        {"check_id": "subgroup_utility_ci_width", "value": 0.25},
        {"check_id": "privacy_dcr_vs_holdout", "state": "PASS"},
        {"check_id": "membership_inference_auc", "value": 0.50, "ci_low": 0.48, "ci_high": 0.52},
    ]
    bundle = evaluate_policy_detailed(policy, evidence_too_wide)
    assert (
        bundle.check_evaluations["subgroup_utility_ci_width"].state
        == CheckState.INSUFFICIENT_EVIDENCE
    )
    assert bundle.verdicts["clinical_ml"] == CheckState.INSUFFICIENT_EVIDENCE.value


def test_state_function_warning_bands() -> None:
    """Metric within warning bands returns WARNING."""
    policy = load_policy("ml-sensitive-v1")
    # utility_tstr_ratio: min 0.90, warning_bands min 0.85
    evidence_in_warning = [
        {"check_id": "schema_validity", "value": 1.0, "state": "PASS"},
        {"check_id": "marginal_fidelity", "value": 0.95, "ci_low": 0.94, "ci_high": 0.96},
        {"check_id": "correlation_fidelity", "value": 0.90, "ci_low": 0.88, "ci_high": 0.92},
        # 0.88 is in [0.85, 0.90) warning band
        {"check_id": "utility_tstr_ratio", "value": 0.88, "ci_low": 0.86, "ci_high": 0.89},
        {"check_id": "subgroup_utility_ci_width", "value": 0.10},
        {"check_id": "privacy_dcr_vs_holdout", "state": "PASS"},
        {"check_id": "membership_inference_auc", "value": 0.50, "ci_low": 0.48, "ci_high": 0.52},
    ]
    bundle = evaluate_policy_detailed(policy, evidence_in_warning)
    assert bundle.check_evaluations["utility_tstr_ratio"].state == CheckState.WARNING
    assert bundle.verdicts["ml_prototyping"] == CheckState.WARNING.value
    assert bundle.verdicts["clinical_ml"] == CheckState.WARNING.value


def test_ci_decision_rule_spanning_threshold() -> None:
    """CI spanning threshold without clear bounds yields INSUFFICIENT_EVIDENCE."""
    policy = load_policy("ml-sensitive-v1")
    # membership_inference_auc: max 0.55
    # CI [0.52, 0.60] spans across 0.55 -> insufficient
    evidence = [
        {"check_id": "schema_validity", "value": 1.0, "state": "PASS"},
        {"check_id": "marginal_fidelity", "value": 0.95, "ci_low": 0.93, "ci_high": 0.97},
        {"check_id": "correlation_fidelity", "value": 0.90, "ci_low": 0.88, "ci_high": 0.92},
        {"check_id": "utility_tstr_ratio", "value": 0.92, "ci_low": 0.91, "ci_high": 0.93},
        {"check_id": "subgroup_utility_ci_width", "value": 0.10},
        {"check_id": "privacy_dcr_vs_holdout", "state": "PASS"},
        {"check_id": "membership_inference_auc", "value": 0.54, "ci_low": 0.51, "ci_high": 0.60},
    ]
    bundle = evaluate_policy_detailed(policy, evidence)
    assert (
        bundle.check_evaluations["membership_inference_auc"].state
        == CheckState.INSUFFICIENT_EVIDENCE
    )


# -----------------------------------------------------------------------------
# Worst-of Aggregation Tests
# -----------------------------------------------------------------------------


def test_worst_of_aggregation_severity_order() -> None:
    """Verify severity order: FAIL > INSUFFICIENT_EVIDENCE > WARNING > PASS."""
    assert aggregate_use_verdict([CheckState.PASS, CheckState.PASS]) == CheckState.PASS
    assert aggregate_use_verdict([CheckState.PASS, CheckState.WARNING]) == CheckState.WARNING
    assert (
        aggregate_use_verdict([CheckState.WARNING, CheckState.INSUFFICIENT_EVIDENCE])
        == CheckState.INSUFFICIENT_EVIDENCE
    )
    assert aggregate_use_verdict([CheckState.WARNING, CheckState.FAIL]) == CheckState.FAIL
    assert (
        aggregate_use_verdict([CheckState.INSUFFICIENT_EVIDENCE, CheckState.FAIL])
        == CheckState.FAIL
    )
    assert (
        aggregate_use_verdict(
            [
                CheckState.PASS,
                CheckState.WARNING,
                CheckState.INSUFFICIENT_EVIDENCE,
                CheckState.FAIL,
            ]
        )
        == CheckState.FAIL
    )


# -----------------------------------------------------------------------------
# Hand-written Fixture Tests
# -----------------------------------------------------------------------------


def test_fixture_all_passing(perfect_evidence: list[dict[str, Any]]) -> None:
    """All required checks pass with adequate CI."""
    policy = load_policy("ml-sensitive-v1")
    verdicts = evaluate_policy(policy, perfect_evidence)
    assert verdicts["software_testing"] == "PASS"
    assert verdicts["ml_prototyping"] == "PASS"
    assert verdicts["clinical_ml"] == "PASS"


def test_fixture_demo_step4(demo_step4_evidence: list[dict[str, Any]]) -> None:
    """Demo Step 4: testing=PASS, prototyping=PASS, clinical=INSUFFICIENT_EVIDENCE."""
    policy = load_policy("ml-sensitive-v1")
    verdicts = evaluate_policy(policy, demo_step4_evidence)
    assert verdicts["software_testing"] == "PASS"
    assert verdicts["ml_prototyping"] == "PASS"
    assert verdicts["clinical_ml"] == "INSUFFICIENT_EVIDENCE"


def test_fixture_privacy_failing(privacy_failing_evidence: list[dict[str, Any]]) -> None:
    """Adversarial check failures block high-assurance clinical ML."""
    policy = load_policy("ml-sensitive-v1")
    verdicts = evaluate_policy(policy, privacy_failing_evidence)
    assert verdicts["software_testing"] == "PASS"
    assert verdicts["clinical_ml"] == "FAIL"


# -----------------------------------------------------------------------------
# Property Tests
# -----------------------------------------------------------------------------


def test_property_deterministic_and_pure(demo_step4_evidence: list[dict[str, Any]]) -> None:
    """Engine is a pure function: same inputs produce exact same outputs across iterations."""
    policy = load_policy("ml-sensitive-v1")
    first_verdicts = evaluate_policy(policy, demo_step4_evidence)
    for _ in range(50):
        assert evaluate_policy(policy, demo_step4_evidence) == first_verdicts


def test_property_missing_evidence_never_yields_pass(
    perfect_evidence: list[dict[str, Any]],
) -> None:
    """Omitting any required check can never result in a PASS verdict for uses requiring it."""
    policy = load_policy("ml-sensitive-v1")
    # For every check required by clinical_ml, remove it and verify clinical_ml != PASS
    required_checks = policy["requires"].keys()
    for check_to_remove in required_checks:
        incomplete_evidence = [e for e in perfect_evidence if e["check_id"] != check_to_remove]
        verdicts = evaluate_policy(policy, incomplete_evidence)
        assert verdicts["clinical_ml"] != "PASS", (
            f"Removing {check_to_remove} produced unexpected PASS"
        )
        assert verdicts["clinical_ml"] in ("INSUFFICIENT_EVIDENCE", "FAIL")


def test_property_monotonicity(perfect_evidence: list[dict[str, Any]]) -> None:
    """Worsening any metric can never improve any verdict."""
    policy = load_policy("ml-sensitive-v1")
    base_verdicts = evaluate_policy(policy, perfect_evidence)
    assert base_verdicts["clinical_ml"] == "PASS"

    # Degradation 1: decrease fidelity into warning zone
    worse_1 = copy.deepcopy(perfect_evidence)
    for rec in worse_1:
        if rec["check_id"] == "utility_tstr_ratio":
            rec["value"] = 0.87
            rec["ci_low"] = 0.86
            rec["ci_high"] = 0.89

    v1 = evaluate_policy(policy, worse_1)
    # Cannot be better than PASS
    assert v1["clinical_ml"] in ("WARNING", "FAIL", "INSUFFICIENT_EVIDENCE")

    # Degradation 2: increase attack AUC to failing level
    worse_2 = copy.deepcopy(worse_1)
    for rec in worse_2:
        if rec["check_id"] == "membership_inference_auc":
            rec["value"] = 0.70
            rec["ci_low"] = 0.65
            rec["ci_high"] = 0.75

    v2 = evaluate_policy(policy, worse_2)
    # Severity must be worse or equal to v1
    severity_rank = {
        CheckState.PASS.value: 1,
        CheckState.WARNING.value: 2,
        CheckState.INSUFFICIENT_EVIDENCE.value: 3,
        CheckState.FAIL.value: 4,
    }
    assert severity_rank[v2["clinical_ml"]] >= severity_rank[v1["clinical_ml"]]


def test_property_adding_required_checks_can_only_maintain_or_worsen_verdict(
    demo_step4_evidence: list[dict[str, Any]],
) -> None:
    """Adding requirements to a use profile never upgrades the verdict."""
    policy = load_policy("ml-sensitive-v1")
    initial_verdicts = evaluate_policy(policy, demo_step4_evidence)

    # software_testing only needs [schema_validity, marginal_fidelity] -> PASS
    assert initial_verdicts["software_testing"] == "PASS"

    # Add subgroup_utility_ci_width to software_testing requirements
    mutated_policy = copy.deepcopy(policy)
    mutated_policy["uses"]["software_testing"].append("subgroup_utility_ci_width")

    new_verdicts = evaluate_policy(mutated_policy, demo_step4_evidence)
    # In demo_step4_evidence, subgroup_utility_ci_width is 0.22 (insufficient)
    assert new_verdicts["software_testing"] == "INSUFFICIENT_EVIDENCE"
