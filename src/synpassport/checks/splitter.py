"""Train/holdout partitioner with holdout hash recording and agent isolation."""

import hashlib
from typing import Any

import numpy as np
import pandas as pd

__all__ = ["SplitResult", "split_train_holdout", "get_agent_partition_metadata"]


class SplitResult:
    """Encapsulates training and isolated holdout partitions with cryptographic binding."""

    def __init__(
        self,
        train_df: pd.DataFrame,
        holdout_df: pd.DataFrame,
        holdout_sha256: str,
        n_train: int,
        n_holdout: int,
        seed: int,
    ) -> None:
        self.train_df = train_df
        self.holdout_df = holdout_df
        self.holdout_sha256 = holdout_sha256
        self.n_train = n_train
        self.n_holdout = n_holdout
        self.seed = seed


def compute_dataframe_sha256(df: pd.DataFrame) -> str:
    """Compute deterministic SHA-256 digest of dataframe bytes."""
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(csv_bytes).hexdigest()


def split_train_holdout(
    data: pd.DataFrame,
    train_ratio: float = 0.5,
    seed: int = 1234,
) -> SplitResult:
    """Partition dataset into training and strictly isolated holdout partitions.

    Args:
        data: Input dataset as a pandas DataFrame.
        train_ratio: Proportion of rows allocated to training partition (default 0.50).
        seed: Random seed for deterministic row permutation.

    Returns:
        SplitResult containing train_df, holdout_df, and holdout_sha256 hash.
    """
    if len(data) < 2:
        raise ValueError("Dataset requires at least 2 rows to partition")

    rng = np.random.default_rng(seed)
    indices = np.arange(len(data))
    rng.shuffle(indices)

    split_point = max(1, int(len(data) * train_ratio))
    train_indices = indices[:split_point]
    holdout_indices = indices[split_point:]

    train_df = data.iloc[train_indices].reset_index(drop=True)
    holdout_df = data.iloc[holdout_indices].reset_index(drop=True)

    holdout_hash = compute_dataframe_sha256(holdout_df)

    return SplitResult(
        train_df=train_df,
        holdout_df=holdout_df,
        holdout_sha256=holdout_hash,
        n_train=len(train_df),
        n_holdout=len(holdout_df),
        seed=seed,
    )


def get_agent_partition_metadata(split_result: SplitResult) -> dict[str, Any]:
    """Expose only partition dimensions and holdout hash; holdout rows are withheld."""
    return {
        "n_train": split_result.n_train,
        "n_holdout": split_result.n_holdout,
        "holdout_sha256": split_result.holdout_sha256,
        "seed": split_result.seed,
    }
