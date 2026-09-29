"""Sufficiency and statistical power analysis checks.

Evaluates sample size sufficiency for designated subgroups to ensure confidence interval
bounds meet policy requirements.
"""

import math
from typing import Any

import pandas as pd

from synpassport.checks.base import BaseCheck, CheckResult
from synpassport.checks.subgroups import filter_subgroup

__all__ = ["SufficiencyCheck"]


class SufficiencyCheck(BaseCheck):
    """Evaluates sample size sufficiency and required minimum records for subgroup assurance."""

    check_id = "sufficiency"

    def run(self, real_data: Any, synth_data: Any, **kwargs: Any) -> CheckResult:
        """Evaluate subgroup power analysis and projected confidence interval width."""
        seed = int(kwargs.get("seed", 1234))
        subgroup_query = kwargs.get("subgroup_query", "")
        target_ci_width = float(kwargs.get("target_ci_width", 0.15))

        if not isinstance(real_data, pd.DataFrame):
            return CheckResult(
                check_id=self.check_id,
                value=0.0,
                seed=seed,
                state="INSUFFICIENT_EVIDENCE",
                error="Expected pandas DataFrame for real_data",
            )

        # Filter real data by subgroup query
        subgroup_df = filter_subgroup(real_data, subgroup_query)
        subgroup_n = len(subgroup_df)

        # Power analysis: N_required = ceil((1.96 / W_target)^2) for worst-case proportion variance
        z_crit = 1.96
        min_n_required = math.ceil((z_crit / target_ci_width) ** 2)

        if subgroup_n > 0:
            projected_ci_width = float((2.0 * z_crit * 0.5) / math.sqrt(subgroup_n))
        else:
            projected_ci_width = 1.0

        if subgroup_n >= min_n_required:
            state = "PASS"
            reason = (
                f"Subgroup N={subgroup_n} satisfies target width {target_ci_width:.2f} "
                f"(need >= {min_n_required})"
            )
        else:
            state = "INSUFFICIENT_EVIDENCE"
            reason = (
                f"Subgroup N={subgroup_n} insufficient; need >= {min_n_required} records "
                f"for width <= {target_ci_width:.2f}"
            )

        return CheckResult(
            check_id=self.check_id,
            value=float(subgroup_n),
            n=subgroup_n,
            seed=seed,
            state=state,
            min_n_required=min_n_required,
            projected_ci_width=projected_ci_width,
            target_ci_width=target_ci_width,
            subgroup_query=subgroup_query,
            reason=reason,
        )
