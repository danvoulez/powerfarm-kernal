-- Registry seed manifest. These rows are operational inputs to the Genesis
-- ceremony; they do not become authoritative Registry entries until admitted
-- with a born_at reference to GenesisClosed.

begin;

create schema if not exists powerfarm_internal;
revoke all on schema powerfarm_internal from public, anon, authenticated, service_role;

create table if not exists public.registry_seed_manifest (
  kind text not null,
  name text not null,
  version bigint not null default 1 check (version > 0),
  constitutional boolean not null default false,
  definition jsonb not null check (jsonb_typeof(definition) = 'object'),
  primary key (kind, name, version)
);

insert into public.registry_seed_manifest
  (kind, name, version, constitutional, definition)
values
  ('command_type', 'RegisterDefinition', 1, true, '{"kind":"command_type","name":"RegisterDefinition","version":1}'),
  ('command_type', 'CreateIdentity', 1, true, '{"kind":"command_type","name":"CreateIdentity","version":1}'),
  ('command_type', 'RotateKey', 1, true, '{"kind":"command_type","name":"RotateKey","version":1}'),
  ('command_type', 'SubmitCommand', 1, true, '{"kind":"command_type","name":"SubmitCommand","version":1}'),
  ('command_type', 'ReviewAuthorization', 1, true, '{"kind":"command_type","name":"ReviewAuthorization","version":1}'),
  ('act_type', 'GenesisCreated', 1, true, '{"kind":"act_type","name":"GenesisCreated","version":1}'),
  ('act_type', 'RegistryCreated', 1, true, '{"kind":"act_type","name":"RegistryCreated","version":1}'),
  ('act_type', 'RootIdentityCreated', 1, true, '{"kind":"act_type","name":"RootIdentityCreated","version":1}'),
  ('act_type', 'RootAuthorityGranted', 1, true, '{"kind":"act_type","name":"RootAuthorityGranted","version":1}'),
  ('act_type', 'GenesisClosed', 1, true, '{"kind":"act_type","name":"GenesisClosed","version":1}'),
  ('act_type', 'CommandSubmitted', 1, true, '{"kind":"act_type","name":"CommandSubmitted","version":1}'),
  ('act_type', 'CommandValidated', 1, true, '{"kind":"act_type","name":"CommandValidated","version":1}'),
  ('act_type', 'CommandRejected', 1, true, '{"kind":"act_type","name":"CommandRejected","version":1}'),
  ('act_type', 'AuthorizationRequested', 1, true, '{"kind":"act_type","name":"AuthorizationRequested","version":1}'),
  ('act_type', 'CommandDenied', 1, true, '{"kind":"act_type","name":"CommandDenied","version":1}'),
  ('act_type', 'ReviewRequested', 1, true, '{"kind":"act_type","name":"ReviewRequested","version":1}'),
  ('act_type', 'AuthorizationReviewed', 1, true, '{"kind":"act_type","name":"AuthorizationReviewed","version":1}'),
  ('act_type', 'AuthorizationResolved', 1, true, '{"kind":"act_type","name":"AuthorizationResolved","version":1}'),
  ('act_type', 'CommandSuperseded', 1, true, '{"kind":"act_type","name":"CommandSuperseded","version":1}'),
  ('act_type', 'CommandExpired', 1, true, '{"kind":"act_type","name":"CommandExpired","version":1}'),
  ('act_type', 'DefinitionRegistered', 1, true, '{"kind":"act_type","name":"DefinitionRegistered","version":1}'),
  ('act_type', 'IdentityCreated', 1, true, '{"kind":"act_type","name":"IdentityCreated","version":1}'),
  ('act_type', 'KeyRotated', 1, true, '{"kind":"act_type","name":"KeyRotated","version":1}'),
  ('relation_type', 'caused_by', 1, true, '{"kind":"relation_type","name":"caused_by","version":1}'),
  ('relation_type', 'authorized_by', 1, true, '{"kind":"relation_type","name":"authorized_by","version":1}'),
  ('relation_type', 'reviewed_by', 1, true, '{"kind":"relation_type","name":"reviewed_by","version":1}'),
  ('relation_type', 'derived_from', 1, false, '{"kind":"relation_type","name":"derived_from","version":1}'),
  ('relation_type', 'forked_from', 1, true, '{"kind":"relation_type","name":"forked_from","version":1}'),
  ('relation_type', 'simulated_from', 1, false, '{"kind":"relation_type","name":"simulated_from","version":1}'),
  ('relation_type', 'crafted_from', 1, false, '{"kind":"relation_type","name":"crafted_from","version":1}'),
  ('relation_type', 'supports', 1, false, '{"kind":"relation_type","name":"supports","version":1}'),
  ('relation_type', 'contradicts', 1, false, '{"kind":"relation_type","name":"contradicts","version":1}'),
  ('relation_type', 'matched_to', 1, false, '{"kind":"relation_type","name":"matched_to","version":1}'),
  ('relation_type', 'anchored_at', 1, true, '{"kind":"relation_type","name":"anchored_at","version":1}'),
  ('relation_type', 'notarized_by', 1, true, '{"kind":"relation_type","name":"notarized_by","version":1}'),
  ('context_type', 'request.origin', 1, true, '{"kind":"context_type","name":"request.origin","version":1}'),
  ('context_type', 'request.metadata', 1, false, '{"kind":"context_type","name":"request.metadata","version":1}'),
  ('context_type', 'review.acts', 1, true, '{"kind":"context_type","name":"review.acts","version":1}'),
  ('context_type', 'delegation.cut', 1, true, '{"kind":"context_type","name":"delegation.cut","version":1}'),
  ('context_type', 'time.claimed', 1, true, '{"kind":"context_type","name":"time.claimed","version":1}'),
  ('rule', 'genesis.root_authority', 1, true, '{"kind":"rule","name":"genesis.root_authority","version":1}'),
  ('projector', 'causal.topological', 1, true, '{"kind":"projector","name":"causal.topological","version":1}'),
  ('projector', 'registry.current', 1, true, '{"kind":"projector","name":"registry.current","version":1}'),
  ('projector', 'identity_keys.at_cut', 1, true, '{"kind":"projector","name":"identity_keys.at_cut","version":1}'),
  ('projector', 'trajectory.graph', 1, false, '{"kind":"projector","name":"trajectory.graph","version":1}')
on conflict (kind, name, version) do update
set constitutional = excluded.constitutional,
    definition = excluded.definition;

alter table public.registry_seed_manifest enable row level security;
revoke all on public.registry_seed_manifest from public, anon, authenticated, service_role;

commit;
