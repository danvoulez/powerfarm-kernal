-- R-26: freeze the four canonical preimage corrections before Genesis.
--
-- This migration intentionally refuses to reinterpret existing history.  The
-- supplied baseline has never run Genesis; if authoritative rows exist in a
-- different environment, that fact requires an explicit audit/fork decision.

begin;

do $$
begin
  if exists (select 1 from public.acts) then
    raise exception 'R-26 requires an empty pre-Genesis acts table';
  end if;
  if exists (select 1 from public.relations) then
    raise exception 'R-26 requires an empty pre-Genesis relations table';
  end if;
end
$$;

alter table public.acts
  add column validity_rule_hash text not null
    check (validity_rule_hash ~ '^[0-9a-f]{64}$'),
  add column validity_disposition text not null
    check (validity_disposition in ('VALID', 'REAUTHORIZE', 'COMMIT_REGARDLESS'));

drop index if exists public.relations_from_type_idx;
drop index if exists public.relations_to_type_idx;

alter table public.relations rename column relation_type to relation_type_hash;
alter table public.relations
  add constraint relations_relation_type_hash_check
  check (relation_type_hash ~ '^[0-9a-f]{64}$');

create index relations_from_type_hash_idx
  on public.relations (from_hash, relation_type_hash);
create index relations_to_type_hash_idx
  on public.relations (to_hash, relation_type_hash);

revoke execute on function powerfarm_internal.commit_act(
  text, bytea, text, text, text, jsonb, jsonb, text, jsonb, jsonb,
  jsonb, text, text, text
) from powerfarm_worker;

drop function powerfarm_internal.commit_act(
  text, bytea, text, text, text, jsonb, jsonb, text, jsonb, jsonb,
  jsonb, text, text, text
);

create function powerfarm_internal.commit_act(
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
  p_validity_rule_hash text,
  p_validity_disposition text,
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
  where hash = p_act_hash;
  if found then
    return existing_act;
  end if;

  if p_act_hash !~ '^[0-9a-f]{64}$'
     or p_command_hash !~ '^[0-9a-f]{64}$'
     or p_identity_hash !~ '^[0-9a-f]{64}$'
     or p_context_hash !~ '^[0-9a-f]{64}$'
     or p_payload_hash !~ '^[0-9a-f]{64}$'
     or p_validity_rule_hash !~ '^[0-9a-f]{64}$' then
    raise exception 'commit contains a malformed content hash';
  end if;
  if p_validity_disposition <> 'VALID' then
    raise exception 'admission requires a VALID decision-validity disposition';
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
    raise exception 'commit requires at least one authorization Rule';
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
    raise exception 'authorization Rule not registered at declared Registry cut';
  end if;
  if not exists (
    select 1 from public.registry r
    where r.hash = p_validity_rule_hash
      and r.kind = 'rule'
      and r.name = 'declared-decision-cut'
      and p_registry_cut ? r.born_at
      and r.version = (
        select max(current_rule.version)
        from public.registry current_rule
        where current_rule.kind = 'rule'
          and current_rule.name = 'declared-decision-cut'
          and p_registry_cut ? current_rule.born_at
      )
  ) then
    raise exception 'decision-validity Rule not registered at declared Registry cut';
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
    payload_hash, validity_rule_hash, validity_disposition, claimed_when
  ) values (
    p_act_hash, p_act_type, p_command_type, p_identity_hash, p_parents,
    p_decision_cut, p_command_hash, p_auth_chain, p_registry_cut,
    p_rule_hashes, p_context_hash, p_payload_hash, p_validity_rule_hash,
    p_validity_disposition, p_claimed_when
  )
  returning * into committed_act;

  return committed_act;
end
$$;

revoke execute on function powerfarm_internal.commit_act(
  text, bytea, text, text, text, jsonb, jsonb, text, jsonb, jsonb,
  jsonb, text, text, text, text, text
) from public, anon, authenticated, service_role;

grant execute on function powerfarm_internal.commit_act(
  text, bytea, text, text, text, jsonb, jsonb, text, jsonb, jsonb,
  jsonb, text, text, text, text, text
) to powerfarm_worker;

commit;
