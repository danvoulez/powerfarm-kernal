"""Build and verify the content-bound M2 Genesis material.

Candidate inputs are useful and reproducible, but ``--require-ready`` refuses
to call them final while a ratification, public key, or custody record is absent.
Private key material is intentionally never accepted by this format.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from kernel.canon import CanonValue, canonicalize, object_hash

from .registry_blueprint import Definition, build_definitions

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "genesis" / "material-input.candidate.json"
REGISTRY_OUTPUT = ROOT / "genesis" / "registry" / "manifest.candidate.json"
GENESIS_OUTPUT = ROOT / "genesis" / "manifest.candidate.json"

RATIFICATIONS = (
    "D-Genesis-04",
    "D-Director-03",
    "D-Director-04",
    "D-Director-05",
    "D-Director-06",
    "D-Director-07",
    "D-Director-08",
    "A-8",
    "A-9",
    "R-1",
    "R-4",
    "R-5",
    "R-12",
    "R-17",
    "R-19",
    "R-20",
)


class MaterialError(ValueError):
    pass


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise MaterialError(f"{label} must be an object")
    return cast(Mapping[str, object], value)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return dict(_mapping(value, str(path)))


def _constitutional(definition: Definition) -> bool:
    kind = str(definition["kind"])
    name = str(definition["name"])
    if kind in {"act_type", "command_type", "rule"}:
        return True
    if kind == "context_type":
        return name != "request.metadata"
    if kind == "mandate":
        return name in {"director.mandate.boundary.v1", "root.mandate.v1"}
    if kind == "projector":
        return name != "trajectory.graph"
    if kind == "relation_type":
        return name in {
            "anchored_at", "authorized_by", "caused_by", "forked_from", "notarized_by",
            "reviewed_by", "supersedes",
        }
    return False


def build_registry_manifest(source: Mapping[str, object]) -> dict[str, CanonValue]:
    choices = cast(Mapping[str, CanonValue], _mapping(source.get("choices"), "choices"))
    definitions = build_definitions(choices)
    entries: list[CanonValue] = []
    for definition in definitions:
        entries.append({
            "constitutional": _constitutional(definition),
            "definition_hash": object_hash("registry", definition),
            "definition": definition,
        })
    counts = Counter(str(definition["kind"]) for definition in definitions)
    content: dict[str, CanonValue] = {
        "format": "powerfarm-registry-manifest-v1",
        "canonicalization": "rfc8785-jcs-v1",
        "hash": "sha256",
        "ratification_status": str(source.get("status", "candidate")),
        "definition_count": len(entries),
        "counts_by_kind": dict(sorted(counts.items())),
        "definitions": entries,
    }
    content["manifest_hash"] = object_hash("registry_manifest", content)
    return content


def _document_hash(path: Path) -> str:
    return hashlib.sha256(b"powerfarm:document:v1" + path.read_bytes()).hexdigest()


def material_blockers(source: Mapping[str, object]) -> tuple[str, ...]:
    blockers: list[str] = []
    ratifications = _mapping(source.get("ratifications"), "ratifications")
    for decision in RATIFICATIONS:
        if ratifications.get(decision) != "RATIFIED":
            blockers.append(f"{decision} is not RATIFIED")
    if source.get("constitution_ratified") is not True:
        blockers.append("Genesis Constitution is not ratified")

    choices = _mapping(source.get("choices"), "choices")
    identities = _mapping(source.get("identities"), "identities")
    public_keys_by_identity: dict[str, set[str]] = {}
    required = ["root", "director"]
    if choices.get("organization_genesis_born") is True:
        required.append("organization")
    if choices.get("recovery_mode") == "constitutional_quorum":
        reviewer_count = choices.get("constitutional_reviewer_count")
        if not isinstance(reviewer_count, int) or reviewer_count < 1:
            blockers.append("constitutional_reviewer_count must be positive")
        else:
            required.extend(f"constitutional_reviewer_{number}"
                            for number in range(1, reviewer_count + 1))

    for identity_name in required:
        identity = identities.get(identity_name)
        if not isinstance(identity, Mapping):
            blockers.append(f"Identity {identity_name} is absent")
            continue
        public_keys = identity.get("public_keys")
        if not isinstance(public_keys, Sequence) or isinstance(public_keys, str) or not public_keys:
            blockers.append(f"Identity {identity_name} has no public key")
        else:
            valid_keys: set[str] = set()
            for public_key in public_keys:
                if not isinstance(public_key, str):
                    blockers.append(f"Identity {identity_name} has a non-string public key")
                    continue
                try:
                    decoded = base64.b64decode(
                        public_key + "=" * (-len(public_key) % 4),
                        altchars=b"-_",
                        validate=True,
                    )
                except (binascii.Error, ValueError):
                    decoded = b""
                if len(decoded) != 32:
                    blockers.append(
                        f"Identity {identity_name} has a public key that is not Ed25519"
                    )
                else:
                    valid_keys.add(public_key)
            public_keys_by_identity[identity_name] = valid_keys
        if any(secret in identity for secret in ("private_key", "private_keys", "seed", "secret")):
            raise MaterialError(f"private key material is forbidden for Identity {identity_name}")
        custody = identity.get("custody")
        if not isinstance(custody, Mapping) or not custody.get("method"):
            blockers.append(f"Identity {identity_name} has no custody record")
    if choices.get("root_director_identity") == "separate" and (
        public_keys_by_identity.get("root", set())
        & public_keys_by_identity.get("director", set())
    ):
        blockers.append("Root and Director share a key despite the separate-Identity choice")
    return tuple(blockers)


def _identity_bindings(source: Mapping[str, object]) -> dict[str, CanonValue]:
    identities = _mapping(source.get("identities"), "identities")
    bound: dict[str, CanonValue] = {}
    for name, raw_identity in sorted(identities.items()):
        identity = _mapping(raw_identity, f"Identity {name}")
        public_content: dict[str, CanonValue] = {
            "kind": str(identity.get("kind", "")),
            "public_keys": cast(CanonValue, identity.get("public_keys", [])),
        }
        bound[name] = {
            **public_content,
            "content_hash": object_hash("genesis_identity", public_content),
            "custody": cast(CanonValue, identity.get("custody")),
        }
    return bound


def build_genesis_manifest(
    source: Mapping[str, object], registry: Mapping[str, CanonValue]
) -> dict[str, CanonValue]:
    blockers = material_blockers(source)
    choices = cast(CanonValue, source.get("choices"))
    identities = _identity_bindings(source)
    ratifications = cast(CanonValue, source.get("ratifications"))
    content: dict[str, CanonValue] = {
        "format": "powerfarm-genesis-manifest-v1",
        "specification": "powerfarm-system-v3.2",
        "canonicalization": "rfc8785-jcs-v1",
        "hash": "sha256",
        "ratification_status": "ready" if not blockers else "blocked",
        "constitution": {
            "path": "GENESIS_DESIGN_PACK/constitution/01_Genesis_Constitution_0.2.md",
            "content_hash": _document_hash(
                ROOT / "GENESIS_DESIGN_PACK" / "constitution" /
                "01_Genesis_Constitution_0.2.md"
            ),
            "ratified": source.get("constitution_ratified") is True,
        },
        "registry_manifest_hash": registry["manifest_hash"],
        "registry_definition_count": registry["definition_count"],
        "structural_laws": [
            "append-only-acts", "reference-by-hash", "acyclic-ancestry",
            "one-authoritative-admission-door",
        ],
        "choices": choices,
        "ratifications": ratifications,
        "identities": identities,
        "genesis_order": [
            "GenesisCreated", "RegistryCreated", "RootIdentityCreated",
            "RootAuthorityGranted", "GenesisClosed",
        ],
        "blockers": list(blockers),
    }
    content["manifest_hash"] = object_hash("genesis_manifest", content)
    return content


def _render(value: Mapping[str, CanonValue]) -> bytes:
    # Pretty JSON is review material. Its identity is always the JCS value.
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def generate(input_path: Path = DEFAULT_INPUT) -> tuple[bytes, bytes]:
    source = _load(input_path)
    registry = build_registry_manifest(source)
    genesis = build_genesis_manifest(source, registry)
    return _render(registry), _render(genesis)


def write(input_path: Path = DEFAULT_INPUT) -> None:
    registry_bytes, genesis_bytes = generate(input_path)
    REGISTRY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_OUTPUT.write_bytes(registry_bytes)
    GENESIS_OUTPUT.write_bytes(genesis_bytes)


def check(input_path: Path = DEFAULT_INPUT, *, require_ready: bool = False) -> None:
    registry_bytes, genesis_bytes = generate(input_path)
    if REGISTRY_OUTPUT.read_bytes() != registry_bytes:
        raise MaterialError(f"generated Registry material is stale: {REGISTRY_OUTPUT}")
    if GENESIS_OUTPUT.read_bytes() != genesis_bytes:
        raise MaterialError(f"generated Genesis material is stale: {GENESIS_OUTPUT}")
    manifest = cast(Mapping[str, object], json.loads(genesis_bytes))
    blockers = manifest.get("blockers")
    if require_ready and blockers:
        raise MaterialError("M2 is blocked: " + "; ".join(cast(list[str], blockers)))
    # Prove the pretty representation decodes to the exact canonical value.
    canonicalize(cast(CanonValue, json.loads(registry_bytes)))
    canonicalize(cast(CanonValue, json.loads(genesis_bytes)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    if args.check or args.require_ready:
        check(args.input, require_ready=args.require_ready)
    else:
        write(args.input)


if __name__ == "__main__":
    main()
