"""Base interface for synthetic data generators."""

from abc import ABC, abstractmethod
from typing import Any

__all__ = ["BaseGenerator"]


class BaseGenerator(ABC):
    """Abstract base class for synthetic data generation models."""

    @abstractmethod
    def fit(self, data: Any, **kwargs: Any) -> None:
        """Fit generator model to training data."""
        raise NotImplementedError

    @abstractmethod
    def sample(self, num_rows: int, seed: int | None = None) -> Any:
        """Sample synthetic rows from fitted model using deterministic seed."""
        raise NotImplementedError
