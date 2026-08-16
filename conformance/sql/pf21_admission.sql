-- PF-21 Versioned Governance, at the real admission boundary.
--
-- conformance/test_pf21.py proves the Kernel resolves semantic dependencies to
-- exact definitions. That proves the Kernel agrees with itself. This file runs
-- the same matrix through `powerfarm_internal.commit_act` -- the function that
-- actually admits Acts -- because PF-21 is a claim about what is *admitted*, not
-- about what Python intended.
--
-- The two layers are deliberately redundant. If they ever disagree, the
-- disagreement is the finding.

-- Hashes are written as repeat(<digit>, 64) throughout, so each fixture object
-- is recognisable on sight:
--   0 Genesis Act   1 second Act    2 Identity     3 Context      4 payload
--   5 rule v1       6 rule v2       7 command_type 8 act_type     9 unregistered
--   c admitted Act  d/f command     e Act that must never land

\set ON_ERROR_STOP on

begin;

-- Objects first: registry, identity and act rows all reference CAS.
insert into public.objects (hash, canon, kind) values
  (repeat('0', 64), '\x00', 'act'),
  (repeat('1', 64), '\x01', 'act'),
  (repeat('2', 64), '\x02', 'identity'),
  (repeat('3', 64), '\x03', 'context'),
  (repeat('4', 64), '\x04', 'payload'),
  (repeat('5', 64), '\x05', 'rule'),
  (repeat('6', 64), '\x06', 'rule'),
  (repeat('7', 64), '\x07', 'command_type'),
  (repeat('8', 64), '\x08', 'act_type')
on conflict (hash) do nothing;

-- Two Acts of history. The second exists so the Registry can grow *after* the
-- Registry cut a later decision declares.
insert into public.acts
  (hash, act_type, command_type, identity_hash, parents, decision_cut,
   command_hash, auth_chain, registry_cut, rule_hashes, context_hash,
   payload_hash, claimed_when)
values
  (repeat('0', 64), 'GenesisClosed', 'Genesis', repeat('2', 64), '[]'::jsonb,
   '[]'::jsonb, repeat('a', 64), '[]'::jsonb, '[]'::jsonb, '[]'::jsonb,
   repeat('3', 64), repeat('4', 64), null),
  (repeat('1', 64), 'ThingCreated', 'CreateThing', repeat('2', 64),
   to_jsonb(array[repeat('0', 64)]), to_jsonb(array[repeat('0', 64)]),
   repeat('b', 64), '[]'::jsonb, to_jsonb(array[repeat('0', 64)]),
   to_jsonb(array[repeat('5', 64)]), repeat('3', 64), repeat('4', 64), null)
on conflict (hash) do nothing;

insert into public.identities (hash, kind, created_act)
values (repeat('2', 64), 'human', repeat('0', 64))
on conflict (hash) do nothing;

-- test.allow v1 is born at Genesis. v2 is born one Act later -- same name,
-- different content hash, different birth.
insert into public.registry (hash, kind, name, version, born_at, constitutional)
values
  (repeat('7', 64), 'command_type', 'CreateThing',  1, repeat('0', 64), false),
  (repeat('8', 64), 'act_type',     'ThingCreated', 1, repeat('0', 64), false),
  (repeat('5', 64), 'rule',         'test.allow',   1, repeat('0', 64), false),
  (repeat('6', 64), 'rule',         'test.allow',   2, repeat('1', 64), false)
on conflict (hash) do nothing;

commit;


-- Every refusal case runs through this shape: if commit_act *succeeds*, the law
-- is broken and we raise loudly. A refusal for any reason is the pass condition
-- for these cases; the Python matrix pins the exact refusal reasons.
create or replace function pg_temp.must_refuse(label text, body text) returns void
language plpgsql as $$
begin
  begin
    execute body;
  exception
    when others then
      if sqlerrm like 'PF-21 VIOLATION%' then raise; end if;
      raise notice 'refused as required: %', label;
      return;
  end;
  raise exception 'PF-21 VIOLATION: % was admitted and should not have been', label;
end $$;


-- Case 1 -- exact Registry cut, exact Rule hash, admitted.
select powerfarm_internal.commit_act(
  repeat('c', 64), '\xc0'::bytea, 'ThingCreated', 'CreateThing', repeat('2', 64),
  to_jsonb(array[repeat('0', 64)]),
  to_jsonb(array[repeat('0', 64), repeat('1', 64)]),
  repeat('d', 64), '[]'::jsonb,
  to_jsonb(array[repeat('0', 64)]),
  to_jsonb(array[repeat('5', 64)]),
  repeat('3', 64), repeat('4', 64), null);

