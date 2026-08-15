begin;

create schema if not exists powerfarm_internal;

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'powerfarm_worker') then
    create role powerfarm_worker nologin noinherit;
  end if;
end
$$;

create or replace function powerfarm_internal.commit_act(
  p_act_hash text,
  p_act_canon bytea,
  p_act_type text,
  p_command_type text,
  p_identity_hash text,
  p_parents jsonb,
  p_decision_cut jsonb,
  p_command_hash text,
  p_auth_chain jsonb,
  p_registry_cut jsonb,
  p_rule_hashes jsonb,
  p_context_hash text,
  p_payload_hash text,
  p_claimed_when text default null
)
returns public.acts
language plpgsql
security definer
set search_path = ''
as $$
declare
  existing_act public.acts%rowtype;
  committed_act public.acts%rowtype;
begin
  if session_user not in ('postgres', 'supabase_admin')
     and not pg_catalog.pg_has_role(session_user, 'powerfarm_worker', 'member') then
    raise exception 'commit_act requires powerfarm_worker membership'
      using errcode = '42501';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('powerfarm:commit-gate:v1', 0)
  );

  select * into existing_act
  from public.acts
  where command_hash = p_command_hash;
  if found then
    if existing_act.hash <> p_act_hash then
      raise exception 'command hash already committed to a different Act';
    end if;
    return existing_act;
  end if;

  if p_act_hash !~ '^[0-9a-f]{64}$'
     or p_command_hash !~ '^[0-9a-f]{64}$'
     or p_identity_hash !~ '^[0-9a-f]{64}$'
     or p_context_hash !~ '^[0-9a-f]{64}$'
     or p_payload_hash !~ '^[0-9a-f]{64}$' then
    raise exception 'commit contains a malformed content hash';
  end if;
  if octet_length(p_act_canon) = 0 then
    raise exception 'canonical Act bytes are required';
  end if;
  if not powerfarm_internal.is_hash_array(p_parents)
     or not powerfarm_internal.is_hash_array(p_decision_cut)
     or not powerfarm_internal.is_hash_array(p_auth_chain)
     or not powerfarm_internal.is_hash_array(p_registry_cut)
     or not powerfarm_internal.is_hash_array(p_rule_hashes) then
    raise exception 'commit contains a malformed hash array';
  end if;
  if jsonb_array_length(p_rule_hashes) = 0 then
    raise exception 'consequential commit requires at least one Rule';
  end if;
  if p_parents ? p_act_hash then
    raise exception 'Act cannot be its own parent';
  end if;

  if (select count(*) from public.acts) <> jsonb_array_length(p_decision_cut)
     or exists (
       select 1 from public.acts a where not (p_decision_cut ? a.hash)
     ) then
    raise exception 'history advanced after authorization; reauthorization required';
  end if;
  if not exists (select 1 from public.identities where hash = p_identity_hash) then
    raise exception 'unknown committing Identity';
  end if;
  if not exists (select 1 from public.objects where hash = p_context_hash) then
    raise exception 'Context must already exist in CAS';
  end if;
  if not exists (select 1 from public.objects where hash = p_payload_hash) then
    raise exception 'payload must already exist in CAS';
  end if;
  if exists (
    select 1 from jsonb_array_elements_text(p_parents) as p(hash)
    where not exists (select 1 from public.acts a where a.hash = p.hash)
  ) then
    raise exception 'every parent must already exist';
  end if;
  if exists (
    select 1 from jsonb_array_elements_text(p_registry_cut) as c(hash)
    where not exists (select 1 from public.acts a where a.hash = c.hash)
  ) then
    raise exception 'registry cut references an unknown Act';
  end if;
  if exists (
    select 1 from jsonb_array_elements_text(p_auth_chain) as c(hash)
    where not exists (select 1 from public.acts a where a.hash = c.hash)
  ) then
    raise exception 'authorization chain references an unknown Act';
  end if;
  if not exists (
    select 1 from public.registry r
    where r.kind = 'command_type' and r.name = p_command_type
      and p_registry_cut ? r.born_at
  ) then
    raise exception 'unregistered command type at declared Registry cut';
  end if;
  if not exists (
    select 1 from public.registry r
    where r.kind = 'act_type' and r.name = p_act_type
      and p_registry_cut ? r.born_at
  ) then
    raise exception 'unregistered Act type at declared Registry cut';
  end if;
  if exists (
    select 1 from jsonb_array_elements_text(p_rule_hashes) as wanted(hash)
    where not exists (
      select 1 from public.registry r
      where r.hash = wanted.hash and r.kind = 'rule'
        and p_registry_cut ? r.born_at
    )
  ) then
    raise exception 'Rule not registered at declared Registry cut';
  end if;

  insert into public.objects (hash, canon, kind)
  values (p_act_hash, p_act_canon, 'act')
  on conflict (hash) do nothing;

  if not exists (
    select 1 from public.objects
    where hash = p_act_hash and canon = p_act_canon and kind = 'act'
  ) then
    raise exception 'CAS collision for Act hash';
  end if;

  insert into public.acts (
    hash, act_type, command_type, identity_hash, parents, decision_cut,
    command_hash, auth_chain, registry_cut, rule_hashes, context_hash,
    payload_hash, claimed_when
  ) values (
    p_act_hash, p_act_type, p_command_type, p_identity_hash, p_parents,
    p_decision_cut, p_command_hash, p_auth_chain, p_registry_cut,
    p_rule_hashes, p_context_hash, p_payload_hash, p_claimed_when
  )
  returning * into committed_act;

  return committed_act;
end
$$;

revoke execute on function powerfarm_internal.commit_act(
  text, bytea, text, text, text, jsonb, jsonb, text, jsonb, jsonb,
  jsonb, text, text, text
) from public, anon, authenticated, service_role;
grant usage on schema powerfarm_internal to powerfarm_worker;
grant execute on function powerfarm_internal.commit_act(
  text, bytea, text, text, text, jsonb, jsonb, text, jsonb, jsonb,
  jsonb, text, text, text
) to powerfarm_worker;

commit;
