# Powerfarm Institutional Bootstrap V0 — Setup & Verification

## 1. Minimal File Tree

```
POWERFARM_HOME/
├── canon/
│   ├── genesis-signature.hex
│   └── signature-documentation.txt
├── genesis/
│   ├── founding-key.pem          # from separate ceremony
│   ├── founding-key.pub.pem      # from separate ceremony
│   ├── fingerprint.sha256        # from separate ceremony
│   └── ceremony.txt              # from separate ceremony
├── ledgers/
│   ├── rules.jsonl               # 2 acts
│   ├── registry.jsonl            # 2 acts
│   ├── states.jsonl              # 2 acts
│   └── messages.jsonl            # 1 act
├── bootstrap-manifest.json       # fixed BEFORE execution
└── bootstrap-receipt.json        # created AFTER successful bootstrap
```

## 2. Source Files

- `bootstrap.py` — the bootstrap script (birth script, not a platform)
- `generate_test_keys.py` — helper to create test key material (NOT part of bootstrap)

## 3. Prerequisites

```bash
pip install cryptography
```

## 4. Setup (Test Environment)

Create a test LAB directory:

```bash
export POWERFARM_HOME="/tmp/powerfarm-lab"
mkdir -p "$POWERFARM_HOME"
```

Generate test keys and manifest:

```bash
python generate_test_keys.py --home "$POWERFARM_HOME" --write-manifest
```

This creates:
- `genesis/founding-key.pem`
- `genesis/founding-key.pub.pem`
- `genesis/fingerprint.sha256`
- `genesis/ceremony.txt`
- `bootstrap-manifest.json`

## 5. Exact Command to Run

```bash
python bootstrap.py bootstrap --home "$POWERFARM_HOME"
```

Or with the default path:

```bash
python bootstrap.py bootstrap
```

## 6. Expected Terminal Output

```
POWERFARM · INSTITUTIONAL GENESIS

  ✓ manifest verified
  ✓ founding key verified
  ✓ bootstrap authority recognized

  ◆ admitting rules.genesis
  ◆ registering institution:powerfarm
  ◆ registering principal:founder
  ◆ establishing initial authority
  ◆ unborn → bootstrapping
  ◆ bootstrapping → operational
  ◆ recording bootstrap.completed

✓ BOOTSTRAP COMPLETE

Bootstrap authority has expired.
Powerfarm is operational.
```

## 7. Verification Commands

### All four JSONL ledgers

```bash
echo "=== rules.jsonl ==="
cat "$POWERFARM_HOME/ledgers/rules.jsonl" | python -m json.tool --compact
echo ""
echo "=== registry.jsonl ==="
cat "$POWERFARM_HOME/ledgers/registry.jsonl" | python -m json.tool --compact
echo ""
echo "=== states.jsonl ==="
cat "$POWERFARM_HOME/ledgers/states.jsonl" | python -m json.tool --compact
echo ""
echo "=== messages.jsonl ==="
cat "$POWERFARM_HOME/ledgers/messages.jsonl" | python -m json.tool --compact
```

### Seven genesis Acts (global sequence)

```bash
# Extract all acts in seq order
cat "$POWERFARM_HOME/ledgers/rules.jsonl" "$POWERFARM_HOME/ledgers/registry.jsonl" "$POWERFARM_HOME/ledgers/states.jsonl" "$POWERFARM_HOME/ledgers/messages.jsonl" | \
  python -c "import sys,json; [print(json.dumps(json.loads(l), indent=2)) for l in sys.stdin]"
```

### Final bootstrap.completed

```bash
python -c "
import json, os
home = os.environ['POWERFARM_HOME']
with open(f'{home}/ledgers/messages.jsonl') as f:
    for line in f:
        act = json.loads(line)
        if act['type'] == 'bootstrap.completed':
            print(json.dumps(act, indent=2))
"
```

### bootstrap-receipt.json

```bash
cat "$POWERFARM_HOME/bootstrap-receipt.json" | python -m json.tool
```

### Second bootstrap attempt is rejected

```bash
python bootstrap.py bootstrap --home "$POWERFARM_HOME"
```

Expected output:

```
ERROR: Bootstrap has already completed.
       Bootstrap authority has expired.
       Powerfarm is operational.
```

Exit code: `1`

### Signature documentation

```bash
cat "$POWERFARM_HOME/canon/signature-documentation.txt"
```

## 8. Failure Behavior

### Bootstrap never runs twice

If `bootstrap-receipt.json` exists, bootstrap refuses immediately with exit code 1.
The founding private key may still exist on the medium, but the software does NOT
treat possession of that key as continuing authority.

### Incomplete bootstrap detection

If a ledger file has content but `bootstrap-receipt.json` is missing,
bootstrap detects an incomplete state and refuses with exit code 1.
This prevents a partially-created institution from going unnoticed.

### Key material failure

If any of these checks fail, bootstrap aborts BEFORE writing anything:

- Private key cannot be loaded or is not Ed25519
- Derived public key does not match stored public key
- Calculated fingerprint does not match `fingerprint.sha256`
- Manifest `bootstrapAuthority` does not match the key fingerprint

### Manifest validation failure

If `bootstrap-manifest.json` is missing, malformed, or missing required fields
(`institution`, `bootstrapAuthority`, `allowed`, `terminatesOn`), bootstrap aborts.

### No force flags

There is no `--force`, `--god-mode`, `--bootstrap-again`, or `--ignore-canon`.
If something is wrong, a human must fix it.
