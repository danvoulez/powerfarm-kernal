"""M3 ceremony entry point, deliberately locked while M2 is not ratified.

The former prototype synthesized five hashes from a YAML summary.  Those were
not admitted Acts and therefore could never be a real Genesis.  M2 removes that
false-success path; M3 will replace this lock with the real admission ceremony.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import NoReturn

ORDER = ("GenesisCreated", "RegistryCreated", "RootIdentityCreated",
         "RootAuthorityGranted", "GenesisClosed")
MANIFEST = Path(__file__).with_name("manifest.candidate.json")


class GenesisNotReady(RuntimeError):
    pass


def ceremony(manifest_bytes: bytes) -> NoReturn:
    manifest = json.loads(manifest_bytes)
    if not isinstance(manifest, dict):
        raise GenesisNotReady("Genesis manifest must be an object")
    blockers = manifest.get("blockers")
    if manifest.get("ratification_status") != "ready" or blockers:
        count = len(blockers) if isinstance(blockers, list) else "unknown"
        raise GenesisNotReady(f"M2 Genesis material is blocked ({count} blockers)")
    raise GenesisNotReady(
        "M2 material is ready, but M3 must admit the ceremony through the real gate"
    )


def main() -> None:
    ceremony(MANIFEST.read_bytes())


if __name__ == "__main__":
    main()
