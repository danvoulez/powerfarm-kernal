-- Powerfarm baseline schema.
--
-- This file intentionally embeds the schema already present in the live
-- Supabase database as a clean, idempotent baseline for the macOS psql pack.
-- It does not require a database reset. Re-running it must converge.
--
-- If we later switch to Supabase CLI migration history as the deploy source of
-- truth, reconcile remote history with `supabase migration squash` / `repair`
-- before using `supabase db push`.

begin;

-- ---------------------------------------------------------------------------
-- Constitutional ledger tables
-- ---------------------------------------------------------------------------

create table if not exists public.objects (
  hash text primary key check (hash ~ '^[0-9a-f]{64}$'),
  canon bytea not null,
  kind text not null
);

create table if not exists public.acts (
  seq bigint generated always as identity primary key,
  hash text not null unique references public.objects(hash),
  act_type text not null,
  identity_hash text not null,
  parents jsonb not null check (jsonb_typeof(parents) = 'array'),
  decision_cut jsonb not null check (jsonb_typeof(decision_cut) = 'array'),
  command_hash text not null unique,
  auth_chain jsonb not null default '[]'::jsonb,
  registry_cut jsonb not null check (jsonb_typeof(registry_cut) = 'array'),
  context_hash text not null,
  payload_hash text not null references public.objects(hash),
  claimed_when text
);

create table if not exists public.relations (
  hash text primary key references public.objects(hash),
  from_hash text not null references public.objects(hash),
  to_hash text not null references public.objects(hash),
  relation_type text not null,
  payload_hash text references public.objects(hash)
);

create table if not exists public.registry (
  hash text primary key references public.objects(hash),
  kind text not null,
  name text not null,
  version bigint not null check (version > 0),
  born_at text not null references public.acts(hash),
  constitutional boolean not null default false,
  unique (kind, name, version)
);

create table if not exists public.identities (
  hash text primary key references public.objects(hash),
  kind text not null,
  created_act text not null references public.acts(hash)
);

create table if not exists public.identity_keys (
  identity_hash text not null references public.identities(hash),
  pubkey text not null,
  valid_from_act text not null references public.acts(hash),
  valid_until_act text references public.acts(hash),
  primary key (identity_hash, pubkey, valid_from_act)
);

create index if not exists acts_identity_idx on public.acts (identity_hash);
create index if not exists acts_parents_gin on public.acts using gin (parents);

-- Acts are append-only. Existing rows are corrected by new Acts, never edited.
create or replace function public.reject_act_mutation() returns trigger
language plpgsql set search_path = '' as $$
begin
  raise exception 'Powerfarm Acts are append-only';
end
$$;

drop trigger if exists acts_are_immutable on public.acts;
create trigger acts_are_immutable
before update or delete on public.acts
for each row execute function public.reject_act_mutation();

-- ---------------------------------------------------------------------------
-- Supabase authentication boundary projections
-- ---------------------------------------------------------------------------

create table if not exists public.identity_links (
  supabase_user uuid not null references auth.users(id),
  identity_hash text not null references public.identities(hash),
  linked_act text not null references public.acts(hash),
  unlinked_act text references public.acts(hash),
  primary key (supabase_user, identity_hash)
);

create index if not exists identity_links_identity_idx
  on public.identity_links (identity_hash)
  where unlinked_act is null;

create table if not exists public.oauth_applications (
  client_id text primary key,
  name text not null,
  client_type text not null check (client_type in ('public','confidential')),
  redirect_uris jsonb not null check (jsonb_typeof(redirect_uris) = 'array'),
  registered_act text not null references public.acts(hash),
  provisioned_act text references public.acts(hash),
  revoked_act text references public.acts(hash),
  owner_identity text not null references public.identities(hash),
  environment text not null default 'production'
    check (environment in ('development','staging','production'))
);

create table if not exists public.authorization_proofs (
  proof_hash text primary key check (proof_hash ~ '^[0-9a-f]{64}$'),
  identity_hash text not null references public.identities(hash),
  command_hash text not null,
  context_hash text not null,
  history_cut jsonb not null,
  credential_id text not null,
  challenge_hash text not null,
  origin text not null,
  rp_id text not null,
  user_present boolean not null,
  user_verified boolean not null,
  issued_at timestamptz not null,
  expires_at timestamptz not null,
  consumed_act text references public.acts(hash)
);

-- Installer-owned migration ledger. The baseline is always safe to re-run;
-- later files are checksum-verified against this table before execution.
create table if not exists public.powerfarm_schema_migrations (
  version text primary key check (version ~ '^[0-9]{14}$'),
  name text not null,
  checksum_sha256 text not null check (checksum_sha256 ~ '^[0-9a-f]{64}$'),
  pack_version text,
  git_commit text check (git_commit is null or git_commit ~ '^[0-9a-f]{40}$'),
  applied_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Defensive RLS and grants baseline
-- ---------------------------------------------------------------------------

alter table public.objects enable row level security;
alter table public.acts enable row level security;
alter table public.relations enable row level security;
alter table public.registry enable row level security;
alter table public.identities enable row level security;
alter table public.identity_keys enable row level security;
alter table public.identity_links enable row level security;
alter table public.oauth_applications enable row level security;
alter table public.authorization_proofs enable row level security;
alter table public.powerfarm_schema_migrations enable row level security;

revoke update, delete, truncate on public.acts from public;

revoke insert, update, delete, truncate
  on public.objects,
     public.acts,
     public.relations,
     public.registry,
     public.identities,
     public.identity_keys
  from public;

revoke all
  on public.identity_links,
     public.oauth_applications,
     public.authorization_proofs
  from public, anon, authenticated;

revoke all
  on public.objects,
     public.acts,
     public.relations,
     public.registry,
     public.identities,
     public.identity_keys,
     public.powerfarm_schema_migrations
  from anon, authenticated, service_role;

commit;
