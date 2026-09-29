"""Restricted grammar parser for subgroup expressions without eval or exec."""

import re
from typing import Any

import pandas as pd

__all__ = ["filter_subgroup", "parse_subgroup_expression"]

# Supported comparison operators
OPERATORS = {
    ">=": lambda s, val: s >= val,
    "<=": lambda s, val: s <= val,
    "!=": lambda s, val: s != val,
    "==": lambda s, val: s == val,
    ">": lambda s, val: s > val,
    "<": lambda s, val: s < val,
}

OP_PATTERN = re.compile(r"(>=|<=|!=|==|>|<)")


def _parse_literal(literal_str: str) -> Any:
    """Parse scalar literal to float, integer, or clean string without eval."""
    cleaned = literal_str.strip().strip("'\"")
    # Integer attempt
    try:
        return int(cleaned)
    except ValueError:
        pass
    # Float attempt
    try:
        return float(cleaned)
    except ValueError:
        pass
    return cleaned


def parse_subgroup_expression(expr: str) -> list[tuple[str, str, Any]]:
    """Parse restricted subgroup expression into a list of (column, operator, literal) tuples.

    Does not use eval or exec.
    """
    conditions: list[tuple[str, str, Any]] = []
    # Split on 'and' or 'AND'
    raw_clauses = re.split(r"\s+(?:and|AND)\s+", expr.strip())

    for clause in raw_clauses:
        clause = clause.strip()
        if not clause:
            continue
        parts = OP_PATTERN.split(clause, maxsplit=1)
        if len(parts) != 3:
            raise ValueError(f"Invalid subgroup clause: '{clause}'. Expected '<col> <op> <val>'")

        col = parts[0].strip()
        op = parts[1].strip()
        val = _parse_literal(parts[2])

        if op not in OPERATORS:
            raise ValueError(f"Unsupported comparison operator: '{op}' in clause '{clause}'")

        conditions.append((col, op, val))

    return conditions


def filter_subgroup(df: pd.DataFrame, expr: str) -> pd.DataFrame:
    """Filter dataframe rows matching restricted subgroup expression without eval.

    Args:
        df: Input DataFrame.
        expr: Restricted subgroup string (e.g. 'age >= 65 and status == 1').

    Returns:
        Filtered DataFrame containing only matching rows.
    """
    if not expr or not expr.strip():
        return df

    conditions = parse_subgroup_expression(expr)
    mask = pd.Series(True, index=df.index)

    for col, op, val in conditions:
        if col not in df.columns:
            # Column not present in dataframe -> empty subset
            return df.iloc[0:0]

        series = df[col]
        # Type alignment if comparing numeric with float/int
        if pd.api.types.is_numeric_dtype(series) and isinstance(val, (int, float)):
            comp_series = pd.to_numeric(series, errors="coerce")
        else:
            comp_series = series.astype(str)
            val = str(val)

        op_fn = OPERATORS[op]
        clause_mask = op_fn(comp_series, val)
        mask = mask & clause_mask

    return df[mask].reset_index(drop=True)