-- Case 7 -- what was admitted is exactly what authorized it, and stays so.
do $$
declare
  admitted public.acts%rowtype;
begin
  select * into admitted from public.acts where hash = repeat('c', 64);
  if admitted.rule_hashes <> to_jsonb(array[repeat('5', 64)]) then
    raise exception 'PF-21 VIOLATION: admitted rule_hashes drifted: %', admitted.rule_hashes;
  end if;
  if admitted.registry_cut <> to_jsonb(array[repeat('0', 64)]) then
    raise exception 'PF-21 VIOLATION: admitted registry_cut drifted: %', admitted.registry_cut;
  end if;
  raise notice 'admitted Act cites exactly the versions that validated it';
end $$;

-- Case 2 -- v2 exists in history, but is not born within the declared Registry
-- cut. "Latest" is not a resolution strategy.
select pg_temp.must_refuse('rule born after the declared Registry cut', $q$
  select powerfarm_internal.commit_act(
    repeat('e', 64), '\xe0'::bytea, 'ThingCreated', 'CreateThing', repeat('2', 64),
    to_jsonb(array[repeat('0', 64)]),
    to_jsonb(array[repeat('0', 64), repeat('1', 64), repeat('c', 64)]),
    repeat('f', 64), '[]'::jsonb,
    to_jsonb(array[repeat('0', 64)]),
    to_jsonb(array[repeat('6', 64)]),
    repeat('3', 64), repeat('4', 64), null)
$q$);

-- Case 3 -- a Rule hash nobody registered. The name 'test.allow' is registered
-- twice over; the hash is what must resolve.
select pg_temp.must_refuse('right name, unregistered hash', $q$
  select powerfarm_internal.commit_act(
    repeat('e', 64), '\xe0'::bytea, 'ThingCreated', 'CreateThing', repeat('2', 64),
    to_jsonb(array[repeat('0', 64)]),
    to_jsonb(array[repeat('0', 64), repeat('1', 64), repeat('c', 64)]),
    repeat('f', 64), '[]'::jsonb,
    to_jsonb(array[repeat('0', 64)]),
    to_jsonb(array[repeat('9', 64)]),
    repeat('3', 64), repeat('4', 64), null)
$q$);

-- Case 4 -- an act type that is not registered at the declared Registry cut.
select pg_temp.must_refuse('act type unregistered at the declared cut', $q$
  select powerfarm_internal.commit_act(
    repeat('e', 64), '\xe0'::bytea, 'NeverRegistered', 'CreateThing', repeat('2', 64),
    to_jsonb(array[repeat('0', 64)]),
    to_jsonb(array[repeat('0', 64), repeat('1', 64), repeat('c', 64)]),
    repeat('f', 64), '[]'::jsonb,
    to_jsonb(array[repeat('0', 64)]),
    to_jsonb(array[repeat('5', 64)]),
    repeat('3', 64), repeat('4', 64), null)
$q$);

-- Case 5 -- one unresolvable hash among several rejects the whole admission.
-- Partial attribution is not a thing.
select pg_temp.must_refuse('one bad hash among several', $q$
  select powerfarm_internal.commit_act(
    repeat('e', 64), '\xe0'::bytea, 'ThingCreated', 'CreateThing', repeat('2', 64),
    to_jsonb(array[repeat('0', 64)]),
    to_jsonb(array[repeat('0', 64), repeat('1', 64), repeat('c', 64)]),
    repeat('f', 64), '[]'::jsonb,
    to_jsonb(array[repeat('0', 64)]),
    to_jsonb(array[repeat('5', 64), repeat('9', 64)]),
    repeat('3', 64), repeat('4', 64), null)
$q$);

-- Case 6 -- no Rule at all cannot buy a consequence.
select pg_temp.must_refuse('empty rule_hashes', $q$
  select powerfarm_internal.commit_act(
    repeat('e', 64), '\xe0'::bytea, 'ThingCreated', 'CreateThing', repeat('2', 64),
    to_jsonb(array[repeat('0', 64)]),
    to_jsonb(array[repeat('0', 64), repeat('1', 64), repeat('c', 64)]),
    repeat('f', 64), '[]'::jsonb,
    to_jsonb(array[repeat('0', 64)]),
    '[]'::jsonb,
    repeat('3', 64), repeat('4', 64), null)
$q$);

-- Nothing from the refusal cases may have landed.
do $$
begin
  if exists (select 1 from public.acts where hash = repeat('e', 64)) then
    raise exception 'PF-21 VIOLATION: a refused admission left an Act behind';
  end if;
  raise notice 'no refused admission left an Act behind';
end $$;
