"""Schema validity check.

Evaluates column types, valid ranges, nullability constraints, and categorical domains.
"""

from typing import Any

import numpy as np
import pandas as pd

from synpassport.checks.base import BaseCheck, CheckResult

__all__ = ["SchemaValidityCheck"]


class SchemaValidityCheck(BaseCheck):
    """Verifies synthetic dataset conforms strictly to expected schema definitions."""

    check_id = "schema_validity"

    def run(self, real_data: Any, synth_data: Any, **kwargs: Any) -> CheckResult:
        """Evaluate schema conformity score.

        Computes fraction of rows in synth_data that strictly conform to
        types, nullability, categorical domains, and numeric ranges of real_data.
        """
        seed = int(kwargs.get("seed", 1234))

        if not isinstance(synth_data, pd.DataFrame) or not isinstance(real_data, pd.DataFrame):
            return CheckResult(
                check_id=self.check_id,
                value=0.0,
                seed=seed,
                state="FAIL",
                error="Expected pandas DataFrame for both real and synthetic datasets",
            )

        n_rows = len(synth_data)
        if n_rows == 0:
            return CheckResult(
                check_id=self.check_id,
                value=0.0,
                n=0,
                seed=seed,
                state="FAIL",
                error="Synthetic dataset has zero rows",
            )

        # 1. Column presence check
        missing_columns = [col for col in real_data.columns if col not in synth_data.columns]
        if missing_columns:
            return CheckResult(
                check_id=self.check_id,
                value=0.0,
                n=n_rows,
                seed=seed,
                state="FAIL",
                missing_columns=missing_columns,
                error=f"Synthetic data missing required columns: {missing_columns}",
            )

        # Row validity mask
        valid_row_mask = np.ones(n_rows, dtype=bool)
        column_reports: dict[str, dict[str, Any]] = {}

        for col in real_data.columns:
            real_col = real_data[col]
            synth_col = synth_data[col]

            is_numeric = pd.api.types.is_numeric_dtype(real_col)
            synth_is_numeric = pd.api.types.is_numeric_dtype(synth_col)

            col_mask = np.ones(n_rows, dtype=bool)

            # Type match
            if is_numeric != synth_is_numeric:
                col_mask = np.zeros(n_rows, dtype=bool)
                column_reports[col] = {"status": "type_mismatch"}
                valid_row_mask &= col_mask
                continue

            # Nullability constraint
            real_null_rate = real_col.isna().mean()
            synth_nulls = synth_col.isna()
            if real_null_rate == 0.0:
                col_mask &= ~synth_nulls
            else:
                # Allowed nulls up to real_null_rate + 0.10
                if synth_nulls.mean() > (real_null_rate + 0.10):
                    col_mask &= ~synth_nulls

            if is_numeric:
                # Range check: within [min - 3*std, max + 3*std]
                real_clean = real_col.dropna()
                if len(real_clean) > 0:
                    r_min, r_max = float(real_clean.min()), float(real_clean.max())
                    r_std = float(real_clean.std()) if len(real_clean) > 1 else 0.0
                    lower_bound = r_min - (3.0 * r_std)
                    upper_bound = r_max + (3.0 * r_std)

                    synth_numeric = pd.to_numeric(synth_col, errors="coerce")
                    in_range = (synth_numeric >= lower_bound) & (synth_numeric <= upper_bound)
                    col_mask &= in_range.fillna(False)
            else:
                # Categorical domain check
                real_domain = set(real_col.dropna().astype(str).unique())
                synth_str = synth_col.dropna().astype(str)
                in_domain = synth_str.isin(real_domain)
                # Keep null rows aligned with nullability check
                col_mask &= in_domain.reindex(synth_col.index, fill_value=True)

            valid_row_mask &= col_mask
            column_reports[col] = {"valid_fraction": float(col_mask.mean())}

        score = float(valid_row_mask.mean())
        state = "PASS" if score == 1.0 else "FAIL"

        return CheckResult(
            check_id=self.check_id,
            value=score,
            n=n_rows,
            seed=seed,
            state=state,
            column_reports=column_reports,
        )
