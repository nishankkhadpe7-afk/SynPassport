"""Deterministic policy evaluation engine.

Pure function that maps evidence records against policy thresholds to produce
verdicts (PASS, WARNING, FAIL, INSUFFICIENT_EVIDENCE) per intended use.
Missing or errored evidence yields INSUFFICIENT_EVIDENCE and never PASS.
"""

from collections.abc import Sequence
from typing import Any

from synpassport.policy.models import SEVERITY_ORDER, CheckState, PolicyProfile

__all__ = [
    "evaluate_policy",
    "evaluate_check",
    "aggregate_use_verdict",
    "CheckEvaluationResult",
    "EvaluationBundle",
]


class CheckEvaluationResult:
    """Outcome of evaluating a single check against its policy threshold."""

    def __init__(
        self,
        check_id: str,
        state: CheckState,
        value: float | None = None,
        ci: list[float] | None = None,
        threshold: Any = None,
        reason: str = "",
    ) -> None:
        self.check_id = check_id
        self.state = state
        self.value = value
        self.ci = ci
        self.threshold = threshold
        self.reason = reason

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            "check_id": self.check_id,
            "state": self.state.value,
            "value": self.value,
            "ci": self.ci,
            "threshold": self.threshold,
            "reason": self.reason,
        }


class EvaluationBundle:
    """Complete evaluation report containing per-use verdicts and per-check evaluations."""

    def __init__(
        self,
        verdicts: dict[str, str],
        check_evaluations: dict[str, CheckEvaluationResult],
    ) -> None:
        self.verdicts = verdicts
        self.check_evaluations = check_evaluations


def _find_evidence_record(check_id: str, evidence: Sequence[Any]) -> dict[str, Any] | None:
    """Find matching evidence record by check_id or aliases."""
    normalized_evidence: list[dict[str, Any]] = []
    for r in evidence:
        if isinstance(r, dict):
            normalized_evidence.append(r)
        elif hasattr(r, "to_dict") and callable(r.to_dict):
            normalized_evidence.append(r.to_dict())
        elif hasattr(r, "model_dump") and callable(r.model_dump):
            normalized_evidence.append(r.model_dump())
        elif hasattr(r, "__dict__"):
            normalized_evidence.append(dict(r.__dict__))

    for record in normalized_evidence:
        cid = record.get("check_id") or record.get("check")
        if cid == check_id:
            return record

    # Derived alias for subgroup utility CI width if recorded under subgroup_utility
    if check_id == "subgroup_utility_ci_width":
        for record in normalized_evidence:
            cid = record.get("check_id") or record.get("check")
            if cid in ("subgroup_utility", "subgroup_utility_ci"):
                ci_low = record.get("ci_low")
                ci_high = record.get("ci_high")
                if ci_low is None and "ci" in record and isinstance(record["ci"], (list, tuple)):
                    if len(record["ci"]) == 2:
                        ci_low, ci_high = record["ci"][0], record["ci"][1]
                if ci_low is not None and ci_high is not None:
                    return {
                        "check_id": "subgroup_utility_ci_width",
                        "value": float(ci_high) - float(ci_low),
                        "ci_low": None,
                        "ci_high": None,
                    }
    return None


