begin;

create schema if not exists powerfarm_internal;

create index if not exists identity_keys_open_idx
  on public.identity_keys (identity_hash, pubkey)
  where valid_until_act is null;
create index if not exists identity_keys_valid_from_idx
  on public.identity_keys (valid_from_act);
create index if not exists identity_keys_valid_until_idx
  on public.identity_keys (valid_until_act)
  where valid_until_act is not null;

create or replace function powerfarm_internal.identity_keys_at_cut(
  p_identity_hash text,
  p_cut jsonb
)
returns table (pubkey text, valid_from_act text, valid_until_act text)
language sql
stable
security invoker
set search_path = ''
as $$
  select k.pubkey, k.valid_from_act, k.valid_until_act
  from public.identity_keys as k
  where k.identity_hash = p_identity_hash
    and p_cut ? k.valid_from_act
    and (k.valid_until_act is null or not (p_cut ? k.valid_until_act))
  order by k.valid_from_act, k.pubkey
$$;

create or replace view public.identity_keys_open
with (security_invoker = true)
as
select identity_hash, pubkey, valid_from_act
from public.identity_keys
where valid_until_act is null;

revoke all on public.identity_keys_open from public, anon, authenticated, service_role;
revoke execute on function powerfarm_internal.identity_keys_at_cut(text, jsonb)
  from public, anon, authenticated, service_role;

commit;
