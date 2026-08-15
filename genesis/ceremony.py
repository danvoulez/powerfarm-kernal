"""Produce the stable, dependency-ordered genesis root without a privileged backdoor."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from kernel.canon import object_hash

ORDER = ("GenesisCreated", "RegistryCreated", "RootIdentityCreated",
         "RootAuthorityGranted", "GenesisClosed")


def ceremony(config_bytes: bytes) -> tuple[str, tuple[dict[str, object], ...]]:
    config_hash = object_hash("genesis_config", base64.urlsafe_b64encode(config_bytes).decode())
    parent: str | None = None
    acts: list[dict[str, object]] = []
    for act_type in ORDER:
        value: dict[str, object] = {"act_type": act_type, "config_hash": config_hash,
                                    "parents": [] if parent is None else [parent]}
        parent = object_hash("genesis_act", value)  # type: ignore[arg-type]
        acts.append({**value, "hash": parent})
    assert parent is not None
    return parent, tuple(acts)


def main() -> None:
    root, acts = ceremony(Path(__file__).with_name("genesis.yaml").read_bytes())
    print(json.dumps({"acts": acts, "genesis_root_hash": root}, indent=2))


if __name__ == "__main__":
    main()
