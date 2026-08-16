-- Operational vocabulary needed by the MCP 2026-07-28 stateless boundary.
-- These rows remain seed inputs: Registry authority still requires admission by Acts.

begin;

insert into public.registry_seed_manifest
  (kind, name, version, constitutional, definition)
values
  ('command_type', 'AdmitObservation', 1, true,
   '{"kind":"command_type","name":"AdmitObservation","version":1}'),
  ('act_type', 'ObservationAdmitted', 1, true,
   '{"kind":"act_type","name":"ObservationAdmitted","version":1}')
on conflict (kind, name, version) do update
set constitutional = excluded.constitutional,
    definition = excluded.definition;

commit;
