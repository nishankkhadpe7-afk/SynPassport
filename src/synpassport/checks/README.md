# Assurance & Statistical Checks Pipeline (`synpassport.checks`)

The `synpassport.checks` module implements the statistical, privacy, fidelity, utility, and power analysis checks that evaluate synthetic datasets against real training data and holdout sets.

---

## Component Structure

```
src/synpassport/checks/
├── base.py         # Abstract BaseCheck class & CheckContext definition
├── bootstrap.py    # Non-parametric bootstrap confidence interval calculator
├── fidelity.py     # Marginal distributions & Correlation structure checks
├── privacy.py      # DCR vs Holdout & Distance-based MIA privacy checks
├── run.py          # CHECK_REGISTRY & pipeline orchestrator run_checks_pipeline()
├── schema.py       # Structural schema validity check
├── splitter.py     # Deterministic 50/50 train vs holdout dataset splitter
├── subgroups.py    # Subgroup performance utility checks
├── sufficiency.py  # Power analysis sample sufficiency check
└── utility.py      # TSTR (Train synthetic, Test real) vs TRTR utility ratio check
```

---

## The 8 Standard Checks

All checks produce an `EvidenceRecord` containing metric values, 95% bootstrap confidence intervals (`ci_low`, `ci_high`), threshold reference values, and execution states (`PASS`, `FAIL`, `INSUFFICIENT_EVIDENCE`).

### 1. `schema_validity` ([`schema.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/schema.py))
Verifies that the synthetic dataset matches the expected tabular structure of the real dataset.
- **Metrics**: Column count mismatch, missing required columns, incompatible data types.
- **Threshold**: Zero schema violations (`value == 0.0`).

### 2. `marginal_fidelity` ([`fidelity.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/fidelity.py))
Measures distribution similarity across individual feature columns.
- **Numeric Columns**: 1D Wasserstein Distance (Earth Mover's Distance).
- **Categorical Columns**: Jensen-Shannon Distance ($0 \le JSD \le 1$).
- **Aggregation**: Mean distance across all columns.
- **Threshold**: `mean_distance <= max_marginal_distance` (e.g. `0.15`).

### 3. `correlation_fidelity` ([`fidelity.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/fidelity.py))
Measures preservation of bivariate feature dependencies.
- **Numeric Features**: Difference between Pearson correlation matrices $\|R_{real} - R_{synth}\|_F$.
- **Categorical Features**: Difference between Cramér's V association matrices.
- **Threshold**: Frobenius norm difference $\le 0.20$.

### 4. `utility_tstr_ratio` ([`utility.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/utility.py))
Evaluates machine learning model downstream performance using Train synthetic, Test real (TSTR) compared to Train real, Test real (TRTR).
- **Classification**: $\text{Ratio} = \frac{\text{AUC}_{TSTR}}{\text{AUC}_{TRTR}}$
- **Regression**: $\text{Ratio} = \frac{R^2_{TSTR}}{R^2_{TRTR}}$
- **Threshold**: $\text{Ratio} \ge 0.80$.

### 5. `subgroup_utility_ci` ([`subgroups.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/subgroups.py))
Evaluates predictive performance across key demographic or domain subgroups to prevent algorithmic bias or subset performance degradation.
- **Method**: Calculates accuracy/AUC per subgroup with 1000-sample bootstrap CIs.

### 6. `privacy_dcr_vs_holdout` ([`privacy.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/privacy.py))
Distance to Closest Record (DCR) privacy audit to detect memorization and overfitting.
- **Method**:
  1. Real dataset is split 50/50 into `R_train` and `R_holdout` deterministically via `split_train_holdout()`.
  2. Features are MinMax normalized to $[0, 1]$.
  3. For each synthetic record $s_i$, compute Euclidean $d_{train}(s_i) = \min_{r \in R_{train}} \|s_i - r\|_2$ and $d_{holdout}(s_i) = \min_{h \in R_{holdout}} \|s_i - h\|_2$.
  4. Compute fraction of synthetic points closer to training set: $F_{closer} = P(d_{train} < d_{holdout})$.
  5. Run 1000 bootstrap iterations to establish 95% CI $[ci_{low}, ci_{high}]$.
- **Verdict Logic**:
  - `ci_low > 0.60` $\rightarrow$ **`FAIL`** (statistically significant overfitting/memorization).
  - `ci_low <= 0.60` and `ci_high >= 0.60` $\rightarrow$ **`INSUFFICIENT_EVIDENCE`** (confidence interval spans threshold).
  - `ci_high < 0.60` $\rightarrow$ **`PASS`**.

### 7. `membership_inference_auc` ([`privacy.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/privacy.py))
Evaluates vulnerability to distance-based Membership Inference Attacks (MIA).
- **Method**: Uses DCR distributions of training vs holdout records to train an optimal decision boundary classifier predicting membership.
- **Bootstrap**: 1000 resamples for 95% CI $[ci_{low}, ci_{high}]$ on MIA AUC.
- **Verdict Logic**:
  - `ci_low > 0.55` $\rightarrow$ **`FAIL`** (vulnerable to membership leakage).
  - `ci_high <= 0.55` $\rightarrow$ **`PASS`**.
  - Otherwise $\rightarrow$ **`INSUFFICIENT_EVIDENCE`**.

### 8. `sufficiency` ([`sufficiency.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/sufficiency.py))
Statistical power analysis checking whether synthetic sample size $N_{synth}$ provides adequate statistical power for downstream inference.

---

## Execution Pipeline ([`run.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/run.py))

The entrypoint function `run_checks_pipeline()` coordinates execution:

```python
from synpassport.checks.run import run_checks_pipeline

evidence_records = run_checks_pipeline(
    data_path="data/real.csv",
    synth_path="data/synthetic.csv",
    policy_id_or_path="policies/policy_hipaa.yaml",
    holdout_path=None, # Auto-split 50/50 if None
    seed=42
)
```
