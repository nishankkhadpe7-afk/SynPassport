"""SDV synthetic data generator wrappers for Gaussian Copula and CTGAN."""

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm

from synpassport.checks.identifiers import (
    detect_datetime_format,
    detect_identifier_columns,
    fresh_identifiers,
)
from synpassport.generators.base import BaseGenerator

__all__ = [
    "GaussianCopulaGenerator",
    "CTGANGenerator",
    "SDVGeneratorWrapper",
]


_CONTINUOUS_MIN_UNIQUE = 20
# Text columns with more distinct values than this are identifier-like (IDs, timestamps).
# One-hot encoding them would make CTGAN's input thousands of columns wide and can exhaust
# memory, so CTGAN learns the other columns and these are drawn from their own marginals.
_CTGAN_MAX_CATEGORIES = 200


class _ColumnModel:
    """Empirical marginal for one column, mapped to and from the unit interval."""

    def __init__(self, series: pd.Series) -> None:
        self.dtype = series.dtype
        non_null = series.dropna()
        self.missing_rate = float(series.isna().mean()) if len(series) else 0.0
        is_float = pd.api.types.is_float_dtype(series)
        self.continuous = bool(
            is_float
            and non_null.nunique() >= _CONTINUOUS_MIN_UNIQUE
            and not np.all(np.mod(non_null.to_numpy(dtype=float), 1.0) == 0.0)
        )

        if len(non_null) == 0:
            self.continuous = False
            self.values: np.ndarray = np.array(["unknown"], dtype=object)
            self.cum_probs: np.ndarray = np.array([1.0])
            return

        if self.continuous:
            self.values = np.sort(non_null.to_numpy(dtype=float))
            n = len(self.values)
            self.positions = (np.arange(n) + 0.5) / n
        else:
            counts = non_null.value_counts()
            if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
                counts = counts.sort_index()  # ordered numeric categories keep their order
            self.values = np.array(list(counts.index), dtype=object)
            probs = counts.to_numpy(dtype=float) / counts.sum()
            self.cum_probs = np.cumsum(probs)
            self.cum_probs[-1] = 1.0
            self._value_to_mid = {}
            lower = 0.0
            for val, upper in zip(self.values, self.cum_probs, strict=True):
                self._value_to_mid[val] = (lower + upper) / 2.0
                lower = float(upper)

    def to_uniform(self, series: pd.Series) -> np.ndarray:
        """Map observed values to (0, 1); missing values map to the median (0.5)."""
        out = np.full(len(series), 0.5)
        mask = series.notna().to_numpy()
        if not mask.any():
            return out
        if self.continuous:
            vals = series[mask].to_numpy(dtype=float)
            out[mask] = np.interp(vals, self.values, self.positions)
        else:
            out[mask] = [self._value_to_mid.get(v, 0.5) for v in series[mask]]
        return out

    def from_uniform(self, u: np.ndarray, rng: np.random.Generator) -> pd.Series:
        """Map uniform draws back to values drawn from the empirical marginal."""
        if self.continuous:
            result = pd.Series(np.interp(u, self.positions, self.values))
        else:
            idx = np.clip(np.searchsorted(self.cum_probs, u, side="right"), 0, len(self.values) - 1)
            result = pd.Series(self.values[idx])
            try:
                result = result.astype(self.dtype)
            except (TypeError, ValueError):
                pass
        if self.missing_rate > 0:
            missing = rng.random(len(u)) < self.missing_rate
            result = result.where(~missing)
        return result


_SECONDS_PER_DAY = 86400.0


