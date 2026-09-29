"""Ed25519 digital signature signing and verification service.

Signs canonical passport bytes using an Ed25519 private key and verifies signatures
with the corresponding public key. Signs over canonical bytes excluding the 'signature' field.
"""

import base64
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from synpassport.passport.canonical import canonical_json_dumps

__all__ = [
    "load_private_key",
    "load_public_key",
    "sign_payload",
    "verify_signature",
]


def load_private_key(key_input: Any) -> ed25519.Ed25519PrivateKey:
    """Load an Ed25519 private key from an object, file path, PEM string, or raw bytes."""
    if isinstance(key_input, ed25519.Ed25519PrivateKey):
        return key_input
    if isinstance(key_input, (str, Path)):
        p = Path(key_input)
        if p.is_file():
            data = p.read_bytes()
        else:
            data = str(key_input).encode("utf-8")
    elif isinstance(key_input, bytes):
        data = key_input
    else:
        raise TypeError(f"Unsupported private key input type: {type(key_input).__name__}")

    if b"BEGIN " in data:
        key = serialization.load_pem_private_key(data, password=None)
        if isinstance(key, ed25519.Ed25519PrivateKey):
            return key
        raise TypeError("Loaded key is not an Ed25519 private key")
    if len(data) == 32:
        return ed25519.Ed25519PrivateKey.from_private_bytes(data)

    raise ValueError("Invalid Ed25519 private key format")


def load_public_key(key_input: Any) -> ed25519.Ed25519PublicKey:
    """Load an Ed25519 public key from an object, file path, PEM string, or raw bytes."""
    if isinstance(key_input, ed25519.Ed25519PublicKey):
        return key_input
    if isinstance(key_input, ed25519.Ed25519PrivateKey):
        return key_input.public_key()
    if isinstance(key_input, (str, Path)):
        p = Path(key_input)
        if p.is_file():
            data = p.read_bytes()
        else:
            data = str(key_input).encode("utf-8")
    elif isinstance(key_input, bytes):
        data = key_input
    else:
        raise TypeError(f"Unsupported public key input type: {type(key_input).__name__}")

    if b"BEGIN " in data:
        key = serialization.load_pem_public_key(data)
        if isinstance(key, ed25519.Ed25519PublicKey):
            return key
        raise TypeError("Loaded key is not an Ed25519 public key")
    if len(data) == 32:
        return ed25519.Ed25519PublicKey.from_public_bytes(data)

    raise ValueError("Invalid Ed25519 public key format")


def sign_payload(
    payload: dict[str, Any] | bytes,
    signing_key: Any,
) -> str:
    """Generate Ed25519 signature in base64 over canonical bytes excluding 'signature'."""
    if isinstance(payload, dict):
        clean_payload = {k: v for k, v in payload.items() if k != "signature"}
        target_bytes = canonical_json_dumps(clean_payload)
    elif isinstance(payload, bytes):
        target_bytes = payload
    else:
        raise TypeError(f"Payload must be dict or bytes, got {type(payload).__name__}")

    priv_key = load_private_key(signing_key)
    signature_bytes = priv_key.sign(target_bytes)
    return base64.b64encode(signature_bytes).decode("ascii")


def verify_signature(
    payload: dict[str, Any] | bytes,
    signature_b64: str,
    public_key: Any,
) -> bool:
    """Verify Ed25519 base64 signature against canonical payload bytes and public key."""
    try:
        if not signature_b64:
            return False
        if isinstance(payload, dict):
            clean_payload = {k: v for k, v in payload.items() if k != "signature"}
            target_bytes = canonical_json_dumps(clean_payload)
        else:
            target_bytes = payload

        pub_key = load_public_key(public_key)
        sig_bytes = base64.b64decode(signature_b64)
        pub_key.verify(sig_bytes, target_bytes)
        return True
    except (InvalidSignature, ValueError, TypeError, OSError):
        return False
    except Exception:
        return False
