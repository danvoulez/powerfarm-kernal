# Genesis material

M2 prepares content; M3 performs the irreversible ceremony. Nothing in this
directory is an admitted Genesis yet.

The deterministic source is `registry_blueprint.py` plus
`material-input.candidate.json`. Regenerate and verify the review artifacts with:

```bash
uv run python -m genesis.material
uv run python -m genesis.material --check
```

`--require-ready` is the ceremony-precondition gate. It refuses while a required
decision, Constitution ratification, public Ed25519 key, or custody record is
missing:

```bash
uv run python -m genesis.material --require-ready
```

Private keys, seeds, and secrets are forbidden in the input. Only public key
material and a custody description belong in the content-bound manifest.

## Candidate status

The current Registry candidate derives 112 definitions from its actual content:

- 37 `act_type`
- 21 `command_type`
- 18 `relation_type`
- 15 `context_type`
- 9 `rule`
- 7 `projector`
- 3 `mandate`
- 2 `office`

The additional ten definitions constitute the permanent Constitutional Advisor:
request/issue/transfer command and Act pairs, one pinned opinion context, one non-authority Rule,
one advisory mandate and one permanent office. The chair requires a current premium frontier model
selected by governed policy and remains distinct from both human authority and its replaceable
inference infrastructure.

`SubmitCommand` remains in this candidate because R-1 recommends removing it but
has not been ratified. This reconciles the source document's stated count of 18
commands with the 17 commands it enumerates after the proposed removal. A ruling
may set `submit_command` to `drop`; the generated count and manifest hash will
then change honestly rather than preserving any count as a magic number.

The old `genesis.yaml` and synthetic hash ceremony were removed. `ceremony.py`
now refuses to run while M2 is blocked and, even when material becomes ready,
requires M3 to use the real admission mechanism.
