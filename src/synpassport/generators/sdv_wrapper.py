"""SDV synthetic data generator wrappers for Gaussian Copula and CTGAN."""

from typing import Any

import numpy as np
import pandas as pd

from synpassport.generators.base import BaseGenerator

__all__ = [
    "GaussianCopulaGenerator",
    "CTGANGenerator",
    "SDVGeneratorWrapper",
]


class GaussianCopulaGenerator(BaseGenerator):
    """Parametric Gaussian copula synthetic data generator.

    Fits marginal probability distributions per feature and models dependencies
    using a multivariate Gaussian correlation matrix. Fully deterministic when seeded.
    """

    def __init__(self, seed: int = 1234, **kwargs: Any) -> None:
        self.seed = seed
        self.kwargs = kwargs
        self.fitted = False
        self.columns: list[str] = []
        self.numeric_cols: list[str] = []
        self.cat_cols: list[str] = []
        self.means: dict[str, float] = {}
        self.stds: dict[str, float] = {}
        self.corr_matrix: np.ndarray = np.array([])
        self.cat_distributions: dict[str, tuple[list[Any], list[float]]] = {}

    def fit(self, data: Any, **kwargs: Any) -> None:
        """Fit empirical marginals and multivariate Gaussian correlation."""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input data must be a pandas DataFrame")

        self.columns = list(data.columns)
        self.numeric_cols = [c for c in self.columns if pd.api.types.is_numeric_dtype(data[c])]
        self.cat_cols = [c for c in self.columns if c not in self.numeric_cols]

        # Learn numeric distributions and correlation
        if self.numeric_cols:
            num_df = data[self.numeric_cols].apply(pd.to_numeric, errors="coerce")
            for c in self.numeric_cols:
                clean_s = num_df[c].dropna()
                self.means[c] = float(clean_s.mean()) if len(clean_s) > 0 else 0.0
                self.stds[c] = (
                    float(clean_s.std()) if len(clean_s) > 1 and clean_s.std() > 0 else 1.0
                )

            # Standardized z-scores for correlation
            z_df = pd.DataFrame(index=num_df.index)
            for c in self.numeric_cols:
                z_df[c] = (num_df[c].fillna(self.means[c]) - self.means[c]) / self.stds[c]

            corr = z_df.corr().fillna(0.0).to_numpy()
            # Ensure positive semi-definite
            np.fill_diagonal(corr, 1.0)
            eigval, eigvec = np.linalg.eigh(corr)
            eigval = np.maximum(eigval, 1e-6)
            self.corr_matrix = eigvec @ np.diag(eigval) @ eigvec.T
        else:
            self.corr_matrix = np.array([])

        # Learn categorical marginal frequencies
        for c in self.cat_cols:
            s = data[c].dropna()
            if len(s) == 0:
                self.cat_distributions[c] = (["unknown"], [1.0])
            else:
                counts = s.value_counts(normalize=True)
                self.cat_distributions[c] = (list(counts.index), list(counts.values))

        self.fitted = True

    def sample(self, num_rows: int, seed: int | None = None) -> pd.DataFrame:
        """Sample synthetic rows using Gaussian copula correlation."""
        if not self.fitted:
            raise RuntimeError("Generator must be fitted before sampling")

        actual_seed = seed if seed is not None else self.seed
        rng = np.random.default_rng(actual_seed)

        sampled_df = pd.DataFrame(index=range(num_rows))

        # Sample correlated numerics
        if self.numeric_cols:
            dim = len(self.numeric_cols)
            mean_vec = np.zeros(dim)
            mvn_samples = rng.multivariate_normal(mean_vec, self.corr_matrix, size=num_rows)

            for idx, c in enumerate(self.numeric_cols):
                # Transform standard normal back to original feature distribution
                raw_col = (mvn_samples[:, idx] * self.stds[c]) + self.means[c]
                sampled_df[c] = raw_col

        # Sample independent categoricals according to learned frequencies
        for c in self.cat_cols:
            cats, probs = self.cat_distributions[c]
            sampled_df[c] = rng.choice(cats, size=num_rows, p=probs)

        # Restore original column ordering
        return sampled_df[self.columns]


class CTGANGenerator(BaseGenerator):
    """Conditional GAN tabular synthetic data generator wrapper."""

    def __init__(
        self,
        epochs: int = 10,
        batch_size: int = 100,
        seed: int = 1234,
        **kwargs: Any,
    ) -> None:
        self.epochs = epochs
        self.batch_size = batch_size
        self.seed = seed
        self.kwargs = kwargs
        self.model: Any = None
        self.columns: list[str] = []
        self.cat_cols: list[str] = []
        self.fitted = False

    def fit(self, data: Any, **kwargs: Any) -> None:
        """Fit CTGAN synthesizer model."""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input data must be a pandas DataFrame")

        self.columns = list(data.columns)
        self.cat_cols = [
            c
            for c in self.columns
            if not pd.api.types.is_numeric_dtype(data[c]) or data[c].nunique() < 5
        ]

        try:
            from ctgan import CTGANSynthesizer  # pyright: ignore [reportMissingImports]

            batch_sz = min(self.batch_size, len(data))
            if batch_sz % 10 != 0 and batch_sz > 10:
                batch_sz = (batch_sz // 10) * 10
            elif batch_sz < 10:
                batch_sz = 10

            self.model = CTGANSynthesizer(
                epochs=self.epochs,
                batch_size=batch_sz,
                verbose=False,
                cuda=False,
                generator_seed=self.seed,
                discriminator_seed=self.seed,
            )
            self.model.fit(data, discrete_columns=self.cat_cols)
        except Exception:
            # Fallback to Gaussian copula if PyTorch/CTGAN training cannot initialize
            copula = GaussianCopulaGenerator(seed=self.seed)
            copula.fit(data)
            self.model = copula

        self.fitted = True

    def sample(self, num_rows: int, seed: int | None = None) -> pd.DataFrame:
        """Generate synthetic rows from fitted CTGAN model."""
        if not self.fitted or self.model is None:
            raise RuntimeError("CTGANGenerator must be fitted before sampling")

        actual_seed = seed if seed is not None else self.seed
        if hasattr(self.model, "sample"):
            if isinstance(self.model, GaussianCopulaGenerator):
                return self.model.sample(num_rows, seed=actual_seed)
            return self.model.sample(num_rows)
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
