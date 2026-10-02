"""Evidence Passport creation, canonical serialization, signing, and verification."""

from synpassport.passport.builder import (
    EvidencePassport,
    approve_passport,
    build_passport,
    get_code_version,
    verify_dataset_hash,
    verify_passport,
)
from synpassport.passport.canonical import (
    canonical_hash,
    canonical_json_dumps,
    hash_dataset_file,
    normalize_for_canonical,
)
from synpassport.passport.keygen import compute_key_id, generate_keypair
from synpassport.passport.signer import (
    load_private_key,
    load_public_key,
    sign_payload,
    verify_signature,
)
from synpassport.passport.trust import (
    TrustedKeyRegistry,
    compute_key_fingerprint,
    resolve_trusted_key,
    validate_passport_expiry,
)

__all__ = [
    "EvidencePassport",
    "TrustedKeyRegistry",
    "approve_passport",
    "build_passport",
    "canonical_hash",
    "canonical_json_dumps",
    "compute_key_fingerprint",
    "compute_key_id",
    "generate_keypair",
    "get_code_version",
    "hash_dataset_file",
    "load_private_key",
    "load_public_key",
    "normalize_for_canonical",
    "resolve_trusted_key",
    "sign_payload",
    "validate_passport_expiry",
    "verify_dataset_hash",
    "verify_passport",
    "verify_signature",
]
