-- Linking a credential principal to an Identity is a governed change, not an
-- administrative INSERT.
--
-- `principal_bindings` had no writer at all: the table existed and was read, so
-- the only way a row could appear was by hand. That is precisely the second,
-- invisible mechanism section 17 forbids -- the system cannot govern users by
-- one path and govern itself by another.
--
-- So the binding becomes what everything else is:
--
--     LinkPrincipal   -> Rules -> PrincipalLinked
--     RevokePrincipal -> Rules -> PrincipalRevoked
--
-- and the table becomes a projection of those Acts (section 14). Deleting it
-- loses nothing; the Acts remain and rebuild it. `linked_act` and `unlinked_act`
-- are the Act hashes that admitted and withdrew the binding, which is why
-- revocation is an Act rather than a delete.

begin;

insert into public.registry_seed_manifest
  (kind, name, version, constitutional, definition)
values
  ('command_type', 'LinkPrincipal', 1, true,
   '{"kind":"command_type","name":"LinkPrincipal","version":1}'),
  ('command_type', 'RevokePrincipal', 1, true,
   '{"kind":"command_type","name":"RevokePrincipal","version":1}'),
  ('act_type', 'PrincipalLinked', 1, true,
   '{"kind":"act_type","name":"PrincipalLinked","version":1}'),
  ('act_type', 'PrincipalRevoked', 1, true,
   '{"kind":"act_type","name":"PrincipalRevoked","version":1}')
on conflict (kind, name, version) do update
set constitutional = excluded.constitutional,
    definition = excluded.definition;

commit;
