-- R-24/R-25/R-27: one transaction owns the admission cut, Act placement,
-- and every declared companion write.

begin;

update public.registry_seed_manifest
set definition = jsonb_set(
  definition,
  '{companion}',
  '{"writer":"principal_bindings","cardinality":"exactly_one"}'::jsonb
)
where kind = 'act_type'
  and name in ('PrincipalLinked', 'PrincipalRevoked')
  and version = 1;

alter function powerfarm_internal.commit_act(
  text, bytea, text, text, text, jsonb, jsonb, text, jsonb, jsonb,
  jsonb, text, text, text, text, text
) rename to commit_act_internal;

revoke execute on function powerfarm_internal.commit_act_internal(
  text, bytea, text, text, text, jsonb, jsonb, text, jsonb, jsonb,
  jsonb, text, text, text, text, text
) from public, anon, authenticated, service_role, powerfarm_worker;

create function powerfarm_internal.begin_admission()
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  admission_cut jsonb;
begin
  if session_user not in ('postgres', 'supabase_admin')
     and not pg_catalog.pg_has_role(session_user, 'powerfarm_worker', 'member') then
    raise exception 'begin_admission requires powerfarm_worker membership'
      using errcode = '42501';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('powerfarm:commit-gate:v1', 0)
  );
  select coalesce(jsonb_agg(a.hash order by a.hash), '[]'::jsonb)
    into admission_cut
  from public.acts a;
  perform pg_catalog.set_config(
    'powerfarm.admission_cut', admission_cut::text, true
  );
  return admission_cut;
end
$$;

create function powerfarm_internal.admit(
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
  p_claimed_when text,
  p_admission_cut jsonb,
  p_companions jsonb
)
returns public.acts
language plpgsql
security definer
set search_path = ''
as $$
declare
  actual_cut jsonb;
  act_definition jsonb;
  contract jsonb;
  companion jsonb;
  companion_count integer;
  committed_act public.acts%rowtype;
  affected integer;
begin
  if session_user not in ('postgres', 'supabase_admin')
     and not pg_catalog.pg_has_role(session_user, 'powerfarm_worker', 'member') then
    raise exception 'admit requires powerfarm_worker membership'
      using errcode = '42501';
  end if;
  if nullif(pg_catalog.current_setting('powerfarm.admission_cut', true), '') is null then
    raise exception 'admit requires an active admission scope';
  end if;
  if jsonb_typeof(p_admission_cut) is distinct from 'array'
     or pg_catalog.current_setting('powerfarm.admission_cut', true)::jsonb
       is distinct from p_admission_cut then
    raise exception 'admission cut does not belong to this scope';
  end if;

  select coalesce(jsonb_agg(a.hash order by a.hash), '[]'::jsonb)
    into actual_cut
  from public.acts a;
  if actual_cut is distinct from p_admission_cut then
    raise exception 'history advanced inside admission scope';
  end if;
  if jsonb_typeof(p_companions) is distinct from 'array' then
    raise exception 'companions must be an array';
  end if;

  select convert_from(o.canon, 'UTF8')::jsonb
    into act_definition
  from public.registry r
  join public.objects o on o.hash = r.hash
  where r.kind = 'act_type'
    and r.name = p_act_type
    and p_registry_cut ? r.born_at
  order by r.version desc
  limit 1;
  if act_definition is null then
    raise exception 'Act type definition is unavailable at declared Registry cut';
  end if;

  contract := act_definition -> 'companion';
  companion_count := jsonb_array_length(p_companions);
  if contract is null then
    if companion_count <> 0 then
      raise exception 'Act type declares no companion';
    end if;
  else
    if jsonb_typeof(contract) is distinct from 'object'
       or contract ->> 'cardinality' is null
       or contract ->> 'cardinality' not in ('exactly_one', 'one_or_more') then
      raise exception 'unsupported companion contract';
    end if;
    if contract ->> 'cardinality' = 'exactly_one' and companion_count <> 1 then
      raise exception 'companion contract requires exactly one row';
    end if;
    if contract ->> 'cardinality' = 'one_or_more' and companion_count < 1 then
      raise exception 'companion contract requires one or more rows';
    end if;
    if exists (
      select 1 from jsonb_array_elements(p_companions) as supplied(value)
      where supplied.value ->> 'writer' is distinct from contract ->> 'writer'
    ) then
      raise exception 'companion writer does not match Act type contract';
    end if;
    if contract ->> 'writer' is distinct from 'principal_bindings' then
      raise exception 'unsupported companion writer';
    end if;
  end if;

  select * into committed_act
  from powerfarm_internal.commit_act_internal(
    p_act_hash, p_act_canon, p_act_type, p_command_type, p_identity_hash,
    p_parents, p_decision_cut, p_command_hash, p_auth_chain, p_registry_cut,
    p_rule_hashes, p_context_hash, p_payload_hash, p_validity_rule_hash,
    p_validity_disposition, p_claimed_when
  );

  for companion in select value from jsonb_array_elements(p_companions)
  loop
    if contract ->> 'writer' is distinct from 'principal_bindings' then
      raise exception 'unsupported companion writer';
    end if;
    if jsonb_typeof(companion -> 'row') is distinct from 'object' then
      raise exception 'principal companion row must be an object';
    end if;
    if companion #>> '{row,operation}' = 'link' then
      insert into public.principal_bindings
        (issuer, subject, identity_hash, linked_act)
      values (
        companion #>> '{row,issuer}',
        companion #>> '{row,subject}',
        companion #>> '{row,identity_hash}',
        committed_act.hash
      );
    elsif companion #>> '{row,operation}' = 'revoke' then
      update public.principal_bindings
      set unlinked_act = committed_act.hash
      where issuer = companion #>> '{row,issuer}'
        and subject = companion #>> '{row,subject}'
        and unlinked_act is null;
      get diagnostics affected = row_count;
      if affected <> 1 then
        raise exception 'credential principal has no live binding';
      end if;
    else
      raise exception 'unsupported principal companion operation';
    end if;
  end loop;

  return committed_act;
end
$$;

revoke execute on function powerfarm_internal.begin_admission()
  from public, anon, authenticated, service_role;
revoke execute on function powerfarm_internal.admit(
  text, bytea, text, text, text, jsonb, jsonb, text, jsonb, jsonb,
  jsonb, text, text, text, text, text, jsonb, jsonb
) from public, anon, authenticated, service_role;
grant execute on function powerfarm_internal.begin_admission()
  to powerfarm_worker;
grant execute on function powerfarm_internal.admit(
  text, bytea, text, text, text, jsonb, jsonb, text, jsonb, jsonb,
  jsonb, text, text, text, text, text, jsonb, jsonb
) to powerfarm_worker;

revoke insert, update, delete on public.principal_bindings from powerfarm_worker;
drop policy if exists powerfarm_worker_insert on public.principal_bindings;
drop policy if exists powerfarm_worker_unlink on public.principal_bindings;

commit;