class _TablePrep:
    """Prepares a table for a generator and restores the generator's output.

    * Identifier columns (all-unique text keys) are left out of the model and filled
      afterwards, either by resampling real values or, when ``regenerate_identifiers``
      is on, with fresh values in the same format so no real identifier is copied.
    * Text datetimes are modelled as fractional days and written back in their format.
    """

    def __init__(self, regenerate_identifiers: bool = False) -> None:
        self.regenerate_identifiers = regenerate_identifiers
        self.columns: list[str] = []
        self.side_cols: list[str] = []
        self.side_models: dict[str, _ColumnModel] = {}
        self.side_real: dict[str, pd.Series] = {}
        self.dt_formats: dict[str, str] = {}

    def fit_transform(
        self, data: pd.DataFrame, extra_side: list[str] | None = None
    ) -> pd.DataFrame:
        self.columns = list(data.columns)
        ids = detect_identifier_columns(data)
        self.side_cols = ids + [c for c in (extra_side or []) if c not in ids]
        self.side_models = {c: _ColumnModel(data[c]) for c in self.side_cols}
        self.side_real = {c: data[c].copy() for c in self.side_cols}
        model_df = data[[c for c in self.columns if c not in self.side_cols]].copy()
        self.dt_formats = {}
        for col in list(model_df.columns):
            fmt = detect_datetime_format(model_df[col])
            if fmt is None:
                continue
            self.dt_formats[col] = fmt
            parsed = pd.to_datetime(model_df[col].astype(str), format=fmt, errors="coerce")
            days = (parsed - pd.Timestamp("1970-01-01")) / pd.Timedelta(days=1)
            # A tiny offset keeps whole-day dates on the continuous path of the copula.
            model_df[col] = days.astype(float) + 1e-7
        return model_df

    def restore(self, out: pd.DataFrame, num_rows: int, rng: np.random.Generator) -> pd.DataFrame:
        out = out.reset_index(drop=True)
        for col, fmt in self.dt_formats.items():
            if col in out.columns:
                days = pd.to_numeric(out[col], errors="coerce")
                ts = pd.Timestamp("1970-01-01") + pd.to_timedelta(days * _SECONDS_PER_DAY, unit="s")
                out[col] = ts.dt.round("s").dt.strftime(fmt)
        for col in self.side_cols:
            if self.regenerate_identifiers and col in detect_identifier_columns(
                self.side_real[col].to_frame()
            ):
                out[col] = fresh_identifiers(self.side_real[col], num_rows, rng).to_numpy()
            else:
                out[col] = self.side_models[col].from_uniform(rng.random(num_rows), rng).to_numpy()
        return out[self.columns]


class GaussianCopulaGenerator(BaseGenerator):
    """Gaussian copula synthetic data generator.

    Each column keeps its own empirical marginal distribution (so integer, binary and
    categorical columns stay integer, binary and categorical), while dependencies between
    columns are modelled by a multivariate normal on normal scores. Fully deterministic
    when seeded.
    """

    def __init__(
        self, seed: int = 1234, regenerate_identifiers: bool = False, **kwargs: Any
    ) -> None:
        self.seed = seed
        self.kwargs = kwargs
        self.fitted = False
        self.columns: list[str] = []
        self.column_models: dict[str, _ColumnModel] = {}
        self.corr_matrix: np.ndarray = np.array([])
        self.prep = _TablePrep(regenerate_identifiers=regenerate_identifiers)

    def fit(self, data: Any, **kwargs: Any) -> None:
        """Fit per-column empirical marginals and the normal-score correlation."""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input data must be a pandas DataFrame")

        data = self.prep.fit_transform(data)
        self.columns = list(data.columns)
        self.column_models = {c: _ColumnModel(data[c]) for c in self.columns}

        if self.columns and len(data) > 1:
            eps = 1e-6
            z = np.column_stack(
                [
                    norm.ppf(np.clip(self.column_models[c].to_uniform(data[c]), eps, 1 - eps))
                    for c in self.columns
                ]
            )
            with np.errstate(invalid="ignore", divide="ignore"):
                corr = np.corrcoef(z, rowvar=False)
            corr = np.atleast_2d(np.nan_to_num(corr, nan=0.0))
            np.fill_diagonal(corr, 1.0)
            # Ensure positive semi-definite
            eigval, eigvec = np.linalg.eigh(corr)
            eigval = np.maximum(eigval, 1e-6)
            self.corr_matrix = eigvec @ np.diag(eigval) @ eigvec.T
        else:
            self.corr_matrix = np.eye(len(self.columns))

        self.fitted = True

    def sample(self, num_rows: int, seed: int | None = None) -> pd.DataFrame:
        """Sample synthetic rows preserving marginals and pairwise dependence."""
        if not self.fitted:
            raise RuntimeError("Generator must be fitted before sampling")

        actual_seed = seed if seed is not None else self.seed
        rng = np.random.default_rng(actual_seed)

        dim = len(self.columns)
        if dim == 0:
            return self.prep.restore(pd.DataFrame(index=range(num_rows)), num_rows, rng)
        z = rng.multivariate_normal(np.zeros(dim), self.corr_matrix, size=num_rows)
        u = norm.cdf(z)

        sampled = {
            c: self.column_models[c].from_uniform(u[:, idx], rng).to_numpy()
            for idx, c in enumerate(self.columns)
        }
        return self.prep.restore(pd.DataFrame(sampled, columns=self.columns), num_rows, rng)


