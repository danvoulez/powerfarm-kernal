-- 20260815060331 auth_boundary — Supabase authenticates, Powerfarm authorizes.
-- Idempotent. These are governed projections over Acts, not sources of truth.

begin;

-- Explicit mapping: Supabase user UUID -> Powerfarm Identity hash.
-- Never conflate the two identifiers (Identity != Authentication).
create table if not exists identity_links (
  supabase_user uuid not null references auth.users(id),
  identity_hash text not null references identities(hash),
  linked_act text not null references acts(hash),
  unlinked_act text references acts(hash),
  primary key (supabase_user, identity_hash)
);
create index if not exists identity_links_identity_idx on identity_links (identity_hash)
  where unlinked_act is null;

-- OAuth applications as GOVERNED resources. auth.oauth_clients is execution
-- infrastructure; THIS is the projection of OAuthApplication* Acts.
-- Dynamic Client Registration stays OFF: clients are born here, via Command.
create table if not exists oauth_applications (
  client_id text primary key,
  name text not null,
  client_type text not null check (client_type in ('public','confidential')),
  redirect_uris jsonb not null check (jsonb_typeof(redirect_uris) = 'array'),
  registered_act text not null references acts(hash),
  provisioned_act text references acts(hash),
  revoked_act text references acts(hash),
  owner_identity text not null references identities(hash),
  environment text not null default 'production'
    check (environment in ('development','staging','production'))
);

-- Transaction-bound human confirmation:
-- Authentication != Authorization != Confirmation.
create table if not exists authorization_proofs (
  proof_hash text primary key check (proof_hash ~ '^[0-9a-f]{64}$'),
  identity_hash text not null references identities(hash),
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
  consumed_act text references acts(hash)   -- single-use
);

alter table identity_links enable row level security;
alter table oauth_applications enable row level security;
alter table authorization_proofs enable row level security;

revoke all on identity_links, oauth_applications, authorization_proofs
  from public, anon, authenticated;

commit;
