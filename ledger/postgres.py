"""PostgreSQL/Supabase adapter for exact-cut reads and the atomic commit RPC."""

from __future__ import annotations

import base64
import json
from collections.abc import Mapping
from typing import Any, cast
from uuid import UUID

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from kernel.types import Act, Identity

from .base import ObjectRecord, RegistryEntry


def _decode_public_key(value: str) -> bytes:
    try:
        if len(value) == 64:
            decoded = bytes.fromhex(value)
        else:
            decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, TypeError) as error:
        raise ValueError("identity key is neither hex nor base64url") from error
    if len(decoded) != 32:
        raise ValueError("Ed25519 public key must be 32 bytes")
    return decoded


def _row_to_act(row: Mapping[str, Any]) -> Act:
    return Act(
        hash=str(row["hash"]),
        act_type=str(row["act_type"]),
        identity_hash=str(row["identity_hash"]),
        parents=tuple(row["parents"]),
        decision_cut=frozenset(row["decision_cut"]),
        command_hash=str(row["command_hash"]),
        auth_chain=tuple(row["auth_chain"]),
        registry_cut=frozenset(row["registry_cut"]),
        rule_hashes=tuple(row["rule_hashes"]),
        context_hash=str(row["context_hash"]),
        payload_hash=str(row["payload_hash"]),
        claimed_when=row.get("claimed_when"),
    )


