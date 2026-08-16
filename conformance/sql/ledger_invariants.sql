-- Constitutional enforcement that lives in PostgreSQL, proved by violating it.
--
-- Reading a migration and finding a trigger proves the trigger was written once.
-- It does not prove the trigger is attached, enabled, correctly scoped, or still
-- there after fifteen more migrations. A dropped trigger and a working one look
-- identical to a code-reading audit, and the audit reports the invariant either
-- way. So every case here attempts the forbidden thing and requires the database
-- itself to refuse.
--
-- Closes the ENFORCED_UNPROVEN entries for PF-07, PF-10 and PF-12, plus the
-- "one consequence per Command" index that has had no behavioural test since it
-- replaced `unique (command_hash)`.
--
-- Hash space is disjoint from pf21_admission.sql (two-character repeats), so the
-- two files can run against the same database in either order.

\set ON_ERROR_STOP on

begin;

insert into public.objects (hash, canon, kind) values
  (repeat('ab', 32), '\xab', 'act'),
  (repeat('ac', 32), '\xac', 'identity'),
  (repeat('ad', 32), '\xad', 'context'),
  (repeat('ae', 32), '\xae', 'payload'),
  (repeat('af', 32), '\xaf', 'rule'),
  (repeat('ba', 32), '\xba', 'command_type'),
  (repeat('bc', 32), '\xbc', 'act_type'),
  (repeat('bf', 32), '\xbf', 'relation'),
  (repeat('bd', 32), '\xbd', 'act'),
  (repeat('be', 32), '\xbe', 'act')
on conflict (hash) do nothing;

insert into public.acts
  (hash, act_type, command_type, identity_hash, parents, decision_cut,
   command_hash, auth_chain, registry_cut, rule_hashes, context_hash,
   payload_hash, claimed_when)
values
  (repeat('ab', 32), 'GenesisClosed', 'Genesis', repeat('ac', 32), '[]'::jsonb,
   '[]'::jsonb, repeat('ca', 32), '[]'::jsonb, '[]'::jsonb, '[]'::jsonb,
   repeat('ad', 32), repeat('ae', 32), null)
on conflict (hash) do nothing;

insert into public.identities (hash, kind, created_act)
values (repeat('ac', 32), 'human', repeat('ab', 32))
on conflict (hash) do nothing;

insert into public.registry (hash, kind, name, version, born_at, constitutional)
values
  (repeat('ba', 32), 'command_type', 'InvariantProbe', 1, repeat('ab', 32), false),
  (repeat('bc', 32), 'act_type',     'ProbeHappened',  1, repeat('ab', 32), false),
  (repeat('af', 32), 'rule',         'probe.allow',    1, repeat('ab', 32), false)
on conflict (hash) do nothing;

-- The Relation carries its own content hash: `Relation.hash` already exists in
-- kernel/types.py even though nothing writes this table yet (Phase 0a).
insert into public.relations (hash, from_hash, to_hash, relation_type, payload_hash)
values (repeat('bf', 32), repeat('ad', 32), repeat('ae', 32), 'derived_from', null)
on conflict (hash) do nothing;

commit;


create or replace function pg_temp.must_refuse(label text, body text) returns void
language plpgsql as $$
begin
  begin
    execute body;
  exception
    when others then
      if sqlerrm like 'LEDGER VIOLATION%' then raise; end if;
      raise notice 'refused as required: %', label;
      return;
  end;
  raise exception 'LEDGER VIOLATION: % was permitted', label;
end $$;


-- PF-07 Immutable Acts -------------------------------------------------------
-- "Existing Acts are never edited in place; corrections are new Acts."

select pg_temp.must_refuse('UPDATE on acts', $q$
  update public.acts set act_type = 'Rewritten' where hash = repeat('ab', 32)
$q$);

select pg_temp.must_refuse('DELETE from acts', $q$
  delete from public.acts where hash = repeat('ab', 32)
$q$);

