-- Occurrence identity is the Act's own hash, never its Command.
--
-- The baseline declared `acts.command_hash text not null unique`. That single
-- constraint was doing two different jobs:
--
--   1. idempotency -- wrong. PF-23 and section 10.1 place uniqueness on
--      `acts.hash`, which `acts_hash_key` already enforces and which this
--      migration leaves untouched.
--   2. "a Command buys its change once" -- right, and preserved below as a
--      partial unique index over consequential Act types only.
--
-- Job 1 made a Command's lifecycle unrepresentable: section 6.1 requires the
-- lifecycle to be carried entirely by Acts referencing the Command, and PF-15
-- requires it to be reconstructible from those Acts alone. The registry seed
-- already registers all ten lifecycle Act types this constraint forbade from
-- coexisting.
--
-- Act hashes also change with this release: `claimed_when` enters the preimage
-- (section 10.3), so the time claimed inside an Act is finally part of its
-- identity rather than an unauthenticated column beside it.

begin;

alter table public.acts drop constraint if exists acts_command_hash_key;

-- Job 2, stated exactly. Lifecycle stages accumulate; consequence does not.
create unique index if not exists acts_one_consequence_per_command_idx
  on public.acts (command_hash)
  where act_type not in (
    'CommandSubmitted', 'CommandValidated', 'CommandRejected',
    'AuthorizationRequested', 'CommandDenied', 'ReviewRequested',
    'AuthorizationReviewed', 'AuthorizationResolved',
    'CommandSuperseded', 'CommandExpired'
  );

-- Lifecycle projection reads every Act of one Command. `seq` orders it for
-- pagination only -- constitutional order is the ancestry DAG (section 10.2).
create index if not exists acts_command_hash_seq_idx on public.acts (command_hash, seq);

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

  -- Idempotency is keyed on the Act's content hash (PF-23). `decision_cut` and
  -- `claimed_when` are both inside that preimage, so a replay of identical
  -- content returns the same placement while anything that differs in content
  -- is a distinct occurrence and is judged on its own below.
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
    raise exception 'commit requires at least one Rule';
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

commit;
