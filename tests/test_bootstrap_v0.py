import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP = ROOT / "bootstrap" / "v0" / "bootstrap.py"
KEYGEN = ROOT / "bootstrap" / "v0" / "generate_test_keys.py"


def test_bootstrap_v0_runs_once_and_writes_receipt(tmp_path: Path) -> None:
    subprocess.run(
        [sys.executable, str(KEYGEN), "--home", str(tmp_path), "--write-manifest"],
        check=True,
        capture_output=True,
        text=True,
    )

    first = subprocess.run(
        [sys.executable, str(BOOTSTRAP), "bootstrap", "--home", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "BOOTSTRAP COMPLETE" in first.stdout

    receipt = json.loads((tmp_path / "bootstrap-receipt.json").read_text(encoding="utf-8"))
    assert receipt["institution"] == "powerfarm"
    assert receipt["completed"] is True

    ledgers = tmp_path / "ledgers"
    acts = []
    for ledger in ("rules.jsonl", "registry.jsonl", "states.jsonl", "messages.jsonl"):
        acts.extend(
            json.loads(line)
            for line in (ledgers / ledger).read_text(encoding="utf-8").splitlines()
        )
    assert len(acts) == 7
    assert {act["type"] for act in acts} >= {"rules.genesis", "bootstrap.completed"}

    second = subprocess.run(
        [sys.executable, str(BOOTSTRAP), "bootstrap", "--home", str(tmp_path)],
        capture_output=True,
        check=False,
        text=True,
    )
    assert second.returncode == 1
    assert "Bootstrap has already completed" in second.stdout
