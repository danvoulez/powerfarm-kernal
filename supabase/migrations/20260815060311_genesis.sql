-- 20260815060311 genesis — the constitutional minimum. Idempotent by construction.
-- Six tables. Everything else is a projection.

begin;

create table if not exists objects (
  hash text primary key check (hash ~ '^[0-9a-f]{64}$'),
  canon bytea not null,
  kind text not null
);

create table if not exists acts (
  seq bigint generated always as identity primary key,
  hash text not null unique references objects(hash),
  act_type text not null,
  identity_hash text not null,
  parents jsonb not null check (jsonb_typeof(parents) = 'array'),
  decision_cut jsonb not null check (jsonb_typeof(decision_cut) = 'array'),
  command_hash text not null unique,
  auth_chain jsonb not null default '[]'::jsonb,
  registry_cut jsonb not null check (jsonb_typeof(registry_cut) = 'array'),
  context_hash text not null,
  payload_hash text not null references objects(hash),
  claimed_when text
);

create table if not exists relations (
  hash text primary key references objects(hash),
  from_hash text not null references objects(hash),
  to_hash text not null references objects(hash),
  relation_type text not null,
  payload_hash text references objects(hash)
);

create table if not exists registry (
  hash text primary key references objects(hash),
  kind text not null,
  name text not null,
  version bigint not null check (version > 0),
  born_at text not null references acts(hash),
  constitutional boolean not null default false,
  unique (kind, name, version)
);

create table if not exists identities (
  hash text primary key references objects(hash),
  kind text not null,
  created_act text not null references acts(hash)
);

create table if not exists identity_keys (
  identity_hash text not null references identities(hash),
  pubkey text not null,
  valid_from_act text not null references acts(hash),
  valid_until_act text references acts(hash),
  primary key (identity_hash, pubkey, valid_from_act)
);

create index if not exists acts_identity_idx on acts (identity_hash);
create index if not exists acts_parents_gin on acts using gin (parents);

create or replace function reject_act_mutation() returns trigger
language plpgsql set search_path = '' as $$
begin raise exception 'Powerfarm Acts are append-only'; end $$;

drop trigger if exists acts_are_immutable on acts;
create trigger acts_are_immutable before update or delete on acts
for each row execute function reject_act_mutation();

revoke update, delete, truncate on acts from public;
revoke insert, update, delete, truncate on objects, acts, relations, registry,
  identities, identity_keys from public;

commit;