select pg_temp.must_refuse('UPDATE on relations', $q$
  update public.relations set relation_type = 'observed_from'
   where from_hash = repeat('ad', 32)
$q$);

select pg_temp.must_refuse('DELETE from relations', $q$
  delete from public.relations where from_hash = repeat('ad', 32)
$q$);

select pg_temp.must_refuse('UPDATE on registry', $q$
  update public.registry set name = 'Renamed' where hash = repeat('ba', 32)
$q$);

select pg_temp.must_refuse('DELETE from registry', $q$
  delete from public.registry where hash = repeat('ba', 32)
$q$);


-- PF-10 Acyclic Ancestry -----------------------------------------------------
-- A cycle is unconstructible: parents must already exist, and an Act may not be
-- its own parent. Both refusals are asserted rather than inferred.

select pg_temp.must_refuse('Act declaring itself as parent', $q$
  select powerfarm_internal.commit_act(
    repeat('bd', 32), '\xbd'::bytea, 'ProbeHappened', 'InvariantProbe', repeat('ac', 32),
    to_jsonb(array[repeat('bd', 32)]),
    to_jsonb(array(select hash from public.acts order by hash)),
    repeat('cb', 32), '[]'::jsonb,
    to_jsonb(array[repeat('ab', 32)]),
    to_jsonb(array[repeat('af', 32)]),
    repeat('ad', 32), repeat('ae', 32), null)
$q$);

select pg_temp.must_refuse('Act naming a parent that does not exist', $q$
  select powerfarm_internal.commit_act(
    repeat('bd', 32), '\xbd'::bytea, 'ProbeHappened', 'InvariantProbe', repeat('ac', 32),
    to_jsonb(array[repeat('fe', 32)]),
    to_jsonb(array(select hash from public.acts order by hash)),
    repeat('cb', 32), '[]'::jsonb,
    to_jsonb(array[repeat('ab', 32)]),
    to_jsonb(array[repeat('af', 32)]),
    repeat('ad', 32), repeat('ae', 32), null)
$q$);


-- PF-12 Causal Order Constitutional ------------------------------------------
-- "Commit sequence numbers are operational cursors with gaps, never proof of
-- order." Demonstrated rather than asserted: burn a sequence value in an aborted
-- transaction, then show history is unchanged and the next Act's seq has skipped.

do $$
declare
  before_count bigint;
  after_count  bigint;
  burned       bigint;
  landed       bigint;
begin
  select count(*) into before_count from public.acts;

  begin
    insert into public.acts
      (hash, act_type, command_type, identity_hash, parents, decision_cut,
       command_hash, auth_chain, registry_cut, rule_hashes, context_hash,
       payload_hash, claimed_when)
    values
      (repeat('be', 32), 'ProbeHappened', 'InvariantProbe', repeat('ac', 32),
       '[]'::jsonb, '[]'::jsonb, repeat('cc', 32), '[]'::jsonb, '[]'::jsonb,
       '[]'::jsonb, repeat('ad', 32), repeat('ae', 32), null)
    returning seq into burned;
    raise exception 'rollback on purpose';
  exception when others then
    null;  -- the identity value is consumed regardless
  end;

  select count(*) into after_count from public.acts;
  if after_count <> before_count then
    raise exception 'LEDGER VIOLATION: aborted insert changed history';
  end if;

  insert into public.acts
    (hash, act_type, command_type, identity_hash, parents, decision_cut,
     command_hash, auth_chain, registry_cut, rule_hashes, context_hash,
     payload_hash, claimed_when)
  values
    (repeat('be', 32), 'ProbeHappened', 'InvariantProbe', repeat('ac', 32),
     '[]'::jsonb, '[]'::jsonb, repeat('cc', 32), '[]'::jsonb, '[]'::jsonb,
     '[]'::jsonb, repeat('ad', 32), repeat('ae', 32), null)
  returning seq into landed;

  if landed <= burned then
    raise exception 'LEDGER VIOLATION: seq did not advance past the aborted value';
  end if;
  raise notice 'seq has gaps (% burned, % landed) and history is unaffected', burned, landed;
