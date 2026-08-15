from pathlib import Path

from genesis.ceremony import ORDER, ceremony
from kernel.canon import object_hash

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "genesis" / "genesis.yaml"


def test_genesis_is_stable_and_dependency_ordered() -> None:
    config = CONFIG.read_bytes()
    root, acts = ceremony(config)

    assert tuple(act["act_type"] for act in acts) == ORDER
    assert root == acts[-1]["hash"]
    assert ceremony(config) == (root, acts)

    expected_parent: str | None = None
    for act in acts:
        value = {key: item for key, item in act.items() if key != "hash"}
        assert act["parents"] == ([] if expected_parent is None else [expected_parent])
        assert act["hash"] == object_hash("genesis_act", value)  # type: ignore[arg-type]
        expected_parent = str(act["hash"])


def test_genesis_pins_the_definitive_canonicalization() -> None:
    config = CONFIG.read_text(encoding="utf-8")

    assert "specification: powerfarm-system-v3.2" in config
    assert "canonicalization: rfc8785-jcs-v1" in config
    assert "rfc8949" not in config
