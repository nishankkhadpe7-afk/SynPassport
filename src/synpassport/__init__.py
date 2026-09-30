"""SynPassport: Purpose-bound assurance agent for synthetic data.

Issues signed, hash-bound Evidence Passports with deterministic policy enforcement.
"""

from synpassport.sdk import PassportError, VerificationResult, load_dataset, verify

__version__ = "0.1.0"
__all__ = ["PassportError", "VerificationResult", "__version__", "load_dataset", "verify"]