class PostgresStore:
    """Small synchronous adapter; the SQL function arbitrates commit concurrency."""

    def __init__(self, database_url: str, *, min_size: int = 1, max_size: int = 4) -> None:
        self._pool = cast(
            ConnectionPool[Connection[dict[str, Any]]],
            ConnectionPool(
                database_url,
                min_size=min_size,
                max_size=max_size,
                kwargs={"row_factory": dict_row},
                open=True,
            ),
        )

    def history_cut(self) -> frozenset[str]:
        with self._pool.connection() as connection:
            rows = connection.execute("select hash from public.acts order by hash").fetchall()
        return frozenset(str(row["hash"]) for row in rows)

    def registered(self, kind: str, name: str, cut: frozenset[str]) -> bool:
        with self._pool.connection() as connection:
            row = connection.execute(
                """
                select exists (
                  select 1 from public.registry
                  where kind = %s and (name = %s or hash = %s) and %s::jsonb ? born_at
                ) as present
                """,
                (kind, name, name, Jsonb(sorted(cut))),
            ).fetchone()
        return bool(row and row["present"])

    def has_object(self, object_hash: str) -> bool:
        return self.get_object(object_hash) is not None

    def has_act(self, act_hash: str) -> bool:
        return self.get_act(act_hash) is not None

    def put_object(self, object_hash: str, canon: bytes, kind: str) -> None:
        with self._pool.connection() as connection:
            connection.execute(
                """
                insert into public.objects (hash, canon, kind) values (%s, %s, %s)
                on conflict (hash) do nothing
                """,
                (object_hash, canon, kind),
            )
            row = connection.execute(
                "select canon, kind from public.objects where hash = %s", (object_hash,)
            ).fetchone()
            if row is None or bytes(row["canon"]) != canon or row["kind"] != kind:
                raise ValueError("CAS collision")

    def commit_act(self, act: Act, canon: bytes, command_type: str) -> Act:
        with self._pool.connection() as connection:
            row = connection.execute(
                """
                select * from powerfarm_internal.commit_act(
                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    act.hash,
                    canon,
                    act.act_type,
                    command_type,
                    act.identity_hash,
                    Jsonb(list(act.parents)),
                    Jsonb(sorted(act.decision_cut)),
                    act.command_hash,
                    Jsonb(list(act.auth_chain)),
                    Jsonb(sorted(act.registry_cut)),
                    Jsonb(list(act.rule_hashes)),
                    act.context_hash,
                    act.payload_hash,
                    act.claimed_when,
                ),
            ).fetchone()
        if row is None:
            raise RuntimeError("commit RPC returned no Act")
        return _row_to_act(row)

    def get_object(self, object_hash: str) -> ObjectRecord | None:
        with self._pool.connection() as connection:
            row = connection.execute(
                "select hash, canon, kind from public.objects where hash = %s", (object_hash,)
            ).fetchone()
        if row is None:
            return None
        return ObjectRecord(str(row["hash"]), bytes(row["canon"]), str(row["kind"]))

    def get_act(self, act_hash: str) -> Act | None:
        with self._pool.connection() as connection:
            row = connection.execute("select * from public.acts where hash = %s", (act_hash,)).fetchone()
        return _row_to_act(row) if row is not None else None

    def is_closed_cut(self, cut: frozenset[str]) -> bool:
        with self._pool.connection() as connection:
            row = connection.execute(
                """
                select
                  (select count(*) from public.acts where %s::jsonb ? hash) = %s
                  and not exists (
                    select 1
                    from public.acts a,
                         lateral jsonb_array_elements_text(a.parents) as p(parent_hash)
                    where %s::jsonb ? a.hash and not (%s::jsonb ? p.parent_hash)
                  ) as closed
                """,
                (Jsonb(sorted(cut)), len(cut), Jsonb(sorted(cut)), Jsonb(sorted(cut))),
            ).fetchone()
        return bool(row and row["closed"])

    def get_act_for_command(self, command_hash: str) -> Act | None:
        with self._pool.connection() as connection:
            row = connection.execute(
                "select * from public.acts where command_hash = %s", (command_hash,)
            ).fetchone()
        return _row_to_act(row) if row is not None else None

    def get_identity(self, identity_hash: str, cut: frozenset[str]) -> Identity | None:
        with self._pool.connection() as connection:
            identity = connection.execute(
                "select hash, kind from public.identities where hash = %s", (identity_hash,)
            ).fetchone()
            if identity is None:
                return None
            keys = connection.execute(
                "select * from powerfarm_internal.identity_keys_at_cut(%s, %s)",
                (identity_hash, Jsonb(sorted(cut))),
            ).fetchall()
        if len(keys) != 1:
            raise ValueError("identity must have exactly one valid signing key at the declared cut")
        return Identity(identity_hash, str(identity["kind"]), _decode_public_key(str(keys[0]["pubkey"])))

    def registry_entries(
        self, kind: str | None, cut: frozenset[str]
    ) -> tuple[RegistryEntry, ...]:
        query = """
            select r.hash, r.kind, r.name, r.version, r.born_at, r.constitutional, o.canon
            from public.registry r join public.objects o on o.hash = r.hash
            where %s::jsonb ? r.born_at and (%s is null or r.kind = %s)
            order by r.kind, r.name, r.version
        """
        with self._pool.connection() as connection:
            rows = connection.execute(query, (Jsonb(sorted(cut)), kind, kind)).fetchall()
        entries: list[RegistryEntry] = []
        for row in rows:
            definition = json.loads(bytes(row["canon"]).decode("utf-8"))
            entries.append(
                RegistryEntry(
                    hash=str(row["hash"]),
                    kind=str(row["kind"]),
                    name=str(row["name"]),
                    version=int(row["version"]),
                    born_at=str(row["born_at"]),
                    constitutional=bool(row["constitutional"]),
                    definition=definition,
                )
            )
        return tuple(entries)

    def list_acts(self, limit: int = 100) -> tuple[Act, ...]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        with self._pool.connection() as connection:
            rows = connection.execute(
                "select * from public.acts order by seq desc limit %s", (limit,)
            ).fetchall()
        return tuple(_row_to_act(row) for row in reversed(rows))

    def resolve_principal(self, issuer: str, subject: str) -> str | None:
        del issuer
        try:
            user_id = UUID(subject)
        except ValueError:
            return None
        with self._pool.connection() as connection:
            row = connection.execute(
                """
                select identity_hash from public.identity_links
                where supabase_user = %s and unlinked_act is null
                order by linked_act desc limit 1
                """,
                (user_id,),
            ).fetchone()
        return str(row["identity_hash"]) if row is not None else None

    def close(self) -> None:
        self._pool.close()
