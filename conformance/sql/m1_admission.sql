-- M1: Act placement and its declared companion succeed or roll back together.

\set ON_ERROR_STOP on

begin;
insert into public.objects (hash, canon, kind) values
  (repeat('91', 32), convert_to('{"companion":{"cardinality":"exactly_one","writer":"principal_bindings"},"kind":"act_type","name":"PrincipalLinked","version":1}', 'UTF8'), 'act_type'),
  (repeat('92', 32), convert_to('{"companion":{"cardinality":"exactly_one","writer":"principal_bindings"},"kind":"act_type","name":"PrincipalRevoked","version":1}', 'UTF8'), 'act_type'),
  (repeat('93', 32), '\x93', 'command_type'),
  (repeat('94', 32), '\x94', 'command_type')
on conflict (hash) do nothing;
insert into public.registry (hash, kind, name, version, born_at, constitutional) values
  (repeat('91', 32), 'act_type', 'PrincipalLinked', 1, repeat('0', 64), true),
  (repeat('92', 32), 'act_type', 'PrincipalRevoked', 1, repeat('0', 64), true),
  (repeat('93', 32), 'command_type', 'LinkPrincipal', 1, repeat('0', 64), true),
  (repeat('94', 32), 'command_type', 'RevokePrincipal', 1, repeat('0', 64), true)
on conflict (hash) do nothing;
commit;

begin;
select powerfarm_internal.begin_admission() as admission_cut \gset
select powerfarm_internal.admit(
  repeat('95', 32), '\x95'::bytea, 'PrincipalLinked', 'LinkPrincipal', repeat('2', 64),
  to_jsonb(array[repeat('0', 64)]), :'admission_cut'::jsonb,
  repeat('d1', 32), '[]'::jsonb, to_jsonb(array[repeat('0', 64)]),
  to_jsonb(array[repeat('5', 64)]), repeat('3', 64), repeat('4', 64),
  repeat('a1', 32), 'VALID', null, :'admission_cut'::jsonb,
  jsonb_build_array(jsonb_build_object(
    'writer', 'principal_bindings',
    'row', jsonb_build_object(
      'operation', 'link', 'issuer', 'https://m1.example',
      'subject', 'alice', 'identity_hash', repeat('2', 64)
    )
  ))
);
commit;

do $$
begin
  if not exists (
    select 1 from public.principal_bindings
    where issuer = 'https://m1.example' and subject = 'alice'
      and linked_act = repeat('95', 32) and unlinked_act is null
  ) then
    raise exception 'M1 VIOLATION: Act and companion did not land together';
  end if;
end
$$;

-- The Act is inserted before companion dispatch inside `admit`. A rejected
-- companion must nevertheless roll the Act back with the transaction.
begin;
select powerfarm_internal.begin_admission();
do $$
begin
  begin
    perform powerfarm_internal.admit(
      repeat('97', 32), '\x97'::bytea, 'PrincipalRevoked', 'RevokePrincipal', repeat('2', 64),
      to_jsonb(array[repeat('0', 64)]),
      pg_catalog.current_setting('powerfarm.admission_cut')::jsonb,
      repeat('d2', 32), '[]'::jsonb, to_jsonb(array[repeat('0', 64)]),
      to_jsonb(array[repeat('5', 64)]), repeat('3', 64), repeat('4', 64),
      repeat('a1', 32), 'VALID', null,
      pg_catalog.current_setting('powerfarm.admission_cut')::jsonb,
      jsonb_build_array(jsonb_build_object(
        'writer', 'principal_bindings',
        'row', jsonb_build_object(
          'operation', 'revoke', 'issuer', 'https://m1.example', 'subject', 'missing'
        )
      ))
    );
    raise exception 'M1 VIOLATION: missing companion target was accepted';
  exception
    when others then
      if sqlerrm like 'M1 VIOLATION%' then raise; end if;
  end;
  if exists (select 1 from public.acts where hash = repeat('97', 32)) then
    raise exception 'M1 VIOLATION: rejected companion left an Act behind';
  end if;
end
$$;
commit;

