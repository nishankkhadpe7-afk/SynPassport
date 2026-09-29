"""Ed25519 cryptographic keypair generation utility.

Generates local signing key and public key files with restricted file permissions (0600),
where key_id is computed as the SHA-256 digest of the public key bytes.
"""

import hashlib
import os
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from synpassport.passport.signer import load_public_key

__all__ = ["compute_key_id", "generate_keypair"]


def compute_key_id(public_key: Any) -> str:
    """Compute deterministic key_id as the SHA-256 digest of raw Ed25519 public key bytes."""
    pub_key = load_public_key(public_key)
    raw_bytes = pub_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return hashlib.sha256(raw_bytes).hexdigest()


def generate_keypair(
    output_dir: str | Path,
    key_name: str = "ed25519",
) -> tuple[Path, Path, str]:
    """Generate Ed25519 signing keypair in designated directory.

    Sets private key file permissions to 0600.
    Returns (private_key_path, public_key_path, key_id).
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    priv_path = out_path / f"{key_name}_private.pem"
    pub_path = out_path / f"{key_name}_public.pem"

    priv_path.write_bytes(priv_pem)
    try:
        os.chmod(priv_path, 0o600)
    except OSError:
        pass

    pub_path.write_bytes(pub_pem)
    key_id = compute_key_id(public_key)

    return priv_path, pub_path, key_id


def main() -> None:
    """CLI entrypoint for keypair generation."""
    priv_path, pub_path, key_id = generate_keypair(Path("./keys"))
    print(f"Generated Ed25519 keypair:\nPrivate: {priv_path}\nPublic: {pub_path}\nKey ID: {key_id}")


if __name__ == "__main__":
    main()