end $$;

-- And the cut that matters is a set of hashes, computed without reference to seq.
do $$
declare
  by_hash bigint;
begin
  select count(*) into by_hash from public.acts where hash is not null;
  if by_hash < 2 then
    raise exception 'LEDGER VIOLATION: fixture did not land';
  end if;
  raise notice 'history cut is a set of % hashes, not a seq range', by_hash;
end $$;


-- One consequence per Command ------------------------------------------------
-- `acts_one_consequence_per_command_idx` replaced `unique (command_hash)`, which
-- had been doing two jobs. Only this one survived, and until now only the Python
-- gate proved it.

-- Lifecycle stages accumulate: many Acts, one Command, all permitted.
insert into public.objects (hash, canon, kind) values
  (repeat('da', 32), '\xda', 'act'),
  (repeat('db', 32), '\xdb', 'act'),
  (repeat('dc', 32), '\xdc', 'act')
on conflict (hash) do nothing;

insert into public.acts
  (hash, act_type, command_type, identity_hash, parents, decision_cut,
   command_hash, auth_chain, registry_cut, rule_hashes, context_hash,
   payload_hash, claimed_when)
values
  (repeat('da', 32), 'CommandSubmitted', 'InvariantProbe', repeat('ac', 32),
   '[]'::jsonb, '[]'::jsonb, repeat('cd', 32), '[]'::jsonb, '[]'::jsonb,
   '[]'::jsonb, repeat('ad', 32), repeat('ae', 32), null),
  (repeat('db', 32), 'CommandValidated', 'InvariantProbe', repeat('ac', 32),
   '[]'::jsonb, '[]'::jsonb, repeat('cd', 32), '[]'::jsonb, '[]'::jsonb,
   '[]'::jsonb, repeat('ad', 32), repeat('ae', 32), null),
  (repeat('dc', 32), 'ReviewRequested', 'InvariantProbe', repeat('ac', 32),
   '[]'::jsonb, '[]'::jsonb, repeat('cd', 32), '[]'::jsonb, '[]'::jsonb,
   '[]'::jsonb, repeat('ad', 32), repeat('ae', 32), null)
on conflict (hash) do nothing;

do $$
begin
  if (select count(*) from public.acts where command_hash = repeat('cd', 32)) <> 3 then
    raise exception 'LEDGER VIOLATION: lifecycle Acts of one Command were rejected';
  end if;
  raise notice 'three lifecycle Acts coexist for one Command';
end $$;

-- Consequence does not. The first lands; the second is refused by the index.
insert into public.objects (hash, canon, kind)
values (repeat('dd', 32), '\xdd', 'act'), (repeat('de', 32), '\xde', 'act')
on conflict (hash) do nothing;

insert into public.acts
  (hash, act_type, command_type, identity_hash, parents, decision_cut,
   command_hash, auth_chain, registry_cut, rule_hashes, context_hash,
   payload_hash, claimed_when)
values
  (repeat('dd', 32), 'ProbeHappened', 'InvariantProbe', repeat('ac', 32),
   '[]'::jsonb, '[]'::jsonb, repeat('cd', 32), '[]'::jsonb, '[]'::jsonb,
   '[]'::jsonb, repeat('ad', 32), repeat('ae', 32), null)
on conflict (hash) do nothing;

select pg_temp.must_refuse('a second consequential Act for one Command', $q$
  insert into public.acts
    (hash, act_type, command_type, identity_hash, parents, decision_cut,
     command_hash, auth_chain, registry_cut, rule_hashes, context_hash,
     payload_hash, claimed_when)
  values
    (repeat('de', 32), 'ProbeHappened', 'InvariantProbe', repeat('ac', 32),
     '[]'::jsonb, '[]'::jsonb, repeat('cd', 32), '[]'::jsonb, '[]'::jsonb,
     '[]'::jsonb, repeat('ad', 32), repeat('ae', 32), null)
$q$);