def evaluate_check(
    check_id: str,
    threshold_spec: Any,
    warning_band_spec: dict[str, float] | None,
    evidence_record: dict[str, Any] | None,
    max_ci_width_limit: float | None = None,
) -> CheckEvaluationResult:
    """Evaluate a single check requirement against evidence following design.md §3.1."""
    # Condition: Evidence missing / check not run
    if evidence_record is None:
        return CheckEvaluationResult(
            check_id=check_id,
            state=CheckState.INSUFFICIENT_EVIDENCE,
            threshold=threshold_spec,
            reason="Evidence missing for required check",
        )

    # Condition: Execution error
    if evidence_record.get("error") or evidence_record.get("status") in (
        "error",
        "failed",
        "errored",
    ):
        err_msg = str(evidence_record.get("error") or "Check execution error")
        return CheckEvaluationResult(
            check_id=check_id,
            state=CheckState.INSUFFICIENT_EVIDENCE,
            threshold=threshold_spec,
            reason=f"Check execution error: {err_msg}",
        )

    # Extract value and confidence bounds
    raw_val = evidence_record.get("value")
    value: float | None = float(raw_val) if raw_val is not None else None

    ci_low: float | None = (
        float(evidence_record["ci_low"]) if evidence_record.get("ci_low") is not None else None
    )
    ci_high: float | None = (
        float(evidence_record["ci_high"]) if evidence_record.get("ci_high") is not None else None
    )

    if (
        ci_low is None
        and "ci" in evidence_record
        and isinstance(evidence_record["ci"], (list, tuple))
    ):
        if len(evidence_record["ci"]) == 2:
            ci_low = float(evidence_record["ci"][0])
            ci_high = float(evidence_record["ci"][1])

    ci_list = [ci_low, ci_high] if (ci_low is not None and ci_high is not None) else None

    # Condition: Metric CI width > policy CI limit
    if ci_list is not None and ci_low is not None and ci_high is not None:
        actual_ci_width = ci_high - ci_low
        if max_ci_width_limit is not None and actual_ci_width > max_ci_width_limit:
            return CheckEvaluationResult(
                check_id=check_id,
                state=CheckState.INSUFFICIENT_EVIDENCE,
                value=value,
                ci=ci_list,
                threshold=threshold_spec,
                reason=(f"CI width {actual_ci_width:.4f} exceeds limit {max_ci_width_limit}"),
            )

    # Discrete / string requirements
    if threshold_spec == "pass":
        # Schema validity: requires 1.0 or explicit PASS state
        if value is not None:
            if value == 1.0 or evidence_record.get("state") == "PASS":
                return CheckEvaluationResult(
                    check_id=check_id,
                    state=CheckState.PASS,
                    value=value,
                    ci=ci_list,
                    threshold=threshold_spec,
                    reason="Schema validity verified (100% conforming)",
                )
            return CheckEvaluationResult(
                check_id=check_id,
                state=CheckState.FAIL,
                value=value,
                ci=ci_list,
                threshold=threshold_spec,
                reason=f"Schema validity failure: score {value} < 1.0",
            )
        if evidence_record.get("state") in ("PASS", "pass"):
            return CheckEvaluationResult(
                check_id=check_id,
                state=CheckState.PASS,
                threshold=threshold_spec,
                reason="State explicitly PASS",
            )
        if evidence_record.get("state") in ("FAIL", "fail"):
            return CheckEvaluationResult(
                check_id=check_id,
                state=CheckState.FAIL,
                threshold=threshold_spec,
                reason="State explicitly FAIL",
            )
        return CheckEvaluationResult(
            check_id=check_id,
            state=CheckState.INSUFFICIENT_EVIDENCE,
            threshold=threshold_spec,
            reason="Missing schema score or state",
        )

    if threshold_spec == "not_closer_than_holdout":
        # DCR check against holdout
        if evidence_record.get("state") == "FAIL":
            return CheckEvaluationResult(
                check_id=check_id,
                state=CheckState.FAIL,
                value=value,
                ci=ci_list,
                threshold=threshold_spec,
                reason="Synthetic proximity closer to training than holdout beyond tolerance",
            )
        if evidence_record.get("state") == "PASS":
            return CheckEvaluationResult(
                check_id=check_id,
                state=CheckState.PASS,
                value=value,
                ci=ci_list,
                threshold=threshold_spec,
                reason="Synthetic proximity not closer to training than holdout",
            )
        if value is not None:
            # Non-negative distance difference indicates holdout distance is comparable or closer
            if value >= 0.0:
                return CheckEvaluationResult(
                    check_id=check_id,
                    state=CheckState.PASS,
                    value=value,
                    ci=ci_list,
                    threshold=threshold_spec,
                    reason=f"DCR metric {value} meets baseline tolerance",
                )
            return CheckEvaluationResult(
                check_id=check_id,
                state=CheckState.FAIL,
                value=value,
                ci=ci_list,
                threshold=threshold_spec,
                reason=f"DCR metric {value} indicates excessive proximity to training set",
            )
        return CheckEvaluationResult(
            check_id=check_id,
            state=CheckState.INSUFFICIENT_EVIDENCE,
            threshold=threshold_spec,
            reason="DCR evidence missing metric value and state",
        )

    # Numeric threshold requirements: {min: T} or {max: T}
    if isinstance(threshold_spec, dict):
        # 1. Lower-bound threshold: {min: T}
        if "min" in threshold_spec:
            target_min = float(threshold_spec["min"])
            warn_min = (
                float(warning_band_spec["min"])
                if (warning_band_spec and "min" in warning_band_spec)
                else None
            )

            # Bound-based decision rule when CI is available
            if ci_low is not None and ci_high is not None:
                effective_low = ci_low
                effective_high = ci_high

                if warn_min is not None:
                    if effective_high < warn_min:
                        return CheckEvaluationResult(
                            check_id=check_id,
                            state=CheckState.FAIL,
                            value=value,
                            ci=ci_list,
                            threshold=threshold_spec,
                            reason=f"Upper CI {effective_high:.4f} violates warning {warn_min:.4f}",
                        )
                    if effective_low >= target_min:
                        return CheckEvaluationResult(
                            check_id=check_id,
                            state=CheckState.PASS,
                            value=value,
                            ci=ci_list,
                            threshold=threshold_spec,
                            reason=f"Lower CI {effective_low:.4f} meets target {target_min:.4f}",
                        )
                    if effective_low >= warn_min:
                        return CheckEvaluationResult(
                            check_id=check_id,
                            state=CheckState.WARNING,
                            value=value,
                            ci=ci_list,
                            threshold=threshold_spec,
                            reason=(
                                f"Lower CI {effective_low:.4f} in warning band "
                                f"[{warn_min:.4f}, {target_min:.4f})"
                            ),
                        )
                    # CI spans below warning threshold
                    return CheckEvaluationResult(
                        check_id=check_id,
                        state=CheckState.INSUFFICIENT_EVIDENCE,
                        value=value,
                        ci=ci_list,
                        threshold=threshold_spec,
                        reason=f"CI [{effective_low:.4f}, {effective_high:.4f}] spans threshold",
                    )
                else:
                    if effective_high < target_min:
                        return CheckEvaluationResult(
                            check_id=check_id,
                            state=CheckState.FAIL,
                            value=value,
                            ci=ci_list,
                            threshold=threshold_spec,
                            reason=f"Upper CI bound {effective_high:.4f} violates {target_min:.4f}",
                        )
                    if effective_low >= target_min:
                        return CheckEvaluationResult(
                            check_id=check_id,
                            state=CheckState.PASS,
                            value=value,
                            ci=ci_list,
                            threshold=threshold_spec,
                            reason=f"Lower CI bound {effective_low:.4f} meets {target_min:.4f}",
                        )
                    # CI spans target threshold
                    return CheckEvaluationResult(
                        check_id=check_id,
                        state=CheckState.INSUFFICIENT_EVIDENCE,
                        value=value,
                        ci=ci_list,
                        threshold=threshold_spec,
                        reason=f"CI [{effective_low:.4f}, {effective_high:.4f}] spans {target_min}",
                    )

            # Point estimate fallback when CI is not provided
            if value is None:
                return CheckEvaluationResult(
                    check_id=check_id,
                    state=CheckState.INSUFFICIENT_EVIDENCE,
                    threshold=threshold_spec,
                    reason="Missing point metric value",
                )

            if warn_min is not None:
                if value < warn_min:
                    return CheckEvaluationResult(
                        check_id=check_id,
                        state=CheckState.FAIL,
                        value=value,
                        threshold=threshold_spec,
                        reason=f"Value {value:.4f} violates warning threshold {warn_min:.4f}",
                    )
                if value < target_min:
                    return CheckEvaluationResult(
                        check_id=check_id,
                        state=CheckState.WARNING,
                        value=value,
                        threshold=threshold_spec,
                        reason=f"Value {value:.4f} in warning [{warn_min:.4f}, {target_min:.4f})",
                    )
                return CheckEvaluationResult(
                    check_id=check_id,
                    state=CheckState.PASS,
                    value=value,
                    threshold=threshold_spec,
                    reason=f"Value {value:.4f} meets target {target_min:.4f}",
                )
            else:
                if value < target_min:
                    return CheckEvaluationResult(
                        check_id=check_id,
                        state=CheckState.FAIL,
                        value=value,
                        threshold=threshold_spec,
                        reason=f"Value {value:.4f} violates threshold {target_min:.4f}",
                    )
                return CheckEvaluationResult(
                    check_id=check_id,
                    state=CheckState.PASS,
                    value=value,
                    threshold=threshold_spec,
                    reason=f"Value {value:.4f} meets threshold {target_min:.4f}",
                )

        # 2. Upper-bound threshold: {max: T}
        if "max" in threshold_spec:
            target_max = float(threshold_spec["max"])
            warn_max = (
                float(warning_band_spec["max"])
                if (warning_band_spec and "max" in warning_band_spec)
                else None
            )

            # For subgroup utility CI width, exceeding max is INSUFFICIENT_EVIDENCE per §3.1
            is_ci_width_check = "ci_width" in check_id

            if ci_low is not None and ci_high is not None:
                effective_low = ci_low
                effective_high = ci_high

                if warn_max is not None:
                    if effective_low > warn_max:
                        return CheckEvaluationResult(
                            check_id=check_id,
                            state=CheckState.FAIL,
                            value=value,
                            ci=ci_list,
                            threshold=threshold_spec,
                            reason=f"Lower CI {effective_low:.4f} violates warning {warn_max:.4f}",
                        )
                    if effective_high <= target_max:
                        return CheckEvaluationResult(
                            check_id=check_id,
                            state=CheckState.PASS,
                            value=value,
                            ci=ci_list,
                            threshold=threshold_spec,
                            reason=f"Upper CI {effective_high:.4f} meets target {target_max:.4f}",
                        )
                    if effective_high <= warn_max:
                        return CheckEvaluationResult(
                            check_id=check_id,
                            state=CheckState.WARNING,
                            value=value,
                            ci=ci_list,
                            threshold=threshold_spec,
                            reason=(
                                f"Upper CI {effective_high:.4f} in warning band "
                                f"({target_max:.4f}, {warn_max:.4f}]"
                            ),
                        )
                    return CheckEvaluationResult(
                        check_id=check_id,
                        state=CheckState.INSUFFICIENT_EVIDENCE,
                        value=value,
                        ci=ci_list,
                        threshold=threshold_spec,
                        reason=f"CI [{effective_low:.4f}, {effective_high:.4f}] spans threshold",
                    )
                else:
                    if effective_low > target_max:
                        fail_state = (
                            CheckState.INSUFFICIENT_EVIDENCE
                            if is_ci_width_check
                            else CheckState.FAIL
                        )
                        return CheckEvaluationResult(
                            check_id=check_id,
                            state=fail_state,
                            value=value,
                            ci=ci_list,
                            threshold=threshold_spec,
                            reason=f"Lower CI {effective_low:.4f} violates {target_max:.4f}",
                        )
                    if effective_high <= target_max:
                        return CheckEvaluationResult(
                            check_id=check_id,
                            state=CheckState.PASS,
                            value=value,
                            ci=ci_list,
                            threshold=threshold_spec,
                            reason=f"Upper CI {effective_high:.4f} meets {target_max:.4f}",
                        )
                    # CI spans threshold -> INSUFFICIENT_EVIDENCE
                    return CheckEvaluationResult(
                        check_id=check_id,
                        state=CheckState.INSUFFICIENT_EVIDENCE,
                        value=value,
                        ci=ci_list,
                        threshold=threshold_spec,
                        reason=f"CI [{effective_low:.4f}, {effective_high:.4f}] spans {target_max}",
                    )

            if value is None:
                return CheckEvaluationResult(
                    check_id=check_id,
                    state=CheckState.INSUFFICIENT_EVIDENCE,
                    threshold=threshold_spec,
                    reason="Missing point metric value",
                )

            if warn_max is not None:
                if value > warn_max:
                    return CheckEvaluationResult(
                        check_id=check_id,
                        state=CheckState.FAIL,
                        value=value,
                        threshold=threshold_spec,
                        reason=f"Value {value:.4f} violates warning threshold {warn_max:.4f}",
                    )
                if value > target_max:
                    return CheckEvaluationResult(
                        check_id=check_id,
                        state=CheckState.WARNING,
                        value=value,
                        threshold=threshold_spec,
                        reason=f"Value {value:.4f} in warning ({target_max:.4f}, {warn_max:.4f}]",
                    )
                return CheckEvaluationResult(
                    check_id=check_id,
                    state=CheckState.PASS,
                    value=value,
                    threshold=threshold_spec,
                    reason=f"Value {value:.4f} meets target threshold {target_max:.4f}",
                )
            else:
                if value > target_max:
                    state_on_exceed = (
                        CheckState.INSUFFICIENT_EVIDENCE if is_ci_width_check else CheckState.FAIL
                    )
                    return CheckEvaluationResult(
                        check_id=check_id,
                        state=state_on_exceed,
                        value=value,
                        threshold=threshold_spec,
                        reason=f"Value {value:.4f} violates threshold {target_max:.4f}",
                    )
                return CheckEvaluationResult(
                    check_id=check_id,
                    state=CheckState.PASS,
                    value=value,
                    threshold=threshold_spec,
                    reason=f"Value {value:.4f} meets threshold {target_max:.4f}",
                )

    # Unknown threshold specification
    return CheckEvaluationResult(
        check_id=check_id,
        state=CheckState.INSUFFICIENT_EVIDENCE,
        value=value,
        threshold=threshold_spec,
        reason=f"Unsupported threshold specification format: {threshold_spec}",
    )


