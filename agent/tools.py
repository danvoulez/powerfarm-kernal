"""Agent tools propose signed Commands; they never write history."""

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from kernel.canon import canonicalize
from kernel.types import Command


def propose_command(command_type: str, identity_hash: str, payload_hash: str,
                    parents: tuple[str, ...], nonce: str,
                    private_key: Ed25519PrivateKey) -> Command:
    unsigned = Command(command_type, identity_hash, payload_hash, parents, nonce, b"")
    return Command(command_type, identity_hash, payload_hash, parents, nonce,
                   private_key.sign(canonicalize(unsigned.signing_value())))

