"""Identifier and datetime column handling shared by generators and checks.

Identifier columns (transaction IDs, card hashes, IP addresses, session keys) are
detected deterministically from the REAL training data, before any generation, so the
agent can never choose which columns are measured. Such columns:

* carry no distribution worth reproducing (every value is unique), so fidelity,
  correlation, distance and utility checks leave them out;
* are a privacy risk if real values are copied into the synthetic data, which the
  ``identifier_leakage`` check measures;
* can be replaced by fresh values in the same format (``regenerate_identifiers``).

Datetime columns stored as text are compared and modelled as timestamps, not as
thousands of unrelated categories.
"""

from __future__ import annotations

import re
import string
from typing import Any

import numpy as np
import pandas as pd

from synpassport.checks.base import BaseCheck, CheckResult

__all__ = [
    "DATETIME_FORMATS",
    "IdentifierLeakageCheck",
    "comparable_frames",
    "detect_datetime_format",
    "detect_identifier_columns",
    "fresh_identifiers",
    "identifier_format_mask",
]

# A text column is an identifier when at least this share of its values are distinct.
IDENTIFIER_MIN_UNIQUE_RATIO = 0.9
IDENTIFIER_MIN_ROWS = 20

DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
)

_IPV4 = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")


def detect_datetime_format(series: pd.Series) -> str | None:
    """Return the strftime format that parses (almost) every value, or None."""
    if pd.api.types.is_numeric_dtype(series):
        return None
    values = series.dropna().astype(str)
    if len(values) == 0:
        return None
    sample = values.iloc[: min(len(values), 500)]
    for fmt in DATETIME_FORMATS:
        parsed = pd.to_datetime(sample, format=fmt, errors="coerce")
        if parsed.notna().mean() >= 0.98:
            return fmt
    return None


def detect_identifier_columns(df: pd.DataFrame) -> list[str]:
    """Text columns whose values are (almost) all distinct and that are not dates."""
    out: list[str] = []
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
            continue
        values = series.dropna()
        if len(values) < IDENTIFIER_MIN_ROWS:
            continue
        if values.nunique() / len(values) < IDENTIFIER_MIN_UNIQUE_RATIO:
            continue
        if detect_datetime_format(series) is not None:
            continue
        out.append(str(col))
    return out


def comparable_frames(
    real: pd.DataFrame, *others: pd.DataFrame
) -> tuple[pd.DataFrame, list[pd.DataFrame], list[str]]:
    """Drop identifier columns and turn text datetimes into epoch seconds.

    The identifier set is decided from ``real`` only. Returns the converted real frame,
    the converted other frames and the identifier columns that were removed.
    """
    id_cols = detect_identifier_columns(real)
    keep = [c for c in real.columns if c not in id_cols]
    real_out = real[keep].copy()
    others_out = [o[[c for c in keep if c in o.columns]].copy() for o in others]

    for col in keep:
        fmt = detect_datetime_format(real[col])
        if fmt is None:
            continue
        for frame in (real_out, *others_out):
            if col in frame.columns:
                parsed = pd.to_datetime(frame[col].astype(str), format=fmt, errors="coerce")
                epoch = (parsed - pd.Timestamp("1970-01-01")) / pd.Timedelta(seconds=1)
                frame[col] = epoch.astype(float)
    return real_out, others_out, id_cols


def _charset(values: pd.Series) -> set[str]:
    chars: set[str] = set()
    for v in values.astype(str).iloc[:2000]:
        chars.update(v)
    return chars


def _is_ipv4_column(values: pd.Series) -> bool:
    sample = values.astype(str).iloc[: min(len(values), 200)]
    return bool(len(sample)) and bool(sample.str.match(_IPV4).mean() > 0.95)


def _valid_ipv4(value: str) -> bool:
    m = _IPV4.match(value)
    return bool(m) and all(0 <= int(g) <= 255 for g in m.groups())


def identifier_format_mask(real: pd.Series, synth: pd.Series) -> np.ndarray:
    """True where a synthetic identifier looks like the real ones (length and characters)."""
    real_vals = real.dropna().astype(str)
    synth_str = synth.astype(str)
    if _is_ipv4_column(real_vals):
        ok = synth_str.map(_valid_ipv4).to_numpy()
    else:
        lengths = set(real_vals.str.len().unique())
        allowed = _charset(real_vals)
        ok_len = synth_str.str.len().isin(lengths).to_numpy()
        ok_chars = synth_str.map(lambda s: set(s) <= allowed).to_numpy()
        ok = ok_len & ok_chars
    return np.asarray(ok, dtype=bool) | synth.isna().to_numpy()


