"""SynPassport SDK for dataset verification and protected loading."""

from synpassport.sdk.guard import PassportError, load_dataset
from synpassport.sdk.verify import VerificationResult, verify

__all__ = ["verify", "load_dataset", "VerificationResult", "PassportError"]