def aggregate_use_verdict(check_states: list[CheckState]) -> CheckState:
    """Aggregate check states into a single use verdict using worst-of rule.

    Severity order: FAIL > INSUFFICIENT_EVIDENCE > WARNING > PASS.
    """
    if not check_states:
        return CheckState.INSUFFICIENT_EVIDENCE
    return max(check_states, key=lambda s: SEVERITY_ORDER[s])


def evaluate_policy_detailed(
    policy_data: dict[str, Any] | PolicyProfile,
    evidence: Sequence[dict[str, Any] | Any],
) -> EvaluationBundle:
    """Evaluate policy deterministically, returning detailed evaluations and verdicts."""
    policy = policy_data if isinstance(policy_data, PolicyProfile) else PolicyProfile(**policy_data)

    requires = policy.requires
    warning_bands = policy.warning_bands

    # Evaluate each check declared in requires
    check_evaluations: dict[str, CheckEvaluationResult] = {}
    for check_id, threshold_spec in requires.items():
        evidence_rec = _find_evidence_record(check_id, evidence)
        warn_spec = warning_bands.get(check_id)

        # Check for policy CI width limit
        ci_limit = None
        if isinstance(threshold_spec, dict) and "max_ci_width" in threshold_spec:
            ci_limit = float(threshold_spec["max_ci_width"])
        elif (
            "subgroup_utility_ci_width" in requires
            and "max" in requires["subgroup_utility_ci_width"]
        ):
            if check_id in ("subgroup_utility", "subgroup_utility_ci"):
                ci_limit = float(requires["subgroup_utility_ci_width"]["max"])

        eval_res = evaluate_check(
            check_id=check_id,
            threshold_spec=threshold_spec,
            warning_band_spec=warn_spec,
            evidence_record=evidence_rec,
            max_ci_width_limit=ci_limit,
        )
        check_evaluations[check_id] = eval_res

    # Compute verdict for each intended use
    verdicts: dict[str, str] = {}
    for use_name in policy.uses.keys():
        required_check_ids = policy.get_required_checks_for_use(use_name)
        states_for_use: list[CheckState] = []
        for req_cid in required_check_ids:
            if req_cid in check_evaluations:
                states_for_use.append(check_evaluations[req_cid].state)
            else:
                # Required check was not even declared in requires -> insufficient
                states_for_use.append(CheckState.INSUFFICIENT_EVIDENCE)

        verdict_state = aggregate_use_verdict(states_for_use)
        verdicts[use_name] = verdict_state.value

    return EvaluationBundle(verdicts=verdicts, check_evaluations=check_evaluations)


def evaluate_policy(
    policy: dict[str, Any] | PolicyProfile,
    evidence: Sequence[dict[str, Any] | Any],
) -> dict[str, str]:
    """Pure function mapping policy and evidence to per-use verdicts.

    No network, no LLM, no randomness. Same inputs produce identical verdicts.
    Missing or errored evidence yields INSUFFICIENT_EVIDENCE and never PASS.
    """
    bundle = evaluate_policy_detailed(policy, evidence)
    return bundle.verdicts
