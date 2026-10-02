# Synthetic Data Generators (`synpassport.generators`)

The `synpassport.generators` module provides abstract wrappers for tabular synthetic data generation engines integrated with Differential Privacy (DP) controls.

---

## Submodule Architecture

- [`base.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/generators/base.py): `BaseGenerator` abstract interface.
- [`sdv_wrapper.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/generators/sdv_wrapper.py): Wrappers for SDV algorithms (`GaussianCopulaGenerator`, `CTGANGenerator`).

---

## Supported Generator Engines

### 1. `GaussianCopulaGenerator`
- Parametric multivariate copula model.
- Fast execution for low-dimensional tabular numerical/categorical data.

### 2. `CTGANGenerator`
- Conditional GAN architecture designed for tabular data distributions.
- Supports hyperparameter tuning (`epochs`, `batch_size`, `embedding_dim`).
- **Differential Privacy (DP) Training Support**:
  - `dp_enabled: bool`
  - `dp_epsilon: float` (e.g. `3.0`)
  - `dp_delta: float` (e.g. `1e-5`)
