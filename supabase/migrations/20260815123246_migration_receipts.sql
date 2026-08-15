begin;

create table if not exists public.powerfarm_pack_receipts (
  receipt_hash text primary key check (receipt_hash ~ '^[0-9a-f]{64}$'),
  action text not null check (action in ('install', 'update', 'uninstall')),
  pack_version text not null,
  git_commit text check (git_commit is null or git_commit ~ '^[0-9a-f]{40}$'),
  hostname text not null,
  api_hostname text,
  migration_versions jsonb not null default '[]'::jsonb,
  storage_buckets jsonb not null default '[]'::jsonb,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  check (jsonb_typeof(migration_versions) = 'array'),
  check (jsonb_typeof(storage_buckets) = 'array'),
  check (jsonb_typeof(details) = 'object')
);

drop trigger if exists powerfarm_pack_receipts_are_immutable
  on public.powerfarm_pack_receipts;
create trigger powerfarm_pack_receipts_are_immutable
before update or delete on public.powerfarm_pack_receipts
for each row execute function powerfarm_internal.reject_ledger_mutation();

alter table public.powerfarm_pack_receipts enable row level security;

revoke all on public.powerfarm_pack_receipts
  from public, anon, authenticated, service_role;
grant select, insert on public.powerfarm_pack_receipts to powerfarm_worker;

drop policy if exists powerfarm_worker_select on public.powerfarm_pack_receipts;
create policy powerfarm_worker_select on public.powerfarm_pack_receipts for select
  to powerfarm_worker using (true);
drop policy if exists powerfarm_worker_insert on public.powerfarm_pack_receipts;
create policy powerfarm_worker_insert on public.powerfarm_pack_receipts for insert
  to powerfarm_worker with check (true);

commit;
