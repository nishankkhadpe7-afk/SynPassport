"""Evaluation checks and adversarial attack engines."""

from synpassport.checks.base import BaseCheck, CheckResult
from synpassport.checks.bootstrap import compute_bootstrap_ci
from synpassport.checks.fidelity import CorrelationFidelityCheck, MarginalFidelityCheck
from synpassport.checks.privacy import DCRVsHoldoutCheck, MembershipInferenceCheck
from synpassport.checks.schema import SchemaValidityCheck
from synpassport.checks.splitter import (
    SplitResult,
    get_agent_partition_metadata,
    split_train_holdout,
)
from synpassport.checks.subgroups import filter_subgroup, parse_subgroup_expression
from synpassport.checks.sufficiency import SufficiencyCheck
from synpassport.checks.utility import SubgroupUtilityCheck, UtilityTSTRCheck

__all__ = [
    "BaseCheck",
    "CheckResult",
    "compute_bootstrap_ci",
    "split_train_holdout",
    "get_agent_partition_metadata",
    "SplitResult",
    "parse_subgroup_expression",
    "filter_subgroup",
    "SchemaValidityCheck",
    "MarginalFidelityCheck",
    "CorrelationFidelityCheck",
    "UtilityTSTRCheck",
    "SubgroupUtilityCheck",
    "DCRVsHoldoutCheck",
    "MembershipInferenceCheck",
    "SufficiencyCheck",
]
