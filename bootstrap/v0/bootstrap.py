#!/usr/bin/env python3
"""
Powerfarm Institutional Bootstrap V0

A birth script, not a platform.

Bootstrap may create the institution once.
It may not govern the institution afterward.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Ed25519 via cryptography (only external dependency)
# ---------------------------------------------------------------------------
try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError as exc:  # pragma: no cover
    print("ERROR: 'cryptography' package is required.")
    print("Install: pip install cryptography")
    raise SystemExit(1) from exc

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
CLR = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "green": "\033[32m",
    "red": "\033[31m",
    "cyan": "\033[36m",
    "yellow": "\033[33m",
}


def _c(text: str, *codes: str) -> str:
    return "".join(CLR.get(c, "") for c in codes) + text + CLR["reset"]


# ---------------------------------------------------------------------------
# Hash helper
# ---------------------------------------------------------------------------
def _canonical_json(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def _hash_act(act: dict) -> str:
    return hashlib.sha256(_canonical_json(act)).hexdigest()


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def _abort(msg: str) -> None:
    print(_c(f"ABORT: {msg}", "red", "bold"), file=sys.stderr)
    raise SystemExit(1)


def _ok(msg: str) -> None:
    print(f"  {_c('✓', 'green')} {msg}")


def _step(msg: str) -> None:
    print(f"  {_c('◆', 'yellow', 'bold')} {msg}")


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------
def _load_manifest(home: Path) -> dict:
    path = home / "bootstrap-manifest.json"
    if not path.exists():
        _abort(f"Manifest not found: {path}")

    with open(path, "r", encoding="utf-8") as fh:
        try:
            manifest = json.load(fh)
        except json.JSONDecodeError as exc:
            _abort(f"Manifest is not valid JSON: {exc}")

    required = ["institution", "bootstrapAuthority", "allowed", "terminatesOn"]
    for field in required:
        if field not in manifest:
            _abort(f"Manifest missing required field: {field}")

    if not isinstance(manifest.get("allowed"), list):
        _abort("Manifest field 'allowed' must be a list")

    return manifest


# ---------------------------------------------------------------------------
# Key material
# ---------------------------------------------------------------------------
def _load_key_material(home: Path) -> tuple[Ed25519PrivateKey, str]:
    priv_path = home / "genesis" / "founding-key.pem"
    pub_path = home / "genesis" / "founding-key.pub.pem"
    fp_path = home / "genesis" / "fingerprint.sha256"

    for p in (priv_path, pub_path, fp_path):
        if not p.exists():
            _abort(f"Missing key material: {p}")

    # Load private key
    with open(priv_path, "rb") as fh:
        priv_key = serialization.load_pem_private_key(fh.read(), password=None)

    if not isinstance(priv_key, Ed25519PrivateKey):
        _abort("Founding key is not Ed25519")

    # Derive public key and verify against stored public key
    derived_pub = priv_key.public_key()
    derived_pub_pem = derived_pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    with open(pub_path, "rb") as fh:
        stored_pub_pem = fh.read()

    if derived_pub_pem != stored_pub_pem:
        _abort("Derived public key does not match stored public key")

    # Fingerprint = SHA-256 of DER-encoded SubjectPublicKeyInfo
    pub_der = derived_pub.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    fingerprint = hashlib.sha256(pub_der).hexdigest()

    with open(fp_path, "r", encoding="utf-8") as fh:
        stored_fp = fh.read().strip()

    if fingerprint != stored_fp:
        _abort(
            f"Fingerprint mismatch\n"
            f"  Calculated: {fingerprint}\n"
            f"  Expected:   {stored_fp}"
        )

    return priv_key, fingerprint


# ---------------------------------------------------------------------------
# Genesis Acts (prepared in memory before any write)
# ---------------------------------------------------------------------------
def _prepare_acts(manifest: dict, fingerprint: str) -> list[dict]:
    now = datetime.now(UTC).isoformat()
    actor = f"founding:{fingerprint}"

    acts: list[dict] = []

    # 1. rules.genesis
    acts.append(
        {
            "seq": 1,
            "domain": "rules",
            "type": "rules.genesis",
            "subject": "institution:powerfarm",
            "actor": actor,
            "authority": "bootstrap",
            "at": now,
            "payload": {},
            "prev": None,
        }
    )

    # 2. institution.registered
    acts.append(
        {
            "seq": 2,
            "domain": "registry",
            "type": "institution.registered",
            "subject": "institution:powerfarm",
            "actor": actor,
            "authority": "bootstrap",
            "at": now,
            "payload": {},
            "prev": _hash_act(acts[-1]),
        }
    )

    # 3. principal.registered
    acts.append(
        {
            "seq": 3,
            "domain": "registry",
            "type": "principal.registered",
            "subject": "principal:founder",
            "actor": actor,
            "authority": "bootstrap",
            "at": now,
            "payload": {},
            "prev": _hash_act(acts[-1]),
        }
    )

    # 4. authority.granted
    acts.append(
        {
            "seq": 4,
            "domain": "rules",
            "type": "authority.granted",
            "subject": "principal:founder",
            "actor": actor,
            "authority": "bootstrap",
            "at": now,
            "payload": {
                "scope": "constitutional",
                "description": "Initial constitutional authority for institutional governance",
            },
            "prev": _hash_act(acts[-1]),
        }
    )

    # 5. institution.transitioned  unborn → bootstrapping
    acts.append(
        {
            "seq": 5,
            "domain": "states",
            "type": "institution.transitioned",
            "subject": "institution:powerfarm",
            "actor": actor,
            "authority": "bootstrap",
            "at": now,
            "payload": {"from": "unborn", "to": "bootstrapping"},
            "prev": _hash_act(acts[-1]),
        }
    )

    # 6. institution.transitioned  bootstrapping → operational
    acts.append(
        {
            "seq": 6,
            "domain": "states",
            "type": "institution.transitioned",
            "subject": "institution:powerfarm",
            "actor": actor,
            "authority": "bootstrap",
            "at": now,
            "payload": {"from": "bootstrapping", "to": "operational"},
            "prev": _hash_act(acts[-1]),
        }
    )

    # 7. bootstrap.completed
    acts.append(
        {
            "seq": 7,
            "domain": "messages",
            "type": "bootstrap.completed",
            "subject": "institution:powerfarm",
            "actor": actor,
            "authority": "bootstrap",
            "at": now,
            "payload": {},
            "prev": _hash_act(acts[-1]),
        }
    )

    return acts


# ---------------------------------------------------------------------------
# Signature
# ---------------------------------------------------------------------------
def _sign_manifest(private_key: Ed25519PrivateKey, manifest: dict) -> str:
    """
    Signs the SHA-256 digest of the canonical bootstrap-manifest.json.

    What is signed:
      - Canonical JSON of the manifest (sorted keys, no whitespace)
      - SHA-256 digest of those bytes
      - The 32-byte digest is signed with the founding Ed25519 private key
    """
    digest = hashlib.sha256(_canonical_json(manifest)).digest()
    signature = private_key.sign(digest)
    return signature.hex()


# ---------------------------------------------------------------------------
# Write genesis (after all validation and preparation)
# ---------------------------------------------------------------------------
def _write_genesis(
    home: Path, acts: list[dict], signature_hex: str, manifest: dict
) -> None:
    ledgers_dir = home / "ledgers"
    ledgers_dir.mkdir(parents=True, exist_ok=True)

    canon_dir = home / "canon"
    canon_dir.mkdir(parents=True, exist_ok=True)

    # Store public signature
    with open(canon_dir / "genesis-signature.hex", "w", encoding="utf-8") as fh:
        fh.write(signature_hex + "\n")

    # Document exactly what was signed
    with open(canon_dir / "signature-documentation.txt", "w", encoding="utf-8") as fh:
        fh.write("SIGNATURE DOCUMENTATION\n")
        fh.write("=" * 55 + "\n\n")
        fh.write("What was signed:\n")
        fh.write("  1. Canonical JSON of bootstrap-manifest.json\n")
        fh.write("     (sorted keys, no whitespace, UTF-8)\n")
        fh.write("  2. SHA-256 digest of those bytes\n")
        fh.write("  3. The 32-byte digest was signed with the founding\n")
        fh.write("     Ed25519 private key\n\n")
        fh.write("Signature format: hex-encoded Ed25519 signature\n")
        fh.write("Stored in:        canon/genesis-signature.hex\n")
        fh.write("Key used:         founding Ed25519 private key\n")
        fh.write("Purpose:          Genesis commitment / bootstrap attestation\n")

    # Append each Act to its domain ledger
    domain_file = {
        "rules": "rules.jsonl",
        "registry": "registry.jsonl",
        "states": "states.jsonl",
        "messages": "messages.jsonl",
    }

    for act in acts:
        domain = act["domain"]
        filepath = ledgers_dir / domain_file[domain]
        with open(filepath, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(act, separators=(",", ":")) + "\n")


# ---------------------------------------------------------------------------
# Receipt
# ---------------------------------------------------------------------------
def _write_receipt(
    home: Path, manifest: dict, fingerprint: str, last_act: dict
) -> None:
    receipt = {
        "institution": manifest["institution"],
        "completed": True,
        "completedAt": datetime.now(UTC).isoformat(),
        "foundingFingerprint": fingerprint,
        "manifestHash": hashlib.sha256(_canonical_json(manifest)).hexdigest(),
        "lastGenesisAct": _hash_act(last_act),
    }

    with open(home / "bootstrap-receipt.json", "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=2)
        fh.write("\n")


# ---------------------------------------------------------------------------
# Detect incomplete bootstrap
# ---------------------------------------------------------------------------
def _detect_incomplete(home: Path) -> bool:
    """Return True if ledger files have content but no receipt exists."""
    receipt = home / "bootstrap-receipt.json"
    if receipt.exists():
        return False

    ledgers_dir = home / "ledgers"
    if not ledgers_dir.exists():
        return False

    for fname in ("rules.jsonl", "registry.jsonl", "states.jsonl", "messages.jsonl"):
        fpath = ledgers_dir / fname
        if fpath.exists() and fpath.stat().st_size > 0:
            return True

    return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="powerfarm",
        description="Powerfarm Institutional Bootstrap",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    boot = sub.add_parser("bootstrap", help="Perform institutional genesis")
    boot.add_argument(
        "--home",
        default=os.environ.get("POWERFARM_HOME", "/Volumes/LAB-8"),
        help="Powerfarm home directory (default: /Volumes/LAB-8 or $POWERFARM_HOME)",
    )
    return parser


def _print_banner() -> None:
    print()
    print(_c("POWERFARM · INSTITUTIONAL GENESIS", "bold", "cyan"))
    print()


def _print_success() -> None:
    print()
    print(_c("✓ BOOTSTRAP COMPLETE", "bold", "green"))
    print()
    print("Bootstrap authority has expired.")
    print("Powerfarm is operational.")
    print()


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command != "bootstrap":
        parser.print_help()
        return 2

    home = Path(args.home)

    # Validate home exists
    if not home.exists():
        _abort(f"POWERFARM_HOME does not exist: {home}")

    # Validate bootstrap has never completed
    receipt_path = home / "bootstrap-receipt.json"
    if receipt_path.exists():
        print()
        print(_c("ERROR: Bootstrap has already completed.", "red", "bold"))
        print("       Bootstrap authority has expired.")
        print("       Powerfarm is operational.")
        print()
        return 1

    # Detect incomplete state
    if _detect_incomplete(home):
        print()
        print(_c("ERROR: Incomplete bootstrap detected.", "red", "bold"))
        print("       Ledger files exist but bootstrap-receipt.json is missing.")
        print("       The institution is in an inconsistent state.")
        print("       Human intervention required.")
        print()
        return 1

    _print_banner()

    # 1. Validate manifest
    manifest = _load_manifest(home)
    _ok("manifest verified")

    # 2. Validate key material
    priv_key, fingerprint = _load_key_material(home)
    _ok("founding key verified")

    # 3. Verify manifest bootstrapAuthority matches key fingerprint
    expected_actor = f"founding:{fingerprint}"
    if manifest.get("bootstrapAuthority") != expected_actor:
        _abort(
            f"Manifest bootstrapAuthority mismatch\n"
            f"  Manifest:   {manifest.get('bootstrapAuthority')}\n"
            f"  Calculated: {expected_actor}"
        )
    _ok("bootstrap authority recognized")
    print()

    # 4. Prepare all seven Acts in memory
    acts = _prepare_acts(manifest, fingerprint)

    # 5. Sign manifest digest
    signature_hex = _sign_manifest(priv_key, manifest)

    # 6. Write genesis
    _step("admitting rules.genesis")
    _step("registering institution:powerfarm")
    _step("registering principal:founder")
    _step("establishing initial authority")
    _step("unborn → bootstrapping")
    _step("bootstrapping → operational")
    _step("recording bootstrap.completed")

    _write_genesis(home, acts, signature_hex, manifest)
    _write_receipt(home, manifest, fingerprint, acts[-1])

    _print_success()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
