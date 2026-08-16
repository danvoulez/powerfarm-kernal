-- Context vocabulary for delegated action.
--
-- Authentication, agency and authority were one thing and are now three:
--
--   who is presenting this request      -> the verified token
--   who is proposing this transition    -> the Command signature
--   does that relation carry authority  -> Rules, over this Context
--
-- These keys are resolved by the service from a verified token through
-- `principal_bindings` and refused outright when a caller supplies them, so a
-- body claiming `requested_by: pf:id:director` cannot become a trusted fact.
-- They are constitutional because a Rule that reads them is deciding whether
-- one participant may act on request of another.
--
-- Requester and performer being the same Identity is ordinary, not a
-- degenerate case: an autonomous service asks on its own behalf. Nothing here
-- assumes a person stands at the origin of every Command.

begin;

insert into public.registry_seed_manifest
  (kind, name, version, constitutional, definition)
values
  ('context_type', 'request.requested_by', 1, true,
   '{"kind":"context_type","name":"request.requested_by","version":1}'),
  ('context_type', 'request.performed_by', 1, true,
   '{"kind":"context_type","name":"request.performed_by","version":1}'),
  ('context_type', 'request.requester_kind', 1, true,
   '{"kind":"context_type","name":"request.requester_kind","version":1}'),
  ('context_type', 'request.oauth_client', 1, true,
   '{"kind":"context_type","name":"request.oauth_client","version":1}')
on conflict (kind, name, version) do update
set constitutional = excluded.constitutional,
    definition = excluded.definition;

commit;
