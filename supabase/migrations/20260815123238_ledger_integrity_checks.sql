begin;

create schema if not exists powerfarm_internal;

create or replace function powerfarm_internal.is_hash_array(value jsonb)
returns boolean
language plpgsql
immutable
strict
set search_path = ''
as $$
begin
  if jsonb_typeof(value) <> 'array' then
    return false;
  end if;

  return not exists (
      select 1
      from jsonb_array_elements(value) as item
      where jsonb_typeof(item) <> 'string'
         or trim(both '"' from item::text) !~ '^[0-9a-f]{64}$'
    ) and jsonb_array_length(value) = (
      select count(distinct item)
      from jsonb_array_elements_text(value) as item
    );
end
$$;

alter table public.acts add column if not exists command_type text;
alter table public.acts add column if not exists rule_hashes jsonb;
update public.acts set rule_hashes = '[]'::jsonb where rule_hashes is null;
alter table public.acts alter column rule_hashes set default '[]'::jsonb;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'acts_hash_format' and conrelid = 'public.acts'::regclass
  ) then
    alter table public.acts add constraint acts_hash_format
      check (hash ~ '^[0-9a-f]{64}$') not valid;
  end if;
  if not exists (
    select 1 from pg_constraint
    where conname = 'acts_command_hash_format' and conrelid = 'public.acts'::regclass
  ) then
    alter table public.acts add constraint acts_command_hash_format
      check (command_hash ~ '^[0-9a-f]{64}$') not valid;
  end if;
  if not exists (
    select 1 from pg_constraint
    where conname = 'acts_context_hash_format' and conrelid = 'public.acts'::regclass
  ) then
    alter table public.acts add constraint acts_context_hash_format
      check (context_hash ~ '^[0-9a-f]{64}$') not valid;
  end if;
  if not exists (
    select 1 from pg_constraint
    where conname = 'acts_hash_arrays_valid' and conrelid = 'public.acts'::regclass
  ) then
    alter table public.acts add constraint acts_hash_arrays_valid check (
      powerfarm_internal.is_hash_array(parents)
      and powerfarm_internal.is_hash_array(decision_cut)
      and powerfarm_internal.is_hash_array(auth_chain)
      and powerfarm_internal.is_hash_array(registry_cut)
      and powerfarm_internal.is_hash_array(rule_hashes)
    ) not valid;
  end if;
  if not exists (
    select 1 from pg_constraint
    where conname = 'acts_context_hash_fkey' and conrelid = 'public.acts'::regclass
  ) then
    alter table public.acts add constraint acts_context_hash_fkey
      foreign key (context_hash) references public.objects(hash) not valid;
  end if;
end
$$;

create or replace function powerfarm_internal.validate_act_insert()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.command_type is null or new.command_type = '' then
    raise exception 'Act command_type is required';
  end if;
  if not powerfarm_internal.is_hash_array(new.parents)
     or not powerfarm_internal.is_hash_array(new.decision_cut)
     or not powerfarm_internal.is_hash_array(new.auth_chain)
     or not powerfarm_internal.is_hash_array(new.registry_cut)
     or not powerfarm_internal.is_hash_array(new.rule_hashes) then
    raise exception 'Act hash arrays are malformed';
  end if;
  if new.parents ? new.hash then
    raise exception 'Act cannot be its own parent';
  end if;
  if exists (
    select 1 from jsonb_array_elements_text(new.parents) as p(hash)
    where not exists (select 1 from public.acts a where a.hash = p.hash)
  ) then
    raise exception 'every parent must already exist';
  end if;
  if exists (
    select 1 from jsonb_array_elements_text(new.decision_cut) as c(hash)
    where not exists (select 1 from public.acts a where a.hash = c.hash)
  ) then
    raise exception 'decision cut references an unknown Act';
  end if;
  if exists (
    select 1 from jsonb_array_elements_text(new.registry_cut) as c(hash)
    where not exists (select 1 from public.acts a where a.hash = c.hash)
  ) then
    raise exception 'registry cut references an unknown Act';
  end if;
  if exists (
    select 1 from jsonb_array_elements_text(new.auth_chain) as c(hash)
    where not exists (select 1 from public.acts a where a.hash = c.hash)
  ) then
    raise exception 'authorization chain references an unknown Act';
  end if;
  return new;
end
$$;

drop trigger if exists validate_act_before_insert on public.acts;
create trigger validate_act_before_insert
before insert on public.acts
for each row execute function powerfarm_internal.validate_act_insert();

create or replace function powerfarm_internal.reject_ledger_mutation()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  raise exception 'Powerfarm ledger rows are immutable';
end
$$;

drop trigger if exists objects_are_immutable on public.objects;
create trigger objects_are_immutable before update or delete on public.objects
for each row execute function powerfarm_internal.reject_ledger_mutation();
drop trigger if exists relations_are_immutable on public.relations;
create trigger relations_are_immutable before update or delete on public.relations
for each row execute function powerfarm_internal.reject_ledger_mutation();
drop trigger if exists registry_is_immutable on public.registry;
create trigger registry_is_immutable before update or delete on public.registry
for each row execute function powerfarm_internal.reject_ledger_mutation();
drop trigger if exists identities_are_immutable on public.identities;
create trigger identities_are_immutable before update or delete on public.identities
for each row execute function powerfarm_internal.reject_ledger_mutation();

create index if not exists acts_command_type_seq_idx on public.acts (command_type, seq);
create index if not exists acts_payload_hash_idx on public.acts (payload_hash);
create index if not exists acts_context_hash_idx on public.acts (context_hash);
create index if not exists relations_from_type_idx on public.relations (from_hash, relation_type);
create index if not exists relations_to_type_idx on public.relations (to_hash, relation_type);
create index if not exists relations_payload_hash_idx on public.relations (payload_hash)
  where payload_hash is not null;
create index if not exists registry_born_at_idx on public.registry (born_at);
create index if not exists identities_created_act_idx on public.identities (created_act);

revoke execute on function powerfarm_internal.is_hash_array(jsonb)
  from public, anon, authenticated, service_role;
revoke execute on function powerfarm_internal.validate_act_insert()
  from public, anon, authenticated, service_role;
revoke execute on function powerfarm_internal.reject_ledger_mutation()
  from public, anon, authenticated, service_role;

commit;