class CTGANGenerator(BaseGenerator):
    """Conditional GAN tabular synthetic data generator wrapper."""

    def __init__(
        self,
        epochs: int = 10,
        batch_size: int = 100,
        seed: int = 1234,
        regenerate_identifiers: bool = False,
        **kwargs: Any,
    ) -> None:
        self.regenerate_identifiers = regenerate_identifiers
        self.prep = _TablePrep(regenerate_identifiers=regenerate_identifiers)
        self.epochs = epochs
        self.batch_size = batch_size
        self.seed = seed
        self.kwargs = kwargs
        self.model: Any = None
        self.columns: list[str] = []
        self.cat_cols: list[str] = []
        self.fitted = False
        # Name of the model that was actually trained (may differ if CTGAN is unavailable).
        self.backend = "CTGAN"
        self.fallback_reason: str | None = None

    def fit(self, data: Any, **kwargs: Any) -> None:
        """Fit CTGAN synthesizer model."""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input data must be a pandas DataFrame")

        self.columns = list(data.columns)
        # Text columns with very many distinct values would make CTGAN's one-hot input
        # enormous (and can exhaust memory), so they are filled outside the model too.
        high_card = [
            c
            for c in self.columns
            if not pd.api.types.is_numeric_dtype(data[c])
            and data[c].nunique() > _CTGAN_MAX_CATEGORIES
            and detect_datetime_format(data[c]) is None
        ]
        model_df = self.prep.fit_transform(data, extra_side=high_card)
        model_cols = list(model_df.columns)
        self.cat_cols = [
            c
            for c in model_cols
            if not pd.api.types.is_numeric_dtype(model_df[c]) or model_df[c].nunique() < 5
        ]
        self.note: str | None = None
        side = self.prep.side_cols
        if side:
            action = (
                "replaced with fresh values in the same format"
                if self.regenerate_identifiers
                else "drawn from their own distributions"
            )
            self.note = (
                f"{len(side)} identifier-like column(s) "
                f"({', '.join(side[:5])}{'…' if len(side) > 5 else ''}) "
                f"{action}; CTGAN modelled the rest"
            )

        try:
            batch_sz = min(self.batch_size, len(data))
            # CTGAN needs the batch size to be a multiple of its pac size (10).
            batch_sz = max(10, (batch_sz // 10) * 10)

            try:
                # ctgan >= 0.5 exposes the class as CTGAN
                from ctgan import CTGAN  # pyright: ignore [reportMissingImports]

                self.model = CTGAN(
                    epochs=self.epochs,
                    batch_size=batch_sz,
                    verbose=False,
                    enable_gpu=False,
                )
                self.model.set_random_state(self.seed)
            except ImportError:
                # older ctgan releases used CTGANSynthesizer
                from ctgan import CTGANSynthesizer  # pyright: ignore [reportMissingImports]

                self.model = CTGANSynthesizer(
                    epochs=self.epochs,
                    batch_size=batch_sz,
                    verbose=False,
                    cuda=False,
                )
            if not model_cols:
                raise ValueError("every column is identifier-like; nothing for CTGAN to learn")
            self.model.fit(model_df, discrete_columns=self.cat_cols)
        except Exception as exc:
            # Fallback to Gaussian copula if PyTorch/CTGAN training cannot initialize.
            # The fallback is recorded so evidence never claims CTGAN was used.
            copula = GaussianCopulaGenerator(
                seed=self.seed, regenerate_identifiers=self.regenerate_identifiers
            )
            copula.fit(data)
            self.model = copula
            self.backend = "GaussianCopula"
            self.note = None
            self.fallback_reason = f"CTGAN unavailable ({type(exc).__name__}: {exc})"

        self.fitted = True

    def sample(self, num_rows: int, seed: int | None = None) -> pd.DataFrame:
        """Generate synthetic rows from fitted CTGAN model."""
        if not self.fitted or self.model is None:
            raise RuntimeError("CTGANGenerator must be fitted before sampling")

        actual_seed = seed if seed is not None else self.seed
        if hasattr(self.model, "sample"):
            if isinstance(self.model, GaussianCopulaGenerator):
                return self.model.sample(num_rows, seed=actual_seed)
            if hasattr(self.model, "set_random_state"):
                self.model.set_random_state(actual_seed)
            out = self.model.sample(num_rows)
            return self.prep.restore(out, num_rows, np.random.default_rng(actual_seed))
        raise RuntimeError("Model does not support sample method")


class SDVGeneratorWrapper(BaseGenerator):
    """Unified wrapper supporting Gaussian Copula and CTGAN generation."""

    def __init__(
        self, model_type: str = "gaussian_copula", seed: int = 1234, **kwargs: Any
    ) -> None:
        self.model_type = model_type.lower()
        self.seed = seed
        self.kwargs = kwargs

        if self.model_type == "ctgan":
            self.generator: BaseGenerator = CTGANGenerator(seed=seed, **kwargs)
        else:
            self.generator = GaussianCopulaGenerator(seed=seed, **kwargs)

    def fit(self, data: Any, **kwargs: Any) -> None:
        """Fit the underlying generator."""
        self.generator.fit(data, **kwargs)

    def sample(self, num_rows: int, seed: int | None = None) -> pd.DataFrame:
        """Sample synthetic rows."""
        return self.generator.sample(num_rows, seed=seed)