def fresh_identifiers(real: pd.Series, n: int, rng: np.random.Generator) -> pd.Series:
    """Generate ``n`` new, unique identifiers in the real column's format.

    No generated value equals a real value, so no real identifier can leak.
    """
    real_vals = real.dropna().astype(str)
    if len(real_vals) == 0:
        return pd.Series([None] * n, dtype=object)
    taken = set(real_vals)
    templates = real_vals.to_numpy()
    is_ip = _is_ipv4_column(real_vals)

    # Characters identical at a position in every real value of that length (prefixes
    # such as "TXN-") are kept; the other positions are randomised.
    fixed: dict[int, dict[int, str]] = {}
    variable: set[str] = set()
    for length, group in real_vals.groupby(real_vals.str.len()):
        cols = list(zip(*group.iloc[:2000].tolist(), strict=True))
        fixed[int(length)] = {i: chars[0] for i, chars in enumerate(cols) if len(set(chars)) == 1}
        for i, chars in enumerate(cols):
            if i not in fixed[int(length)]:
                variable.update(chars)

    var_alnum = {c for c in variable if c.isalnum()}
    hex_only = bool(var_alnum) and var_alnum <= set(string.hexdigits)
    hex_pool = sorted(var_alnum)
    digits = list(string.digits)
    upper = sorted(c for c in var_alnum if c.isupper()) or list(string.ascii_uppercase)
    lower = sorted(c for c in var_alnum if c.islower()) or list(string.ascii_lowercase)

    def make_one() -> str:
        if is_ip:
            return ".".join(str(int(x)) for x in rng.integers(1, 255, size=4))
        template = templates[int(rng.integers(0, len(templates)))]
        keep = fixed.get(len(template), {})
        out = []
        for pos, ch in enumerate(template):
            if pos in keep:
                out.append(ch)
            elif hex_only and ch.isalnum():
                out.append(hex_pool[int(rng.integers(0, len(hex_pool)))])
            elif ch.isdigit():
                out.append(digits[int(rng.integers(0, 10))])
            elif ch.isupper():
                out.append(upper[int(rng.integers(0, len(upper)))])
            elif ch.islower():
                out.append(lower[int(rng.integers(0, len(lower)))])
            else:
                out.append(ch)  # keep separators such as "-" or "."
        return "".join(out)

    result: list[str] = []
    seen: set[str] = set()
    attempts = 0
    while len(result) < n and attempts < n * 50:
        attempts += 1
        value = make_one()
        if value in taken or value in seen:
            continue
        seen.add(value)
        result.append(value)
    while len(result) < n:  # extremely unlikely: fall back to a numbered value
        result.append(f"SYN-{len(result):09d}")
    return pd.Series(result, dtype=object)


class IdentifierLeakageCheck(BaseCheck):
    """Share of synthetic identifier values copied verbatim from the real data."""

    check_id = "identifier_leakage"

    def run(self, real_data: Any, synth_data: Any, **kwargs: Any) -> CheckResult:
        seed = int(kwargs.get("seed", 1234))
        if not isinstance(real_data, pd.DataFrame) or not isinstance(synth_data, pd.DataFrame):
            return CheckResult(
                check_id=self.check_id,
                value=1.0,
                seed=seed,
                state="FAIL",
                error="Expected pandas DataFrame inputs",
            )

        # Compared with the training data only: those are the records the generator saw.
        # (A chance match with an unseen holdout ID in a small ID space is not copying.)
        id_cols = detect_identifier_columns(real_data)
        per_column: dict[str, float] = {}
        for col in id_cols:
            if col not in synth_data.columns:
                continue
            real_values = set(real_data[col].dropna().astype(str))
            synth_values = synth_data[col].dropna().astype(str)
            if len(synth_values) == 0:
                continue
            per_column[col] = float(synth_values.isin(real_values).mean())

        value = max(per_column.values()) if per_column else 0.0
        worst = max(per_column, key=lambda k: per_column[k]) if per_column else ""
        return CheckResult(
            check_id=self.check_id,
            value=value,
            n=len(synth_data),
            seed=seed,
            identifier_columns=id_cols,
            per_column=per_column,
            worst_column=worst,
            note=(
                "No identifier-like columns detected"
                if not id_cols
                else "Share of synthetic identifiers that copy a training-data identifier"
            ),
        )
