#!/usr/bin/env python3
"""
Test key ceremony helper for Powerfarm Bootstrap.

THIS IS NOT PART OF BOOTSTRAP.
It exists only so you can verify the bootstrap script on a test medium.

In production, founding-key.pem is created by a separate, human-run
ceremony and placed on the LAB device BEFORE bootstrap runs.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError as exc:
    print("ERROR: 'cryptography' package is required.")
    print("Install: pip install cryptography")
    raise SystemExit(1) from exc


def main():
    parser = argparse.ArgumentParser(description="Generate test founding key material")
    parser.add_argument(
        "--home",
        default=os.environ.get("POWERFARM_HOME", "/Volumes/LAB-8"),
        help="Powerfarm home directory",
    )
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help="Also write bootstrap-manifest.json",
    )
    args = parser.parse_args()

    home = Path(args.home)
    genesis_dir = home / "genesis"
    genesis_dir.mkdir(parents=True, exist_ok=True)

    # Generate Ed25519 key pair
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Serialize private key (PKCS#8, unencrypted)
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Serialize public key (SubjectPublicKeyInfo)
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Fingerprint = SHA-256 of DER-encoded SubjectPublicKeyInfo
    pub_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    fingerprint = hashlib.sha256(pub_der).hexdigest()

    # Write key files
    with open(genesis_dir / "founding-key.pem", "wb") as fh:
        fh.write(priv_pem)
    os.chmod(genesis_dir / "founding-key.pem", 0o600)

    with open(genesis_dir / "founding-key.pub.pem", "wb") as fh:
        fh.write(pub_pem)

    with open(genesis_dir / "fingerprint.sha256", "w", encoding="utf-8") as fh:
        fh.write(fingerprint + "\n")

    # Write ceremony.txt (placeholder)
    with open(genesis_dir / "ceremony.txt", "w", encoding="utf-8") as fh:
        fh.write("Key ceremony placeholder.\n")
        fh.write("In production, this file documents the human ceremony.\n")

    print(f"Generated founding key material in: {genesis_dir}")
    print(f"  Fingerprint: {fingerprint}")

    if args.write_manifest:
        manifest = {
            "institution": "powerfarm",
            "bootstrapAuthority": f"founding:{fingerprint}",
            "allowed": [
                "rules.genesis",
                "institution.registered",
                "principal.registered",
                "authority.granted",
                "institution.transitioned",
                "bootstrap.completed",
            ],
            "terminatesOn": "bootstrap.completed",
        }
        with open(home / "bootstrap-manifest.json", "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
            fh.write("\n")
        print(f"  Wrote: {home / 'bootstrap-manifest.json'}")

    print()
    print("To run bootstrap:")
    print(f"  python bootstrap.py bootstrap --home {home}")


if __name__ == "__main__":
    main()
