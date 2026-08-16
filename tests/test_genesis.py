import json

import pytest

from genesis.ceremony import MANIFEST, ORDER, GenesisNotReady, ceremony


def test_m2_cannot_be_mistaken_for_a_genesis_ceremony() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["genesis_order"] == list(ORDER)
    assert manifest["ratification_status"] == "blocked"
    with pytest.raises(GenesisNotReady, match="M2 Genesis material is blocked"):
        ceremony(MANIFEST.read_bytes())


def test_genesis_pins_the_definitive_canonicalization() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["specification"] == "powerfarm-system-v3.2"
    assert manifest["canonicalization"] == "rfc8785-jcs-v1"
