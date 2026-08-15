begin;

-- Storage object creation is deliberately absent here. The macOS installer
-- creates private buckets through the Supabase Storage API and records only
-- durable, content-addressed metadata in Postgres.
create table if not exists public.remote_ledger_segments (
  segment_hash text primary key check (segment_hash ~ '^[0-9a-f]{64}$'),
  bucket_id text not null default 'powerfarm-ledger'
    check (bucket_id = 'powerfarm-ledger'),
  object_path text not null unique,
  first_seq bigint not null check (first_seq > 0),
  last_seq bigint not null check (last_seq >= first_seq),
  input_cut jsonb not null,
  input_cut_hash text not null check (input_cut_hash ~ '^[0-9a-f]{64}$'),
  object_size bigint not null check (object_size >= 0),
  content_type text not null default 'application/x-ndjson',
  object_etag text,
  source_act text references public.acts(hash),
  created_by text references public.identities(hash),
  created_at timestamptz not null default now(),
  verified_at timestamptz,
  check (powerfarm_internal.is_hash_array(input_cut))
);

create table if not exists public.update_packages (
  package_hash text primary key check (package_hash ~ '^[0-9a-f]{64}$'),
  version text not null,
  git_commit text not null check (git_commit ~ '^[0-9a-f]{40}$'),
  bucket_id text not null default 'powerfarm-packages'
    check (bucket_id = 'powerfarm-packages'),
  object_path text not null unique,
  manifest_hash text not null check (manifest_hash ~ '^[0-9a-f]{64}$'),
  object_size bigint not null check (object_size > 0),
  platform text not null default 'macos-launchd'
    check (platform = 'macos-launchd'),
  minimum_pack_version text,
  source_act text references public.acts(hash),
  published_by text references public.identities(hash),
  published_at timestamptz not null default now(),
  revoked_act text references public.acts(hash),
  unique (version, platform)
);

create index if not exists remote_ledger_segments_seq_idx
  on public.remote_ledger_segments (first_seq, last_seq);
create index if not exists remote_ledger_segments_cut_idx
  on public.remote_ledger_segments (input_cut_hash);
create index if not exists update_packages_published_idx
  on public.update_packages (platform, published_at desc)
  where revoked_act is null;

alter table public.remote_ledger_segments enable row level security;
alter table public.update_packages enable row level security;

revoke all on public.remote_ledger_segments, public.update_packages
  from public, anon, authenticated, service_role;

commit;
